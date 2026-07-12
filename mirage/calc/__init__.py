import functools
import logging

from .kd_tree import FastKdTree as KdTree, PyKdTree, FastKdTree

from .ray_tracer import RayTracer
from .reducer import Reducer
from .reducers import *

from .engine import Engine, ResultCalculator, ResultEvent
from .dask_result_calculator import DaskResultCalculator

from mirage.util import ClusterProvider, Dictify, LocalClusterProvider

logger = logging.getLogger(__name__)


@functools.cache
def get_or_create_engine(cluster_config: str | None = None) -> Engine:
    """
    Create and returns an Engine, using the configs in the provided file. If no
    config is provided, a default Local cluster is used.

    This function caches the result and will return the same object on subsequent
    calls unless a different cluster_config is provided.
    """
    try:
        cluster = Dictify.from_yaml(ClusterProvider, cluster_config)  # type: ignore
        logger.info(
            f"Constructed {type(cluster).__name__} cluster from file {cluster_config}"
        )
    except FileNotFoundError, TypeError:
        logger.warning("No cluster config file found. Using default local cluster")
        cluster = LocalClusterProvider()

    calculator = DaskResultCalculator(cluster_provider=cluster)

    return Engine.create_and_start(calculator)


__all__ = [
    "KdTree",
    "PyKdTree",
    "FastKdTree",
    "RayTracer",
    "Reducer",
    "Engine",
    "ResultEvent",
    "ResultCalculator",
]
