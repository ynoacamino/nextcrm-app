"""SpikeRecoveryChart — análisis de recuperación post-pico para pruebas SPIKE."""

from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

from k6_charts.charts.base import BaseChart


class SpikeRecoveryChart(BaseChart):
    """3 paneles: VUs + recuperación, latencia + anotaciones, throughput."""

    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str = "spike-recovery",
    ) -> str | None:
        t, span = ts["t"], ts["span"]
        p95, vus = ts["p95"], ts["vus"]

        fig, axes = plt.subplots(
            3, 1, figsize=(9.2, 7.0), sharex=True,
            gridspec_kw=self._make_gridspec_kw(hspace=0.26, top=0.94, bottom=0.08),
        )

        recovery = self._find_recovery(vus, t)

        self._panel_vus_with_recovery(axes[0], t, vus, recovery)
        self._panel_latency_with_recovery(axes[1], t, p95, ts["med"], recovery)
        self._panel_throughput_spike(axes[2], t, ts, span)

        fig.suptitle(
            f"{label}  \u00b7  recuperaci\u00f3n post-pico",
            x=0.09, ha="left", fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.995,
        )
        return self.save(fig, outdir, file_id)

    def _find_recovery(
        self, vus: np.ndarray, t: np.ndarray,
    ) -> dict[str, Any]:
        """Detecta el final del pico y el momento de recuperación."""
        vu_max = float(np.nanmax(vus))
        if vu_max <= 0:
            return {"vu_max": vu_max}

        peak_mask = vus >= vu_max * 0.8
        peak_end_idx = 0
        for i in range(len(vus) - 1, -1, -1):
            if peak_mask[i]:
                peak_end_idx = i
                break

        threshold = vu_max * 0.2
        recovery_idx = peak_end_idx
        for i in range(peak_end_idx, len(vus)):
            if vus[i] <= threshold:
                recovery_idx = i
                break
        else:
            recovery_idx = len(vus) - 1

        return {
            "vu_max": vu_max,
            "peak_end_idx": peak_end_idx,
            "recovery_idx": recovery_idx,
            "t_peak_end": t[peak_end_idx],
            "t_recovery": t[recovery_idx],
            "recovery_s": float(t[recovery_idx] - t[peak_end_idx]),
        }

    def _panel_vus_with_recovery(
        self, ax: Any, t: np.ndarray, vus: np.ndarray,
        recovery: dict[str, Any],
    ) -> None:
        ax.fill_between(t, vus, step="post", color=self.p.s4, alpha=0.16, zorder=1)
        ax.step(t, vus, where="post", color=self.p.s4, lw=1.8, zorder=2)
        ax.set_title("Perfil de carga (VUs)", loc="left")
        ax.set_ylabel("VUs")
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        self.style_ax(ax)

        if recovery["vu_max"] > 0:
            ax.axvspan(
                recovery["t_peak_end"], recovery["t_recovery"],
                alpha=0.15, color=self.p.warn, zorder=0,
            )
            ax.axvline(
                recovery["t_peak_end"], color=self.p.s4,
                ls="--", lw=1.0, alpha=0.6,
            )
            ax.axvline(
                recovery["t_recovery"], color=self.p.good,
                ls="--", lw=1.0, alpha=0.6,
            )

    def _panel_latency_with_recovery(
        self, ax: Any, t: np.ndarray, p95: np.ndarray,
        med: np.ndarray, recovery: dict[str, Any],
    ) -> None:
        ax.plot(t, p95, color=self.p.s1, lw=2.0, label="p95")
        ax.plot(t, med, color=self.p.s3, lw=1.5, label="mediana")
        ax.set_title("Latencia de respuesta", loc="left")
        ax.set_ylabel("ms")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylim(bottom=0)
        ax.legend(loc="upper left", frameon=False, fontsize=9, handlelength=1.4)
        self.style_ax(ax)

        if recovery["vu_max"] <= 0:
            return

        ax.axvspan(
            recovery["t_peak_end"], recovery["t_recovery"],
            alpha=0.15, color=self.p.warn, zorder=0,
        )

        pi = recovery["peak_end_idx"]
        ri = recovery["recovery_idx"]
        peak_p95 = float(np.nanmax(p95[pi:ri + 1])) if ri > pi else float(p95[pi])
        recover_p95 = (
            float(np.nanmean(p95[ri:min(ri + 5, len(p95))]))
            if ri < len(p95) else float(p95[-1])
        )

        ax.annotate(
            f"pico: {self.fmt_ms(peak_p95)}",
            xy=(t[pi + (ri - pi) // 2], peak_p95),
            xytext=(0, 14), textcoords="offset points", ha="center",
            fontsize=9, fontweight="bold", color=self.p.crit,
            arrowprops=dict(arrowstyle="->", color=self.p.crit, lw=1.0),
        )
        ax.annotate(
            f"recuperaci\u00f3n: {self.fmt_ms(recover_p95)}\n\u0394 {recovery['recovery_s']:.0f}s",
            xy=(t[ri], recover_p95),
            xytext=(12, -20), textcoords="offset points",
            fontsize=9, fontweight="bold", color=self.p.good,
            arrowprops=dict(arrowstyle="->", color=self.p.good, lw=1.0),
        )

    def _panel_throughput_spike(
        self, ax: Any, t: np.ndarray, ts: dict[str, Any], span: float,
    ) -> None:
        ax.fill_between(t, ts["rps"], color=self.p.s2, alpha=0.16, zorder=1)
        ax.plot(t, ts["rps"], color=self.p.s2, lw=1.8, zorder=2)
        ax.set_title("Throughput", loc="left")
        ax.set_ylabel("req/s")
        ax.set_ylim(bottom=0)
        self.style_ax(ax)
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: self.fmt_time_axis(v, span))
        )
        ax.set_xlabel("Tiempo transcurrido")
        ax.set_xlim(0, t[-1])
