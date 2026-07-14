from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

from k6_charts.charts.base import BaseChart


class TimelineChart(BaseChart):
    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str,
    ) -> str | None:
        has_err = bool(np.nanmax(ts["err"]) > 0)
        fig, axes = plt.subplots(
            4, 1,
            figsize=(9.2, 8.4),
            sharex=True,
            gridspec_kw=self._make_gridspec_kw(hspace=0.28),
        )
        t, span = ts["t"], ts["span"]

        self._panel_latency(axes[0], t, ts)
        self._panel_vus(axes[1], t, ts)
        self._panel_throughput(axes[2], t, ts)
        self._panel_error(axes[3], t, ts, has_err, span)

        fig.suptitle(
            f"{label} \u2014 Perfil temporal de la prueba",
            fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.995,
        )
        fig.text(
            0.975, 0.008,
            f"Duraci\u00f3n {self.fmt_dur(span * 1000)} \u00b7 {ts['bs']} s/punto",
            ha="right", color=self.p.muted, fontsize=7.5,
        )
        return self.save(fig, outdir, file_id)

    def _panel_latency(self, ax: Any, t: np.ndarray, ts: dict[str, Any]) -> None:
        p95 = self._interp_nans(ts["p95"])
        med = self._interp_nans(ts["med"])
        avg = self._interp_nans(ts["avg"])
        ax.plot(t, p95, color=self.p.s1, lw=self.theme.line_width, label="p95")
        ax.plot(t, med, color=self.p.s3, lw=self.theme.line_width * 0.8, label="Mediana")
        ax.plot(t, avg, color=self.p.muted, lw=1.2, ls="--", label="Media")
        ax.set_title("Latencia de respuesta", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("ms")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.legend(
            loc="upper left", ncol=3, frameon=False, fontsize=7.5,
            handlelength=1.4, bbox_to_anchor=(0, 1.02),
        )
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

    def _panel_vus(self, ax: Any, t: np.ndarray, ts: dict[str, Any]) -> None:
        ax.fill_between(t, ts["vus"], step="post", color=self.p.s4, alpha=0.16, zorder=1)
        ax.step(t, ts["vus"], where="post", color=self.p.s4, lw=self.theme.line_width, zorder=2)
        ax.set_title("Usuarios virtuales (VUs)", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("VUs")
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        self.style_ax(ax)

    def _panel_throughput(self, ax: Any, t: np.ndarray, ts: dict[str, Any]) -> None:
        ax.fill_between(t, ts["rps"], color=self.p.s2, alpha=0.16, zorder=1)
        ax.plot(t, ts["rps"], color=self.p.s2, lw=self.theme.line_width, zorder=2)
        ax.set_title("Throughput", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("req/s")
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

    def _panel_error(
        self, ax: Any, t: np.ndarray, ts: dict[str, Any],
        has_err: bool, span: float,
    ) -> None:
        ecol = self.p.crit if has_err else self.p.good
        if has_err:
            ax.fill_between(t, ts["err"], step="post", color=ecol, alpha=0.18, zorder=1)
        ax.step(t, ts["err"], where="post", color=ecol, lw=self.theme.line_width, zorder=2)
        ax.set_title("Tasa de error", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("%")
        ax.set_ylim(0, max(1.0, float(np.nanmax(ts["err"])) * 1.2))
        if not has_err:
            ax.text(
                0.5, 0.5, "0% \u2014 Sin peticiones fallidas",
                transform=ax.transAxes, ha="center", va="center",
                color=self.p.good, fontsize=9, fontweight="bold",
            )
        self.style_ax(ax)
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: self.fmt_time_axis(v, span))
        )
        ax.set_xlabel("Tiempo transcurrido", fontsize=8)
        ax.set_xlim(0, t[-1])
