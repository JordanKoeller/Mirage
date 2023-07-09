"""
Mirage
======

This is the main module for defining and simulating gravitational lensed systems."""
import logging

logger = logging.getLogger(__name__)

from mirage.util import register_serializers

register_serializers()
from mirage.model import *
from mirage.sim import *
from mirage.calc import *

try:
  from mirage.viz import *
except ImportError:
  logger.info("Matplotlib not installed. Skipping mirage.viz module")
