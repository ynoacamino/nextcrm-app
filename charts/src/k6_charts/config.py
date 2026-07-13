"""Theme — configuración centralizada de colores, fuentes y tamaños."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Palette:
    """Paleta de colores validada y accessible (colorblind-safe)."""

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
        """Devuelve la paleta como diccionario plano."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass(frozen=True)
class Theme:
    """Configuración completa de estilo para los reportes."""

    palette: Palette = field(default_factory=Palette)
    font_family: str = "DejaVu Sans"
    font_size: float = 10.5
    title_size: float = 11.5
    suptitle_size: float = 13.0
    label_size: float = 9.5
    axis_linewidth: float = 0.8
    grid_linewidth: float = 0.8
    tick_length: float = 3.0
    line_width: float = 2.0
    marker_size: float = 6.0
    default_figsize: tuple[float, float] = (9.2, 6.0)
    dpi: int = 300
    style_file: str = "k6_report.mplstyle"

    def apply_rcparams(self) -> None:
        """Aplica la configuración al global rcParams de matplotlib."""
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
            "svg.fonttype": "none",
        })

    def style_file_path(self) -> Path | None:
        """Busca el archivo .mplstyle en ubicaciones conocidas."""
        candidates = [
            Path(__file__).parent.parent.parent / "styles" / self.style_file,
            Path.home() / ".config" / "k6_charts" / self.style_file,
        ]
        for p in candidates:
            if p.is_file():
                return p
        return None


def get_default_theme() -> Theme:
    """Retorna el tema por defecto."""
    return Theme()
