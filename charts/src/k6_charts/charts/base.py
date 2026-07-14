"""BaseChart — clase base para todas las gráficas k6.

Proporciona estilo, guardado y utilidades comunes.
"""

from __future__ import annotations

import os
from abc import ABC

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from k6_charts.config import Theme
from k6_charts.formatters import fmt_ms, fmt_int, fmt_dur, fmt_time_axis


class BaseChart(ABC):
    """Clase base abstracta para todas las gráficas del reporte k6.

    Proporciona:
    - Acceso al tema (Theme) y paleta de colores
    - Método save() para PNG + PDF
    - Método style_ax() para estandarizar ejes
    - Helpers reutilizables para formateo
    """

    def __init__(self, theme: Theme | None = None) -> None:
        self.theme = theme or Theme()
        self.p = self.theme.palette

    def style_ax(self, ax: Axes, ygrid: bool = True) -> None:
        """Aplica el estilo estándar a un eje."""
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.p.axis)
        ax.spines["bottom"].set_color(self.p.axis)
        ax.grid(
            axis="y" if ygrid else "both",
            color=self.p.grid,
            linewidth=self.theme.grid_linewidth,
            zorder=0,
        )
        ax.grid(axis="x", visible=False)
        ax.tick_params(length=self.theme.tick_length, color=self.p.axis)
        ax.set_axisbelow(True)

    def save(self, fig: Figure, outdir: str, name: str) -> str:
        """Guarda la figura en PNG (300 dpi) y PDF vectorial. Cierra la figura."""
        png_path = os.path.join(outdir, name + ".png")
        pdf_path = os.path.join(outdir, name + ".pdf")
        fig.savefig(png_path, dpi=self.theme.dpi)
        fig.savefig(pdf_path)
        plt.close(fig)
        return name

    def fmt_ms(self, v: float | None, _: object = None) -> str:
        """Formatea milisegundos (delega a formatters)."""
        return fmt_ms(v, _)

    def fmt_int(self, v: float | None) -> str:
        """Formatea enteros (delega a formatters)."""
        return fmt_int(v)

    def fmt_dur(self, ms: float | None) -> str:
        """Formatea duración (delega a formatters)."""
        return fmt_dur(ms)

    def fmt_time_axis(self, sec: float, span: float) -> str:
        """Formatea eje de tiempo (delega a formatters)."""
        return fmt_time_axis(sec, span)

    def _make_gridspec_kw(
        self,
        left: float = 0.09,
        right: float = 0.975,
        top: float = 0.95,
        bottom: float = 0.07,
        hspace: float = 0.28,
        wspace: float | None = None,
    ) -> dict[str, float]:
        """Genera gridspec_kw estándar con valores personalizables."""
        kw: dict[str, float] = {
            "left": left,
            "right": right,
            "top": top,
            "bottom": bottom,
        }
        if wspace is not None:
            kw["wspace"] = wspace
        if hspace is not None:
            kw["hspace"] = hspace
        return kw
