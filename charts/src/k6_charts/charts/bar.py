"""Bar charts — barras horizontales, agrupadas y por acción."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from k6_charts.charts.base import BaseChart


class HorizontalBarChart(BaseChart):
    """Barras horizontales para comparativas (p95, RPS, errores)."""

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
        """Genera barras horizontales comparativas."""
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
            title, x=0.02, ha="left",
            fontsize=self.theme.suptitle_size, fontweight="bold", y=0.98,
        )
        if subtitle:
            ax.set_title(
                subtitle, loc="left", fontsize=9.5,
                fontweight="normal", color=self.p.muted,
            )

        return self.save(fig, outdir, file_id)


class GroupedBarChart(BaseChart):
    """Barras agrupadas para comparar percentiles entre pruebas."""

    def render(
        self,
        tests: list[dict[str, Any]],
        outdir: str,
        file_id: str = "grouped",
    ) -> str | None:
        """Genera barras agrupadas de latencia por percentil."""
        groups = [
            ("dur_med", "mediana", self.p.s2),
            ("dur_p90", "p90", self.p.s1),
            ("dur_p95", "p95", self.p.s3),
            ("dur_max", "m\u00e1x", self.p.s4),
        ]
        n = len(tests)
        g = len(groups)
        bw = 0.8 / g

        fig, ax = plt.subplots(
            figsize=(9.2, 4.2),
            gridspec_kw={"left": 0.09, "right": 0.975, "top": 0.86, "bottom": 0.12},
        )

        x = np.arange(n)
        for gi, (key, lbl, col) in enumerate(groups):
            vals = [t["s"].get(key) or 0 for t in tests]
            ax.bar(
                x + (gi - (g - 1) / 2) * bw, vals, bw * 0.92,
                label=lbl, color=col, zorder=2,
            )

        ax.set_xticks(x)
        ax.set_xticklabels([t["label"] for t in tests])
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylabel("Latencia")
        ax.legend(
            ncol=4, frameon=False, fontsize=9.5, loc="upper left",
            bbox_to_anchor=(0, 1.14),
        )
        self.style_ax(ax)
        fig.suptitle(
            "Latencia por percentil y por prueba (http_req_duration)",
            x=0.09, ha="left", fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.98,
        )
        return self.save(fig, outdir, file_id)


class PerActionChart(BaseChart):
    """Barras agrupadas de latencia por Server Action (operación)."""

    def render(
        self,
        ts: dict[str, Any],
        label: str,
        outdir: str,
        file_id: str = "per-action",
    ) -> str | None:
        """Genera barras de latencia por operación."""
        action_dur = ts.get("per_action_dur", {})
        if not action_dur:
            return None

        OP_LABELS = {
            "read": "Lectura", "write": "Escritura", "create": "Crear",
            "update": "Actualizar", "delete": "Eliminar", "complex": "Compleja",
        }

        items: list[tuple[str, dict[str, float]]] = []
        for action, durs in sorted(action_dur.items()):
            arr = np.array(durs)
            entity, op = action.split(":", 1) if ":" in action else (action, "")
            op_label = OP_LABELS.get(op, op)
            display = f"{entity} ({op_label})" if op_label else entity
            items.append((display, {
                "med": float(np.percentile(arr, 50)),
                "p90": float(np.percentile(arr, 90)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
                "max": float(arr.max()),
                "count": len(arr),
            }))

        if not items:
            return None

        items.sort(key=lambda x: x[1]["p95"])

        groups = [
            ("med", "mediana", self.p.s2),
            ("p90", "p90", self.p.s1),
            ("p95", "p95", self.p.s3),
            ("p99", "p99", self.p.crit),
        ]
        n = len(items)
        g = len(groups)
        bw = 0.8 / g

        fig, ax = plt.subplots(
            figsize=(9.2, max(4.0, 0.55 * n + 0.8)),
            gridspec_kw={"left": 0.28, "right": 0.95, "top": 0.88, "bottom": 0.10},
        )

        x = np.arange(n)
        for gi, (key, lbl, col) in enumerate(groups):
            vals = [it[1][key] for it in items]
            ax.bar(
                x + (gi - (g - 1) / 2) * bw, vals, bw * 0.88,
                label=lbl, color=col, zorder=2,
            )

        ax.set_xticks(x)
        ax.set_xticklabels([it[0] for it in items], fontsize=9)
        ax.yaxis.set_major_formatter(FuncFormatter(self.fmt_ms))
        ax.set_ylabel("Latencia")
        ax.legend(
            ncol=4, frameon=False, fontsize=9.5, loc="upper left",
            bbox_to_anchor=(0, 1.12),
        )
        self.style_ax(ax)
        ax.set_xlim(-0.5, n - 0.5)
        fig.suptitle(
            f"{label}  \u00b7  latencia por operaci\u00f3n (Server Action)",
            x=0.04, ha="left", fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.98,
        )
        return self.save(fig, outdir, file_id)
