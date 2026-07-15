from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from k6_charts.charts.base import BaseChart


class LatencyThroughputChart(BaseChart):
    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str = "latency-throughput",
    ) -> str | None:
        vu_corr = ts.get("vu_corr")
        if vu_corr is None or len(vu_corr["vu"]) < 2:
            return None

        rps = vu_corr["rps"]
        p95 = vu_corr["p95"]

        fig, ax = plt.subplots(
            figsize=(9.2, 3.8),
            gridspec_kw={"left": 0.09, "right": 0.975, "top": 0.88, "bottom": 0.14},
        )

        ax.fill_between(rps, p95, alpha=0.10, color=self.p.s1, zorder=1)
        ax.plot(
            rps, p95,
            color=self.p.s1, lw=self.theme.line_width,
            marker="o", ms=self.theme.marker_size,
            mec="white", mew=1.0, zorder=3,
        )

        idx_max = int(np.nanargmax(p95))
        ax.annotate(
            self.fmt_ms(float(p95[idx_max])),
            (rps[idx_max], p95[idx_max]),
            xytext=(8, 6), textcoords="offset points",
            fontsize=9.5, fontweight="bold", color=self.p.s1,
        )

        ax.set_title(
            f"{label} \u2014 Latencia vs Throughput",
            loc="center", fontsize=11, pad=8,
        )
        ax.set_xlabel("Throughput (req/s)", fontsize=8)
        ax.set_ylabel("Latencia p95", fontsize=8)
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylim(bottom=0)
        ax.set_xlim(left=0)
        self.style_ax(ax)

        return self.save(fig, outdir, file_id)
