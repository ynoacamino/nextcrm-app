from __future__ import annotations

import os
from abc import ABC

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from k6_charts.config import Theme
from k6_charts.formatters import fmt_ms, fmt_int, fmt_dur, fmt_time_axis


class BaseChart(ABC):
    def __init__(self, theme: Theme | None = None) -> None:
        self.theme = theme or Theme()
        self.p = self.theme.palette

    def style_ax(self, ax: Axes, ygrid: bool = True) -> None:
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
        svg_path = os.path.join(outdir, name + ".svg")
        fig.savefig(svg_path)
        plt.close(fig)
        return name

    def fmt_ms(self, v: float | None, _: object = None) -> str:
        return fmt_ms(v, _)

    def fmt_int(self, v: float | None) -> str:
        return fmt_int(v)

    def fmt_dur(self, ms: float | None) -> str:
        return fmt_dur(ms)

    def fmt_time_axis(self, sec: float, span: float) -> str:
        return fmt_time_axis(sec, span)

    def _interp_nans(self, arr: np.ndarray) -> np.ndarray:
        if not np.any(np.isnan(arr)):
            return arr
        mask = ~np.isnan(arr)
        if mask.sum() < 2:
            return arr
        return np.interp(np.arange(len(arr)), np.where(mask)[0], arr[mask])

    def _make_gridspec_kw(
        self,
        left: float = 0.09,
        right: float = 0.975,
        top: float = 0.95,
        bottom: float = 0.07,
        hspace: float = 0.28,
        wspace: float | None = None,
    ) -> dict[str, float]:
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
