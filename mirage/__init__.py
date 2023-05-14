"""
Mirage
======

This is the main module for defining and simulating gravitational lensed systems.
"""
from mirage.util import register_serializers
register_serializers()
from mirage.model import *
from mirage.sim import *
from mirage.calc import *
from mirage.viz import *
