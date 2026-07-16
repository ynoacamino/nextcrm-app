from __future__ import annotations

from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.gridspec import GridSpec

from k6_charts.charts.base import BaseChart


class ComparisonGridChart(BaseChart):
    MAX_LATENCY_MS = 60000.0

    def render(
        self,
        results: list[dict[str, Any]],
        outdir: str,
        file_id: str = "comparison-grid",
    ) -> str | None:
        if len(results) < 2:
            return None

        wd = [t for t in results if t["s"].get("dur_p95") is not None]
        if not wd:
            return None

        fig = plt.figure(figsize=(14.0, 9.0))
        gs = GridSpec(
            2, 2, figure=fig,
            hspace=0.40, wspace=0.35,
            left=0.07, right=0.97, top=0.91, bottom=0.08,
        )

        ax_p95 = fig.add_subplot(gs[0, 0])
        ax_rps = fig.add_subplot(gs[0, 1])
        ax_err = fig.add_subplot(gs[1, 0])
        ax_grouped = fig.add_subplot(gs[1, 1])

        self._panel_p95(ax_p95, wd)
        self._panel_rps(ax_rps, results)
        self._panel_error(ax_err, results)
        self._panel_grouped(ax_grouped, wd)

        fig.suptitle(
            "Comparativa cross-tipo de pruebas de rendimiento",
            fontsize=self.theme.suptitle_size,
            fontweight="bold",
            y=0.975,
        )

        return self.save(fig, outdir, file_id)

    def _panel_p95(self, ax: Any, tests: list[dict[str, Any]]) -> None:
        items = sorted(
            [(t["label"], t["s"]["dur_p95"]) for t in tests],
            key=lambda x: x[1],
        )
        labels = [i[0] for i in items]
        vals = [i[1] for i in items]
        colors = [self.p.s1] * len(items)

        y = np.arange(len(items))[::-1]
        ax.barh(y, vals, color=colors, height=0.6, zorder=2)

        for yi, v in zip(y, vals):
            ax.annotate(
                self.fmt_ms(v),
                (v, yi), xytext=(5, 0), textcoords="offset points",
                va="center", ha="left", fontsize=8,
                fontweight="bold", color=self.p.ink,
            )

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlim(0, (max(vals) * 1.18) or 1.0)
        ax.set_title("Latencia p95 (menor es mejor)", loc="center", fontsize=10, pad=6)
        ax.set_xlabel("ms", fontsize=8)
        self.style_ax(ax)
        ax.tick_params(length=0)

    def _panel_rps(self, ax: Any, tests: list[dict[str, Any]]) -> None:
        items = sorted(
            [(t["label"], t["s"].get("rps") or 0) for t in tests if t["s"].get("rps") is not None],
            key=lambda x: -x[1],
        )
        if not items:
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=self.p.muted)
            ax.set_title("Throughput (mayor es mejor)", loc="center", fontsize=10, pad=6)
            return

        labels = [i[0] for i in items]
        vals = [i[1] for i in items]

        y = np.arange(len(items))[::-1]
        ax.barh(y, vals, color=self.p.s2, height=0.6, zorder=2)

        for yi, v in zip(y, vals):
            ax.annotate(
                f"{v:.2f}/s",
                (v, yi), xytext=(5, 0), textcoords="offset points",
                va="center", ha="left", fontsize=8,
                fontweight="bold", color=self.p.ink,
            )

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlim(0, (max(vals) * 1.18) or 1.0)
        ax.set_title("Throughput RPS (mayor es mejor)", loc="center", fontsize=10, pad=6)
        ax.set_xlabel("req/s", fontsize=8)
        self.style_ax(ax)
        ax.tick_params(length=0)

    def _panel_error(self, ax: Any, tests: list[dict[str, Any]]) -> None:
        items = sorted(
            [(t["label"], t["s"].get("err_rate") or 0) for t in tests if t["s"].get("err_rate") is not None],
            key=lambda x: -x[1],
        )
        if not items:
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=self.p.muted)
            ax.set_title("Tasa de error (menor es mejor)", loc="center", fontsize=10, pad=6)
            return

        labels = [i[0] for i in items]
        vals = [i[1] for i in items]
        colors = [
            self.p.good if v <= 0.5 else self.p.warn if v <= 2 else self.p.crit
            for v in vals
        ]

        y = np.arange(len(items))[::-1]
        ax.barh(y, vals, color=colors, height=0.6, zorder=2)

        for yi, v in zip(y, vals):
            ax.annotate(
                f"{v:.2f}%",
                (v, yi), xytext=(5, 0), textcoords="offset points",
                va="center", ha="left", fontsize=8,
                fontweight="bold", color=self.p.ink,
            )

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlim(0, (max(vals) * 1.18) or 1.0)
        ax.axvline(0.5, color=self.p.warn, ls=":", lw=0.8, alpha=0.6)
        ax.axvline(2.0, color=self.p.crit, ls=":", lw=0.8, alpha=0.6)
        ax.set_title("Tasa de error (menor es mejor)", loc="center", fontsize=10, pad=6)
        ax.set_xlabel("%", fontsize=8)
        self.style_ax(ax)
        ax.tick_params(length=0)

    def _panel_grouped(self, ax: Any, tests: list[dict[str, Any]]) -> None:
        groups = [
            ("dur_med", "Mediana", self.p.s2),
            ("dur_p90", "P90", self.p.s1),
            ("dur_p95", "P95", self.p.s3),
            ("dur_max", "M\u00e1x", self.p.s4),
        ]
        n = len(tests)
        g = len(groups)
        bw = 0.8 / g

        x = np.arange(n)
        for gi, (key, lbl, col) in enumerate(groups):
            vals = [min(t["s"].get(key) or 0, self.MAX_LATENCY_MS) for t in tests]
            ax.bar(
                x + (gi - (g - 1) / 2) * bw, vals, bw * 0.88,
                label=lbl, color=col, zorder=2,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(
            [t["label"] for t in tests],
            fontsize=6.5, rotation=40, ha="right", rotation_mode="anchor",
        )
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylabel("Latencia", fontsize=7)
        ax.set_ylim(top=self.MAX_LATENCY_MS * 1.1)
        ax.legend(
            ncol=4, frameon=False, fontsize=7, loc="upper left",
        )
        ax.set_title("Percentiles de latencia por prueba", loc="center", fontsize=9, pad=6)
        self.style_ax(ax)
