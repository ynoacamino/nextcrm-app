"""InfraTimelineChart — métricas de infraestructura (CPU, Memory, DB)."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from k6_charts.charts.base import BaseChart


class InfraTimelineChart(BaseChart):
    """Paneles de métricas de infraestructura a lo largo del tiempo."""

    def render(
        self,
        total_span: float,
        metrics: dict[str, dict[str, Any]],
        label: str,
        outdir: str,
        file_id: str = "infra-timeline",
    ) -> str | None:
        """Genera paneles de infraestructura. Retorna nombre del archivo o None."""
        if not metrics:
            return None

        n_panels = len(metrics)
        fig, axes = plt.subplots(
            n_panels, 1,
            figsize=(9.2, 2.4 * n_panels + 1.0),
            sharex=True,
            gridspec_kw=self._make_gridspec_kw(hspace=0.24, top=0.93, bottom=0.08),
        )

        if n_panels == 1:
            axes = [axes]

        colors = [self.p.s1, self.p.s2, self.p.s3, self.p.s4]

        for i, (name, data) in enumerate(metrics.items()):
            ax = axes[i]
            col = colors[i % len(colors)]
            self._panel_metric(ax, data, name, col)

        axes[-1].xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: self.fmt_time_axis(v, total_span))
        )
        axes[-1].set_xlabel("Tiempo transcurrido")
        axes[-1].set_xlim(0, total_span)
        fig.suptitle(
            f"{label}  \u00b7  m\u00e9tricas de infraestructura",
            x=0.09, ha="left", fontsize=self.theme.suptitle_size,
            fontweight="bold", y=0.995,
        )
        return self.save(fig, outdir, file_id)

    def _panel_metric(
        self, ax: Any, data: dict[str, Any], name: str, color: str,
    ) -> None:
        if "t" in data and "vals" in data and len(data["t"]) > 0:
            ax.fill_between(data["t"], data["vals"], alpha=0.12, color=color, zorder=1)
            ax.plot(data["t"], data["vals"], color=color, lw=1.8, zorder=2)

            if "threshold" in data:
                ax.axhline(
                    data["threshold"], color=self.p.crit,
                    ls=":", lw=1.2, alpha=0.7, zorder=3,
                )
                ax.text(
                    data["t"][-1], data["threshold"],
                    f" umbral: {data['threshold']:.0f}%",
                    va="bottom", ha="right", fontsize=8.5, color=self.p.crit,
                )

        ax.set_title(name, loc="left")
        ax.set_ylabel(data.get("unit", "%"))
        ax.set_ylim(bottom=0)
        if data.get("ymax"):
            ax.set_ylim(top=data["ymax"])
        self.style_ax(ax)
