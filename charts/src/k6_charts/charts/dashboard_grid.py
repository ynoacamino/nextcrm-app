from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.gridspec import GridSpec

from k6_charts.charts.base import BaseChart


class DashboardGridChart(BaseChart):
    MAX_LATENCY_MS = 60000.0

    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str = "dashboard",
    ) -> str | None:
        if ts is None:
            return None

        t, span = ts["t"], ts["span"]

        fig = plt.figure(figsize=(14.0, 9.0))
        gs = GridSpec(
            2, 2, figure=fig,
            hspace=0.35, wspace=0.30,
            left=0.07, right=0.97, top=0.91, bottom=0.08,
        )

        ax_timeline = fig.add_subplot(gs[0, 0])
        ax_cdf = fig.add_subplot(gs[0, 1])
        ax_vus = fig.add_subplot(gs[1, 0])
        ax_lt = fig.add_subplot(gs[1, 1])

        self._panel_timeline_compact(ax_timeline, t, ts)
        self._panel_cdf(ax_cdf, ts)
        self._panel_vus(ax_vus, t, ts)
        self._panel_latency_throughput(ax_lt, ts)

        fig.suptitle(
            f"{label} \u2014 Resumen de rendimiento",
            fontsize=self.theme.suptitle_size,
            fontweight="bold",
            y=0.975,
        )

        return self.save(fig, outdir, file_id)

    def _panel_timeline_compact(
        self, ax: Any, t: np.ndarray, ts: dict[str, Any],
    ) -> None:
        span = ts["span"]
        p95 = self._interp_nans(ts["p95"])
        med = self._interp_nans(ts["med"])
        avg = self._interp_nans(ts["avg"])
        ax.plot(t, p95, color=self.p.s1, lw=self.theme.line_width, label="p95")
        ax.plot(t, med, color=self.p.s3, lw=self.theme.line_width * 0.8, label="Mediana")
        ax.plot(t, avg, color=self.p.muted, lw=1.2, ls="--", label="Media")

        ax.set_title("Latencia en el tiempo", loc="center", fontsize=10, pad=6)
        ax.set_ylabel("ms")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.legend(loc="upper left", frameon=False, fontsize=7.5, ncol=3)
        ax.set_ylim(bottom=0)
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: self.fmt_time_axis(v, span))
        )
        ax.set_xlabel("Tiempo transcurrido", fontsize=8)
        self.style_ax(ax)

    def _panel_cdf(self, ax: Any, ts: dict[str, Any]) -> None:
        all_dur = ts["all_dur"]
        if all_dur.size == 0:
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=self.p.muted)
            ax.set_title("Distribuci\u00f3n de latencia (CDF)", loc="center", fontsize=10, pad=6)
            return

        ps = np.arange(0, 100.1, 0.5)
        vs = np.percentile(all_dur, ps)

        ax.fill_between(ps, vs, color=self.p.s1, alpha=0.08, zorder=1)
        ax.plot(ps, vs, color=self.p.s1, lw=self.theme.line_width, zorder=2)

        for p_val, col in [(90, self.p.s3), (95, self.p.s4), (99, self.p.crit)]:
            v = float(np.percentile(all_dur, p_val))
            ax.plot([p_val, p_val], [0, v], color=col, lw=0.9, ls=":", zorder=3)
            ax.plot(p_val, v, "o", color=col, ms=4, mec="white", mew=1.0, zorder=4)
            ax.annotate(
                f"p{p_val}={self.fmt_ms(v)}",
                (p_val, v), xytext=(-4, 6), textcoords="offset points",
                ha="right", color=col, fontsize=7.5, fontweight="bold",
            )

        ax.set_title("Distribuci\u00f3n de latencia (CDF)", loc="center", fontsize=10, pad=6)
        ax.set_xlabel("Percentil", fontsize=8)
        ax.set_ylabel("Latencia", fontsize=8)
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_xlim(0, 100)
        ax.set_ylim(bottom=0)
        ax.set_xticks([0, 25, 50, 75, 90, 95, 100])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"p{int(v)}"))
        self.style_ax(ax)

    def _panel_vus(self, ax: Any, t: np.ndarray, ts: dict[str, Any]) -> None:
        span = ts["span"]
        ax.fill_between(t, ts["vus"], step="post", color=self.p.s4, alpha=0.12, zorder=1)
        ax.step(t, ts["vus"], where="post", color=self.p.s4, lw=1.5, label="VUs", zorder=2)

        ax.set_title("Perfil de carga", loc="center", fontsize=10, pad=6)
        ax.set_ylabel("Virtuales Users", fontsize=8)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        ax.legend(loc="upper left", frameon=False, fontsize=7.5)
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: self.fmt_time_axis(v, span))
        )
        ax.set_xlabel("Tiempo transcurrido", fontsize=8)
        self.style_ax(ax)

    def _panel_latency_throughput(self, ax: Any, ts: dict[str, Any]) -> None:
        vu_corr = ts.get("vu_corr")
        if vu_corr is None or len(vu_corr["vu"]) < 2:
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=self.p.muted)
            ax.set_title("Latencia vs Throughput", loc="center", fontsize=10, pad=6)
            return

        order = np.argsort(vu_corr["rps"])
        rps = vu_corr["rps"][order]
        p95 = vu_corr["p95"][order]

        mask = ~np.isnan(p95)
        rps, p95 = rps[mask], p95[mask]

        if len(rps) < 2:
            ax.text(0.5, 0.5, "Sin datos suficientes", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=self.p.muted)
            ax.set_title("Latencia vs Throughput", loc="center", fontsize=10, pad=6)
            return

        ax.fill_between(rps, p95, alpha=0.10, color=self.p.s1, zorder=1)
        ax.plot(
            rps, p95,
            color=self.p.s1, lw=self.theme.line_width,
            marker="o", ms=self.theme.marker_size, mec="white", mew=1.0, zorder=3,
        )

        idx_max = int(np.nanargmax(p95))
        ax.annotate(
            self.fmt_ms(float(p95[idx_max])),
            (rps[idx_max], p95[idx_max]),
            xytext=(6, 4), textcoords="offset points",
            fontsize=8, fontweight="bold", color=self.p.s1,
        )

        ax.set_title("Latencia vs Throughput", loc="center", fontsize=10, pad=6)
        ax.set_xlabel("req/s", fontsize=8)
        ax.set_ylabel("p95 (ms)", fontsize=8)
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylim(bottom=0)
        ax.set_xlim(left=0)
        self.style_ax(ax)
