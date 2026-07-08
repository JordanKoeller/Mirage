from typing import Self, Optional, List
from dataclasses import dataclass
from functools import cached_property, cache
from astropy.io import fits

from mirage.calc import Reducer, KdTree
from mirage.calc.reducer_funcs import populate_magmap, populate_lightcurve, slice_magmap, merge_index_lists, populate_lensed_image
from mirage.util import Vec2D, PixelRegion, DelegateRegistry, Region, Index2D
from mirage.sim import MicrolensingSimulation
from mirage_ext import reduce_lensed_image
from mirage.io import ReducerReporter

import numpy as np
from astropy import units as u

HIT_COLOR = np.array([120, 120, 255], dtype=np.uint8)

def unlensed_pixel_count(simulation: MicrolensingSimulation, quasar_radius: u.Quantity) -> int:
    source_region = simulation.source_plane.source_region
    pixel_region = simulation.get_ray_bundle().to("uas")
    apparent_quasar_area = (
        quasar_radius.to("uas") ** 2
        * simulation.lensing_system.magnification_coefficient(
            source_region.center
        )
        * np.pi
    )
    return apparent_quasar_area / (
        pixel_region.delta.x * pixel_region.delta.y
    ).to("uas2")

@dataclass(frozen=True)
class Lightcurve:
    data: np.ndarray # 1-dimensional array of QSO proportional to brightness of the QSO without microlensing.
    start_pos: Vec2D # Starting position of the lightcurve.
    end_pos: Vec2D # ending point of the lightcurve (inclusive).

    @property
    def magnitudes(self) -> np.ndarray:
        return -2.5 * np.log10(self.data)


@DelegateRegistry.register
@dataclass(kw_only=True)
class LensedImageReducer(Reducer):
    query: Vec2D # Location to query
    radius: u.Quantity # Radius of the QSO
    resolution: Vec2D # Resolution of the image to render

    def initialize(self, simulation: MicrolensingSimulation):
        self._lens_plane = simulation.get_ray_bundle()
        self.unlensed_pixel_count = unlensed_pixel_count(simulation, self.radius)
        self._canvas = None
        self.theta_0 = simulation.lensing_system.theta_0

    def reduce(self, traced_rays: KdTree):
        active_indices = np.array(traced_rays.query_indices(
            self.query.to(self.theta_0), self.radius.to(self.theta_0)
        ))
        if active_indices is None or len(active_indices) == 0:
            return
        self._canvas = populate_lensed_image(active_indices, self._lens_plane, self.resolution)

    def merge(self, other: Self) -> Self:
        if other._canvas is None:
            return self
        if self._canvas is None:
            self._canvas = other._canvas
            return self
        self._canvas = self._canvas + other._canvas
        return self

    @property
    def output(self) -> np.ndarray | None:
        return self._canvas


    def set_output(self, output: object):
        self._canvas = output

    def save(self, reporter: ReducerReporter) -> None:
        with reporter.writer("canvas.npy") as f:
            np.save(f, self._canvas)

    def load(self, reporter: ReducerReporter) -> None:
        with reporter.reader("canvas.npy") as f:
            self._canvas = np.load(f)


@DelegateRegistry.register
@dataclass(kw_only=True)
class MagnificationMapReducer(Reducer):
    radius: u.Quantity
    resolution: Vec2D
    canvas: Optional[np.ndarray] = None

    def initialize(self, simulation: MicrolensingSimulation):
        self.source_region = simulation.source_plane.source_region
        self.unlensed_pixel_count = unlensed_pixel_count(simulation, self.radius)
        self.theta_0 = simulation.lensing_system.theta_0

    def reduce(self, traced_rays: KdTree):
        pixels = u.Quantity(np.ascontiguousarray(self.pixel_region.to(self.theta_0).pixels.value), self.theta_0)
        radius = self.radius.to(self.theta_0)

        self.canvas = np.array(traced_rays.batch_query_count(pixels, radius))

    def merge(self, other: Self) -> Self:
        other_canvas = other.canvas
        if self.canvas is not None and other_canvas is not None:
            self.canvas += other_canvas
        elif other_canvas is not None:
            self.canvas = other_canvas
        return self

    @property
    def pixel_region(self) -> PixelRegion:
        return PixelRegion(
            dims=self.source_region.to("uas").dims,
            center=self.source_region.to("uas").center,
            resolution=self.resolution,
        )

    @property
    def output(self) -> Optional[np.ndarray]:
        if self.canvas is not None:
            return np.copy(self.canvas)
        return None

    def save(self, reporter: ReducerReporter) -> None:
        with reporter.writer("canvas.npy") as f:
            np.save(f, self.canvas)
        with reporter.writer("magmap.fits") as f:
            # header = fits.Header(headerFields)
            hdu = fits.PrimaryHDU(self.magnitudes) #, header=header)
            hdulist = fits.HDUList([hdu])
            hdulist.writeto(f)

    def load(self, reporter: ReducerReporter) -> None:
        with reporter.reader("canvas.npy") as f:
            self.canvas = np.load(f)

    @cached_property
    def magnitudes(self) -> np.ndarray:
        if self.output is None:
            raise ValueError("Cannot compute magnitudes for empty reducer")
        return -2.5 * np.log10(self.output / self.unlensed_pixel_count)

    def set_output(self, output: object):
        self.canvas = output  # type: ignore

    def slice(self, start: Vec2D | Index2D, end: Vec2D | Index2D) -> tuple[u.Quantity, np.ndarray]:
        """
        Sample the MagnificationMap on an arbitrary axis.

        Returns a ndarray[np.float64, ndim=1] of all the magnification values
        under the line connecting `start` to `end` using nearest-neighbor
        interpolation.
        """
        if isinstance(start, Index2D):
            start = self.pixel_region[start]
        if isinstance(end, Index2D):
            end = self.pixel_region[end]
        dist = (end - start).magnitude
        values = slice_magmap(self, start, end)
        return u.Quantity(np.linspace(0, dist.value, len(values)), self.source_region.unit), values


@DelegateRegistry.register
@dataclass(kw_only=True)
class LightCurvesReducer(Reducer):
    radius: u.Quantity
    resolution: u.Quantity  # In units of N/dist or dist
    num_curves: int
    seed: Optional[int]

    def initialize(self, simulation: MicrolensingSimulation):
        self._curves: List[np.ndarray] = [None for i in range(self.num_curves)]
        self.source_region = simulation.source_plane.source_region
        self.unlensed_pixel_count = unlensed_pixel_count(simulation, self.radius)
        self.theta_0 = simulation.lensing_system.theta_0

    def reduce(self, traced_rays: KdTree):
        query_points = self.get_query_points(self.source_region)
        radius = self.radius.to(self.theta_0).value
        for i in range(self.num_curves):
            queries = query_points[i].to(self.theta_0)
            self._curves[i] = Lightcurve(
                data=populate_lightcurve(queries.value, radius, traced_rays) / self.unlensed_pixel_count,
                start_pos=Vec2D(queries[0][0], queries[0][1]), # Might need to swap 2nd indices
                end_pos=Vec2D(queries[-1][0], queries[-1][1]),
            )

    def merge(self, other: Self) -> Self:
        for i in range(self.num_curves):
            if self._curves[i] is not None and other._curves[i] is not None:
                self._curves[i] = Lightcurve(
                    data=self._curves[i].data + other._curves[i].data,
                    start_pos=self._curves[i].start_pos,
                    end_pos=self._curves[i].end_pos,
                )
            elif other._curves[i] is not None:
                self._curves[i] = other._curves[i]
        return self

    @property
    def output(self):
        return self._curves

    @property
    def lightcurves(self):
        return self._curves

    def set_output(self, output: object):
        self._curves = output  # type: ignore

    def save(self, reporter: ReducerReporter) -> None:
        with reporter.writer("lightcurves.pickle") as f:
            pickle.dump(self._curves, f)

    def load(self, reporter: ReducerReporter) -> None:
        with reporter.reader("lightcurves.pickle") as f:
            self._curves = pickle.load(f)

    def get_query_points(self, region: Region) -> List[u.Quantity]:
        """
        Returns a list of fully interpolated, randomly generated query points,
        where each element of the list is all the query points for a single
        light curve.
        """
        lines = []
        query_seeds = self.get_query_seeds(region)
        diff = self.resolution
        if u.get_physical_type(self.resolution) == u.get_physical_type(
            (1.0 / query_seeds)
        ):
            diff = 1.0 / self.resolution
        diff = diff.to(region.unit)
        for i in range(self.num_curves):
            x0, y0, x1, y1 = query_seeds[i]
            direction = (Vec2D(x1, y1) - Vec2D(x0, y0)).direction
            xs = np.arange(x0.value, x1.value, direction.x.value * diff.value)
            ys = np.arange(y0.value, y1.value, direction.y.value * diff.value)
            num_pts = min(xs.size, ys.size)
            line: np.ndarray = np.ndarray((num_pts, 2))
            line[:, 0] = xs[:num_pts]
            line[:, 1] = ys[:num_pts]
            lines.append(u.Quantity(line, region.unit))
        return lines

    def get_query_seeds(self, region: Region) -> u.Quantity:
        """
        Generate all the query points for this reducer.

        generates two random coordinates in the lens plane `num_curves` many times,
        connects them with a line, then interpolates them onto a bounding box of [-0.5, 0.5].
        """
        rng = np.random.default_rng(self.seed)
        points = rng.random((self.num_curves, 4))
        dx = points[:, 2] - points[:, 0]
        dy = points[:, 3] - points[:, 1]
        ms = dy / dx
        ps = points[:, :2]
        # y - y1 = m(x - x1)
        # y = m(x - x1) + y1
        # y = mx - mx1 + y1
        # Thus, b = (-m*x1 + y1).
        y0s = -ms * ps[:, 0] + ps[:, 1]  # y at x = 0
        # letting y = 0, 0 = mx + b ==> -b/m = x
        x0s = -y0s / ms  # x at y = 0
        y1s = ms + y0s  # y at x = 1
        # letting y = 1, 1 = mx + b ==> 1 - b = mx ==> (1 - b) / m = x
        x1s = (1 - y0s) / ms
        rows = []
        e = 1e-6  # tolerance
        for i in range(self.num_curves):
            row = []
            if y0s[i] <= (1.0 + e) and y0s[i] >= (0.0 - e):
                row.extend([0.0, y0s[i]])
            if x0s[i] <= (1.0 + e) and x0s[i] >= (0.0 - e):
                row.extend([x0s[i], 0.0])
            if y1s[i] <= (1.0 + e) and y1s[i] >= (0.0 - e):
                row.extend([1.0, y1s[i]])
            if x1s[i] <= (1.0 + e) and x1s[i] >= (0.0 - e):
                row.extend([x1s[i], 1.0])
            rows.append(row)
        centered_points = np.array(rows) - 0.5
        center = (
            region.center
            if region.center is not None
            else Vec2D.zero_vector(region.unit)
        )
        scaled_points: np.ndarray = np.ndarray((self.num_curves, 4))
        scaled_points[:, 0] = (
            centered_points[:, 0] * region.dims.x.value + center.x.value
        )
        scaled_points[:, 1] = (
            centered_points[:, 1] * region.dims.y.value + center.y.value
        )
        scaled_points[:, 2] = (
            centered_points[:, 2] * region.dims.x.value + center.x.value
        )
        scaled_points[:, 3] = (
            centered_points[:, 3] * region.dims.y.value + center.y.value
        )
        return u.Quantity(scaled_points, region.unit)
