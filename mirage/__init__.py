"""
Mirage
======

This is the main module for defining and simulating gravitational lensed systems."""

from mirage.calc import *
from mirage.sim import *
from mirage.model import *
from mirage.util import register_serializers
import logging

logger = logging.getLogger(__name__)


register_serializers()

try:
    from mirage.viz import *
except ImportError:
    logger.info("Matplotlib not installed. Skipping mirage.viz module")
