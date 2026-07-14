"""CdfChart — distribución de latencia (percentiles)."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from k6_charts.charts.base import BaseChart


class CdfChart(BaseChart):
    """Gráfica de distribución acumulada de latencia con percentiles clave."""

    def render(
        self,
        all_dur: np.ndarray,
        label: str,
        outdir: str,
        file_id: str,
    ) -> str | None:
        """Genera la CDF de latencia. Retorna el nombre del archivo o None."""
        if all_dur.size == 0:
            return None

        ps = np.arange(0, 100.1, 0.5)
        vs = np.percentile(all_dur, ps)

        fig, ax = plt.subplots(
            figsize=(9.2, 3.6),
            gridspec_kw={"left": 0.09, "right": 0.975, "top": 0.9, "bottom": 0.14},
        )

        ax.fill_between(ps, vs, color=self.p.s1, alpha=0.10, zorder=1)
        ax.plot(ps, vs, color=self.p.s1, lw=2.1, zorder=2)

        percentiles = [
            (90, self.p.s3),
            (95, self.p.s4),
            (99, self.p.crit),
        ]
        for p_val, col in percentiles:
            v = float(np.percentile(all_dur, p_val))
            ax.plot([p_val, p_val], [0, v], color=col, lw=1.2, ls=":", zorder=3)
            ax.plot(p_val, v, "o", color=col, ms=6, mec="white", mew=1.4, zorder=4)
            ax.annotate(
                f"p{p_val}  {self.fmt_ms(v)}",
                (p_val, v), xytext=(-6, 8), textcoords="offset points",
                ha="right", color=col, fontsize=9.5, fontweight="bold",
            )

        ax.set_title(
            f"{label}  \u00b7  distribuci\u00f3n de latencia (percentiles)",
            loc="left", fontsize=12,
        )
        ax.set_xlabel("Percentil de las peticiones")
        ax.set_ylabel("Latencia")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_xlim(0, 100)
        ax.set_ylim(bottom=0)
        ax.set_xticks([0, 25, 50, 75, 90, 95, 100])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"p{int(v)}"))
        self.style_ax(ax)

        return self.save(fig, outdir, file_id)
