
import dask
from dask import array as da
from dask.delayed import delayed
import numpy as np
from scipy.spatial import cKDTree
from collections import deque
from astropy import units as u

from .CalculationDelegate import CalculationDelegate
from mirage.parameters import Parameters, MicrolensingParameters
from mirage.engine.micro_ray_tracer import ray_trace_singlethreaded as trace_chunk
from mirage.util import PixelRegion

from .reducers import MagmapReducer, QueryReducer

PRIMARY_DIMENSION_CHUNK_SIZE = 1000

class DaskCalculationDelegate(CalculationDelegate):

    _dask_array = None
    _dask_kd_tree = None

    def __init__(self, *args, **kwargs):
        dask.config.set(scheduler="threads")

    @property
    def array(self):
        return self._dask_array

    def reconfigure(self, parameters: MicrolensingParameters):
        inputUnit = parameters.theta_E
        rays = DaskCalculationDelegate._generate_dask_grid(parameters)
        self._dask_array = da.map_blocks(
            DaskCalculationDelegate._ray_tracer_mapper,
            rays,
            dtype=np.float64,
            name="traced",
            meta=np.array((), dtype=np.float64),
            parameters=parameters
        )
        self._dask_kd_tree = [
            delayed(DaskCalculationDelegate._construct_kd_trees, pure=True)(chunk)
            for chunk in self._dask_array.to_delayed().flatten().tolist()
        ]

    def get_connecting_rays(self, location, radius):
        pass

    def query(self, reducer: QueryReducer) -> np.ndarray:
        reducers = deque()
        for chunk in self._dask_kd_tree:
            reducers.append(
                delayed(DaskCalculationDelegate._query_helper, pure=True)(
                    chunk, reducer.clone()))
        while reducers:
            if len(reducers) == 1:
                final_agg = reducers.popleft()
                result_reducer = final_agg.compute()
                return result_reducer.value
            chunk_a = reducers.popleft()
            chunk_b = reducers.popleft()
            merged = delayed(DaskCalculationDelegate._merge_reducers)(chunk_a, chunk_b)
            reducers.append(merged)

    def query_region(self, region: PixelRegion, radius: u.Quantity) -> np.ndarray:
        return self.query(MagmapReducer(region, radius))

    @staticmethod
    def _generate_dask_grid(parameters: MicrolensingParameters):
        """
        Given a Parameters instance, generates a uniform grid of all the rays that will be traced
        in the form of a dask array.
        """
        region = parameters.ray_region
        region.to(parameters.theta_E)
        # return da.from_array(region.pixels.value, chunks=(4000, 4000, -1))
        x = da.linspace(
            (-region.dimensions.x / 2).value,
            (+region.dimensions.x / 2).value,
            region.resolution.x.value,
            chunks=(PRIMARY_DIMENSION_CHUNK_SIZE,)
        )
        y = da.linspace(
            (-region.dimensions.y / 2).value,
            (+region.dimensions.y / 2).value,
            region.resolution.y.value,
            chunks=(PRIMARY_DIMENSION_CHUNK_SIZE,)
        )
        xx, yy = np.meshgrid(x,y)
        grid = np.stack([xx,yy], 2)
        grid = grid.rechunk((PRIMARY_DIMENSION_CHUNK_SIZE, PRIMARY_DIMENSION_CHUNK_SIZE, -1))
        return grid

    @staticmethod
    def _ray_tracer_mapper(chunk, parameters):
        stars = parameters.stars
        kap, _starry, gam = parameters.mass_descriptors
        traced = np.empty_like(chunk)
        return trace_chunk(chunk, traced, kap, gam, stars)

    @staticmethod
    def _construct_kd_trees(delayed_chunk):
        flattened = np.reshape(delayed_chunk, (delayed_chunk.shape[0]*delayed_chunk.shape[1], 2))
        return cKDTree(flattened, 128, False, False, False)

    @staticmethod
    def _query_helper(subtree, reducer):
        for query in reducer.query_points():
            ray_indices = subtree.query_ball_point((query.x, query.y), query.radius)
            for index in ray_indices:
                query.reduce_ray(subtree.data[index])
            reducer.save_value(query.identifier, query.get_result())
        return reducer

    @staticmethod
    def _merge_reducers(a, b):
        return a.merge(b)
