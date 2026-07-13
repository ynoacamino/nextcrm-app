"""StressDegradationChart — curva de degradación VU vs p95/RPS/Error."""

from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

from k6_charts.charts.base import BaseChart


class StressDegradationChart(BaseChart):
    """3 paneles: VU vs p95, VU vs RPS, VU vs Error — para pruebas STRESS."""

    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str = "stress-degradation",
    ) -> str | None:
        vu_corr = ts.get("vu_corr")
        if vu_corr is None or len(vu_corr["vu"]) < 2:
            return None

        vu = vu_corr["vu"]
        fig, axes = plt.subplots(
            3, 1, figsize=(9.2, 7.2), sharex=True,
            gridspec_kw=self._make_gridspec_kw(hspace=0.24, top=0.94, bottom=0.08),
        )

        self._panel_latency_vs_vu(axes[0], vu, vu_corr)
        self._panel_rps_vs_vu(axes[1], vu, vu_corr)
        self._panel_error_vs_vu(axes[2], vu, vu_corr)

        axes[-1].set_xlabel("Usuarios Virtuales (VUs)")
        axes[-1].xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
        fig.suptitle(
            f"{label}  \u00b7  curva de degradaci\u00f3n bajo carga creciente",
            x=0.09, ha="left", fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.995,
        )
        return self.save(fig, outdir, file_id)

    def _panel_latency_vs_vu(
        self, ax: Any, vu: np.ndarray, vu_corr: dict[str, Any],
    ) -> None:
        ax.plot(
            vu, vu_corr["p95"], color=self.p.s1, lw=2.2,
            marker="o", ms=4, mec="white", mew=1.2, zorder=3,
        )
        ax.fill_between(vu, vu_corr["p95"], alpha=0.10, color=self.p.s1, zorder=1)
        ax.set_title("Latencia p95 vs Usuarios Virtuales", loc="left")
        ax.set_ylabel("ms")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

        idx_max = int(np.nanargmax(vu_corr["p95"]))
        ax.annotate(
            self.fmt_ms(float(vu_corr["p95"][idx_max])),
            (vu[idx_max], vu_corr["p95"][idx_max]),
            xytext=(8, 6), textcoords="offset points",
            fontsize=9.5, fontweight="bold", color=self.p.s1,
        )

    def _panel_rps_vs_vu(
        self, ax: Any, vu: np.ndarray, vu_corr: dict[str, Any],
    ) -> None:
        ax.plot(
            vu, vu_corr["rps"], color=self.p.s2, lw=2.2,
            marker="s", ms=4, mec="white", mew=1.2, zorder=3,
        )
        ax.fill_between(vu, vu_corr["rps"], alpha=0.10, color=self.p.s2, zorder=1)
        ax.set_title("Throughput (RPS) vs Usuarios Virtuales", loc="left")
        ax.set_ylabel("req/s")
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

        idx_max = int(np.nanargmax(vu_corr["rps"]))
        ax.annotate(
            f"{vu_corr['rps'][idx_max]:.1f}/s",
            (vu[idx_max], vu_corr["rps"][idx_max]),
            xytext=(8, 6), textcoords="offset points",
            fontsize=9.5, fontweight="bold", color=self.p.s2,
        )

    def _panel_error_vs_vu(
        self, ax: Any, vu: np.ndarray, vu_corr: dict[str, Any],
    ) -> None:
        has_err = bool(np.nanmax(vu_corr["err"]) > 0)
        ecol = self.p.crit if has_err else self.p.good
        ax.plot(
            vu, vu_corr["err"], color=ecol, lw=2.2,
            marker="D", ms=4, mec="white", mew=1.2, zorder=3,
        )
        if has_err:
            ax.fill_between(vu, vu_corr["err"], alpha=0.12, color=ecol, zorder=1)
        ax.set_title("Tasa de error vs Usuarios Virtuales", loc="left")
        ax.set_ylabel("%")
        ymax = max(1.0, float(np.nanmax(vu_corr["err"])) * 1.2) if has_err else 1.0
        ax.set_ylim(0, ymax)
        if not has_err:
            ax.text(
                0.5, 0.5, "0 % \u2014 sin peticiones fallidas",
                transform=ax.transAxes, ha="center", va="center",
                color=self.p.good, fontsize=10.5, fontweight="bold",
            )
        self.style_ax(ax)
