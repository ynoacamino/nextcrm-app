from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

from k6_charts.charts.base import BaseChart


class CrossComparisonChart(BaseChart):
    KIND_ORDER = ["PRLOAD", "PRSTRESS", "PRSPIKE", "PRSOAK"]
    KIND_LABELS = {"PRLOAD": "LOAD", "PRSTRESS": "STRESS", "PRSPIKE": "SPIKE", "PRSOAK": "SOAK"}

    def render(
        self,
        results: list[dict[str, Any]],
        outdir: str,
        file_id: str = "cross-comparison",
    ) -> str | None:
        by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for t in results:
            k = t.get("kind")
            if k and t["s"].get("dur_p95") is not None:
                by_kind[k].append(t)

        if len(by_kind) < 2:
            return None

        present = [k for k in self.KIND_ORDER if k in by_kind]
        kind_colors = {
            "PRLOAD": self.p.s1, "PRSTRESS": self.p.s2,
            "PRSPIKE": self.p.s3, "PRSOAK": self.p.s4,
        }

        fig, axes = plt.subplots(
            2, 2, figsize=(9.2, 7.0),
            gridspec_kw=self._make_gridspec_kw(
                hspace=0.32, wspace=0.28, top=0.92, bottom=0.08,
            ),
        )

        self._panel_p95(axes[0, 0], by_kind, present, kind_colors)
        self._panel_rps(axes[0, 1], by_kind, present, kind_colors)
        self._panel_error(axes[1, 0], by_kind, present, kind_colors)
        self._panel_vus(axes[1, 1], by_kind, present, kind_colors)

        fig.suptitle(
            "Comparativa cross-tipo de pruebas de rendimiento",
            fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.995,
        )
        return self.save(fig, outdir, file_id)

    def _panel_p95(
        self, ax: Any, by_kind: dict, present: list, kind_colors: dict,
    ) -> None:
        vals = [np.mean([t["s"]["dur_p95"] for t in by_kind[k]]) for k in present]
        cols = [kind_colors[k] for k in present]
        ax.bar(range(len(present)), vals, color=cols, width=0.6, zorder=2)
        for i, v in enumerate(vals):
            ax.text(
                i, v, self.fmt_ms(v), ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=self.p.ink,
            )
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels([self.KIND_LABELS[k] for k in present])
        ax.set_title("Latencia p95 promedio", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("ms")
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

    def _panel_rps(
        self, ax: Any, by_kind: dict, present: list, kind_colors: dict,
    ) -> None:
        vals = [np.mean([t["s"]["rps"] for t in by_kind[k] if t["s"].get("rps")]) for k in present]
        cols = [kind_colors[k] for k in present]
        ax.bar(range(len(present)), vals, color=cols, width=0.6, zorder=2)
        for i, v in enumerate(vals):
            ax.text(
                i, v, f"{v:.1f}/s", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=self.p.ink,
            )
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels([self.KIND_LABELS[k] for k in present])
        ax.set_title("Throughput promedio", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("req/s")
        ax.set_ylim(bottom=0)
        self.style_ax(ax)

    def _panel_error(
        self, ax: Any, by_kind: dict, present: list, kind_colors: dict,
    ) -> None:
        vals = [
            np.mean([t["s"]["err_rate"] for t in by_kind[k] if t["s"].get("err_rate") is not None])
            for k in present
        ]
        err_cols = [
            self.p.good if v <= 0.5 else self.p.warn if v <= 2 else self.p.crit
            for v in vals
        ]
        ax.bar(range(len(present)), vals, color=err_cols, width=0.6, zorder=2)
        for i, v in enumerate(vals):
            ax.text(
                i, v, f"{v:.2f}%", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=self.p.ink,
            )
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels([self.KIND_LABELS[k] for k in present])
        ax.set_title("Tasa de error promedio", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("%")
        ax.set_ylim(bottom=0)
        self.style_ax(ax)
        ax.axhline(0.5, color=self.p.warn, ls=":", lw=1.0, alpha=0.6)

    def _panel_vus(
        self, ax: Any, by_kind: dict, present: list, kind_colors: dict,
    ) -> None:
        vals = [max((t["s"].get("vus_max") or 0) for t in by_kind[k]) for k in present]
        cols = [kind_colors[k] for k in present]
        ax.bar(range(len(present)), vals, color=cols, width=0.6, zorder=2)
        for i, v in enumerate(vals):
            ax.text(
                i, v, self.fmt_int(v), ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=self.p.ink,
            )
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels([self.KIND_LABELS[k] for k in present])
        ax.set_title("VUs m\u00e1ximos alcanzados", loc="center", fontsize=9.5, pad=6)
        ax.set_ylabel("VUs")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        ax.set_ylim(bottom=0)
        self.style_ax(ax)
