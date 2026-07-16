from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Palette:
    surface: str = "#fcfcfb"
    panel: str = "#ffffff"
    zebra: str = "#f7f6f3"
    grid: str = "#e6e5e1"
    axis: str = "#c9c8c3"
    ink: str = "#111111"
    ink2: str = "#52514e"
    muted: str = "#8a8a86"

    s1: str = "#2a78d6"
    s2: str = "#1b9e77"
    s3: str = "#4a3aa7"
    s4: str = "#e6772e"

    good: str = "#0a8a0a"
    warn: str = "#d99000"
    crit: str = "#cf2f2f"

    def as_dict(self) -> dict[str, str]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass(frozen=True)
class Theme:
    palette: Palette = field(default_factory=Palette)
    font_family: str = "DejaVu Sans"
    font_size: float = 10.0
    title_size: float = 11.0
    suptitle_size: float = 12.0
    label_size: float = 9.0
    axis_linewidth: float = 0.6
    grid_linewidth: float = 0.5
    tick_length: float = 2.5
    line_width: float = 1.8
    marker_size: float = 5.0
    default_figsize: tuple[float, float] = (7.0, 5.0)
    dpi: int = 300
    style_file: str = "k6_report.mplstyle"
    title_ha: str = "center"
    suptitle_ha: str = "center"

    def apply_rcparams(self) -> None:
        import matplotlib
        matplotlib.use("Agg")

        import matplotlib.pyplot as plt

        p = self.palette
        plt.rcParams.update({
            "font.family": self.font_family,
            "font.size": self.font_size,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "axes.facecolor": "white",
            "axes.edgecolor": p.axis,
            "axes.linewidth": self.axis_linewidth,
            "axes.grid": True,
            "grid.color": p.grid,
            "grid.linewidth": self.grid_linewidth,
            "xtick.color": p.ink2,
            "ytick.color": p.ink2,
            "axes.labelcolor": p.ink2,
            "text.color": p.ink,
            "axes.titleweight": "bold",
            "axes.titlesize": self.title_size,
            "axes.titlepad": 8.0,
            "figure.titleweight": "bold",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        })

    def style_file_path(self) -> Path | None:
        candidates = [
            Path(__file__).parent.parent.parent / "styles" / self.style_file,
            Path.home() / ".config" / "k6_charts" / self.style_file,
        ]
        for p in candidates:
            if p.is_file():
                return p
        return None


def get_default_theme() -> Theme:
    return Theme()
