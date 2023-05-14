from dataclasses import dataclass

from mirage.model import Quasar
from mirage.util import Vec2D, Region


@dataclass(frozen=True)
class SourcePlane:
    quasar: Quasar
    source_region: Region
