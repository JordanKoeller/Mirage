import dataclasses


@dataclasses.dataclass
class VizConfig:
    io_cache_size: str | int = "4GB"
    default_layers: list[str] = dataclasses.field(default_factory=lambda: ["Debug", "Magmap", "LensedImageController"])
    colormap: str = "RdBu"
    max_fps: int = 20

    

