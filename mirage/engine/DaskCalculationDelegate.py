
import dask
from dask import array as da
from dask.delayed import delayed
from dask.distributed import Client, LocalCluster
import numpy as np
from scipy.spatial import cKDTree
from collections import deque
from astropy import units as u

from mirage import GlobalPreferences
from mirage.util import PixelRegion, zero_vector
from mirage.parameters import Parameters, MicrolensingParameters
from mirage.engine.micro_ray_tracer import ray_trace_singlethreaded as trace_chunk
from mirage.reducers import MagmapReducer, QueryAccumulator, ReducerTransporter

from .CalculationDelegate import CalculationDelegate

PRIMARY_DIMENSION_CHUNK_SIZE = 2000

class DaskCalculationDelegate(CalculationDelegate):


    def __init__(self, *args, **kwargs):
        self._dask_kd_tree = None
        self.cluster = LocalCluster(n_workers=GlobalPreferences['core_count'])
        self.client = Client(self.cluster)
        print("Dask client UI at ", self.client.dashboard_link)
        # dask.config.set(scheduler="threads")

    def reconfigure(self, parameters: MicrolensingParameters):
        inputUnit = parameters.theta_E
        rayRegion = parameters.ray_region.centered_on(zero_vector(parameters.ray_region.center.unit))
        rayRegion.to(parameters.theta_E)
        self._dask_kd_tree = [
            delayed(DaskCalculationDelegate._ray_trace, pure=True)(chunk, parameters)
            for chunk in rayRegion.subdivide(PRIMARY_DIMENSION_CHUNK_SIZE)
        ]

    def get_connecting_rays(self, location, radius):
        pass

    def query(self, reducer: QueryAccumulator) -> QueryAccumulator:
        reducers = deque()
        for chunk in self._dask_kd_tree:
            reducers.append(
                delayed(DaskCalculationDelegate._query_helper, pure=True)(
                    chunk, ReducerTransporter.from_reducer(reducer)))
        while reducers:
            if len(reducers) == 1:
                final_agg = reducers.popleft()
                result_reducer = final_agg.compute()
                return result_reducer.get_reducer()
            chunk_a = reducers.popleft()
            chunk_b = reducers.popleft()
            merged = delayed(DaskCalculationDelegate._merge_reducers)(chunk_a, chunk_b)
            reducers.append(merged)

    def query_region(self, region: PixelRegion, radius: u.Quantity) -> QueryAccumulator:
        return self.query(MagmapReducer(region, radius))

    @staticmethod
    def _ray_tracer_mapper(chunk, parameters):
        stars = parameters.stars
        kap, _starry, gam = parameters.mass_descriptors
        traced = np.empty_like(chunk)
        return trace_chunk(chunk, traced, kap, gam, stars)

    @staticmethod
    def _ray_trace(subregion, parameters):
        pixels = subregion.pixels.value
        stars = parameters.stars
        kap, _starry, gam = parameters.mass_descriptors
        traced = np.empty_like(pixels)
        traced = trace_chunk(pixels, traced, kap, gam, stars)
        flattened_rays = np.reshape(traced, (traced.shape[0]*traced.shape[1], 2))
        return cKDTree(flattened_rays, 128, False, False, False)



    @staticmethod
    def _query_helper(subtree, reducer_transporter):
        reducer = reducer_transporter.get_reducer()
        reducer.start_iteration()
        while reducer.has_next_accumulator():
            accumulator = reducer.next_accumulator()
            query = accumulator.query_point()
            for index in subtree.query_ball_point((query['x'], query['y']), query['r']):
                accumulator.reduce_ray(subtree.data[index])
            reducer.save_value(accumulator.get_result())
        return ReducerTransporter.from_reducer(reducer)

    @staticmethod
    def _merge_reducers(a, b):
        reducer_a, reducer_b = a.get_reducer(), b.get_reducer()
        return ReducerTransporter.from_reducer(reducer_a.merge(reducer_b))
