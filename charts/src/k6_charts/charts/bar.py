from __future__ import annotations

from typing import Any, Callable

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from k6_charts.charts.base import BaseChart


class HorizontalBarChart(BaseChart):
    def render(
        self,
        title: str,
        subtitle: str | None,
        items: list[tuple[str, float]],
        formatter: Callable[[float], str] | None = None,
        color: str | Callable[[tuple[str, float]], str] | None = None,
        outdir: str = ".",
        file_id: str = "hbar",
    ) -> str | None:
        if not items:
            return None

        items = list(items)
        labels = [i[0] for i in items]
        vals = [i[1] for i in items]

        if formatter is None:
            formatter = self.fmt_ms

        if callable(color) and not isinstance(color, str):
            colors = [color(item) for item in items]
        elif isinstance(color, str):
            colors = [color] * len(items)
        else:
            colors = [self.p.s1] * len(items)

        fig, ax = plt.subplots(
            figsize=(9.2, 0.7 + 0.52 * len(items) + 0.6),
            gridspec_kw={"left": 0.26, "right": 0.9, "top": 0.8, "bottom": 0.12},
        )

        y = np.arange(len(items))[::-1]
        ax.barh(y, vals, color=colors, height=0.62, zorder=2)

        for yi, v in zip(y, vals):
            ax.annotate(
                formatter(v),
                (v, yi), xytext=(6, 0), textcoords="offset points",
                va="center", ha="left", fontsize=10,
                fontweight="bold", color=self.p.ink,
            )

        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlim(0, (max(vals) * 1.16) or 1.0)
        ax.grid(axis="x", color=self.p.grid, linewidth=self.theme.grid_linewidth)
        ax.grid(axis="y", visible=False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.p.axis)
        ax.spines["bottom"].set_color(self.p.axis)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)

        fig.suptitle(
            title,
            fontsize=self.theme.suptitle_size, fontweight="bold", y=0.98,
        )
        if subtitle:
            ax.set_title(
                subtitle, loc="center", fontsize=9,
                fontweight="normal", color=self.p.muted,
            )

        return self.save(fig, outdir, file_id)


class GroupedBarChart(BaseChart):
    MAX_LATENCY_MS = 60000.0

    def render(
        self,
        tests: list[dict[str, Any]],
        outdir: str,
        file_id: str = "grouped",
    ) -> str | None:
        if not tests:
            return None

        groups = [
            ("dur_med", "Mediana", self.p.s2),
            ("dur_p90", "P90", self.p.s1),
            ("dur_p95", "P95", self.p.s3),
            ("dur_max", "M\u00e1x", self.p.s4),
        ]

        mid = (len(tests) + 1) // 2
        chunk_left = tests[:mid]
        chunk_right = tests[mid:]

        fig, axes = plt.subplots(
            2, 1, figsize=(12.0, 7.0),
            gridspec_kw={"left": 0.10, "right": 0.97, "top": 0.90, "bottom": 0.08, "hspace": 0.45},
        )

        for ax, chunk, x_off in [(axes[0], chunk_left, 0), (axes[1], chunk_right, 0)]:
            if not chunk:
                ax.axis("off")
                continue
            self._render_bars(ax, chunk, groups, x_off)

        fig.suptitle(
            "Percentiles de latencia por prueba (http_req_duration)",
            fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.97,
        )
        return self.save(fig, outdir, file_id)

    def _render_bars(
        self, ax: Any, tests: list[dict[str, Any]],
        groups: list[tuple[str, str, str]], x_off: int,
    ) -> None:
        n = len(tests)
        g = len(groups)
        bw = 0.8 / g
        x = np.arange(n)

        for gi, (key, lbl, col) in enumerate(groups):
            vals = [min(t["s"].get(key) or 0, self.MAX_LATENCY_MS) for t in tests]
            ax.bar(
                x + (gi - (g - 1) / 2) * bw, vals, bw * 0.90,
                label=lbl, color=col, zorder=2,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(
            [t["label"] for t in tests],
            fontsize=7.5, rotation=35, ha="right", rotation_mode="anchor",
        )
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylabel("Latencia", fontsize=8)
        ax.set_ylim(top=self.MAX_LATENCY_MS * 1.1)
        ax.legend(
            ncol=4, frameon=False, fontsize=8, loc="upper left",
            bbox_to_anchor=(0, 1.08),
        )
        self.style_ax(ax)
