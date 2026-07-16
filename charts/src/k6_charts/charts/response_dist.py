from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

from k6_charts.charts.base import BaseChart


class ResponseDistChart(BaseChart):
    def render(
        self,
        all_dur: np.ndarray,
        label: str,
        outdir: str,
        file_id: str = "response-dist",
    ) -> str | None:
        if all_dur.size == 0:
            return None

        fig, ax = plt.subplots(
            figsize=(9.2, 3.8),
            gridspec_kw={"left": 0.09, "right": 0.975, "top": 0.88, "bottom": 0.14},
        )

        counts, bins, patches = ax.hist(
            all_dur, bins=50, color=self.p.s1, alpha=0.7,
            edgecolor="white", linewidth=0.5, zorder=2,
        )

        for patch in patches:
            patch.set_facecolor(self.p.s1)
            patch.set_alpha(0.7)

        p50 = float(np.percentile(all_dur, 50))
        p95 = float(np.percentile(all_dur, 95))
        p99 = float(np.percentile(all_dur, 99))

        for p_val, col, lbl in [
            (p50, self.p.s3, "p50"),
            (p95, self.p.s4, "p95"),
            (p99, self.p.crit, "p99"),
        ]:
            ax.axvline(p_val, color=col, ls="--", lw=1.2, alpha=0.8, zorder=3)
            ax.text(
                p_val, ax.get_ylim()[1] * 0.92,
                f" {lbl}={self.fmt_ms(p_val)}",
                fontsize=8, fontweight="bold", color=col,
                va="top",
            )

        ax.set_title(
            f"{label} \u2014 Distribuci\u00f3n de tiempos de respuesta",
            loc="center", fontsize=11, pad=8,
        )
        ax.set_xlabel("Tiempo de respuesta (ms)", fontsize=8)
        ax.set_ylabel("Frecuencia", fontsize=8)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=len(all_dur)))
        ax.xaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_xlim(left=0)
        self.style_ax(ax)

        return self.save(fig, outdir, file_id)
