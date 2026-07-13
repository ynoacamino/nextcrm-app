"""CLI — orquestación principal del generador de reportes k6."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any

from k6_charts.config import Theme
from k6_charts.parsers import discover, parse_summary, parse_csv, parse_infra_csv
from k6_charts.charts.timeline import TimelineChart
from k6_charts.charts.cdf import CdfChart
from k6_charts.charts.bar import HorizontalBarChart, GroupedBarChart, PerActionChart
from k6_charts.charts.stress import StressDegradationChart
from k6_charts.charts.spike import SpikeRecoveryChart
from k6_charts.charts.infra import InfraTimelineChart
from k6_charts.charts.comparison import CrossComparisonChart
from k6_charts.tables import render_table
from k6_charts.formatters import fmt_ms, fmt_int, fmt_dur

log = logging.getLogger("k6_charts")


def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="k6-charts",
        description="Genera gráficas y tablas de calidad de publicación desde k6.",
    )
    ap.add_argument("--in", dest="indir", default=".", help="Directorio con archivos k6")
    ap.add_argument("--out", dest="outdir", default="./k6-report-py", help="Directorio de salida")
    ap.add_argument(
        "--infra", dest="infra_csv", default=None,
        help="CSV de métricas de infra (Prometheus/Grafana): timestamp,metric_name,value",
    )
    ap.add_argument(
        "--verbose", "-v", action="store_true", help="Salida detallada",
    )
    return ap


def _merge_summary_and_timeseries(
    summary: dict[str, Any],
    ts: dict[str, Any] | None,
) -> dict[str, Any]:
    """Combina el resumen JSON con las métricas del CSV."""
    if ts and ts.get("raw"):
        if summary.get("dur_p99") is None:
            summary["dur_p99"] = ts["raw"]["p99"]
        if summary.get("dur_max") is None:
            summary["dur_max"] = ts["raw"]["max"]
    return summary


def _pf(result: dict[str, Any]) -> tuple[str, bool | None]:
    """Formatea el estado de umbrales de una prueba."""
    th = result["s"].get("thresholds") or []
    if not th:
        return ("\u2014", None)
    bad = sum(1 for x in th if not x[2])
    return (f"\u2717 {bad}/{len(th)}", False) if bad else (f"\u2713 {len(th)}/{len(th)}", True)


def _resumen_color_factory(
    metrics_defs: list[tuple[str, Any]],
    palette: Any,
) -> Callable[[int, int, str], str | None]:
    """Crea la función de color para la tabla resumen."""
    def resumen_color(r: int, c: int, val: str) -> str | None:
        if c == 0:
            return palette.ink
        name = metrics_defs[r][0]
        if name == "Umbrales":
            if str(val).startswith("\u2717"):
                return palette.crit
            if str(val).startswith("\u2713"):
                return palette.good
            return palette.ink2
        if name == "Tasa de error":
            try:
                return palette.crit if float(str(val).replace("%", "")) > 1 else palette.good
            except ValueError:
                return palette.ink2
        return palette.ink2
    return resumen_color


def main(argv: list[str] | None = None) -> None:
    """Entry point principal."""
    ap = _build_argparser()
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    os.makedirs(args.outdir, exist_ok=True)
    theme = Theme()
    theme.apply_rcparams()

    sets = discover(args.indir)
    if not sets:
        log.error("No se encontraron archivos k6 en %s", args.indir)
        sys.exit(1)

    log.info("Datasets: %s", ", ".join(str(d["id"]) for d in sets))

    results: list[dict[str, Any]] = []
    for d in sets:
        log.info("· %s: resumen...", d["id"])
        s = parse_summary(str(d["summary"])) if d.get("summary") else {}
        log.info("  csv...")
        ts = parse_csv(str(d["csv"])) if d.get("csv") else None
        if ts:
            log.info("  (%d pts)", len(ts["t"]))
        else:
            log.info("  (sin csv)")

        if s and ts:
            s = _merge_summary_and_timeseries(s, ts)

        results.append(dict(d, s=s or {}, ts=ts))

    timeline = TimelineChart(theme)
    cdf = CdfChart(theme)
    hbar = HorizontalBarChart(theme)
    grouped = GroupedBarChart(theme)
    per_action = PerActionChart(theme)
    stress = StressDegradationChart(theme)
    spike = SpikeRecoveryChart(theme)
    infra_chart = InfraTimelineChart(theme)
    comparison = CrossComparisonChart(theme)

    written: list[str] = []

    def w(name: str | None) -> None:
        if name is not None:
            written.append(name)

    for t in results:
        if t["ts"] is not None:
            w(timeline.render(t["ts"], t["label"], args.outdir, f"timeline-{t['id']}"))
            if t["ts"]["all_dur"].size:
                w(cdf.render(t["ts"]["all_dur"], t["label"], args.outdir, f"cdf-{t['id']}"))
            if t.get("kind") == "PRSTRESS":
                w(stress.render(t["ts"], t["label"], args.outdir, f"stress-degradation-{t['id']}"))
            if t.get("kind") == "PRSPIKE":
                w(spike.render(t["ts"], t["label"], args.outdir, f"spike-recovery-{t['id']}"))
            if t["ts"].get("per_action_dur"):
                w(per_action.render(t["ts"], t["label"], args.outdir, f"per-action-{t['id']}"))

    if args.infra_csv:
        infra = parse_infra_csv(args.infra_csv)
        if infra:
            MAPPED = {
                "cpu": {"unit": "%", "threshold": 70.0, "ymax": 100.0},
                "memory": {"unit": "%", "threshold": 80.0, "ymax": 100.0},
                "db_connections": {"unit": "conexiones", "threshold": 180.0},
            }
            mapped: dict[str, dict[str, Any]] = {}
            for name, data in infra.items():
                key = name.lower()
                for pattern, meta in MAPPED.items():
                    if pattern in key:
                        mapped[f"{meta['unit'].upper()} \u2014 {name}"] = {**data, **meta}
                        break
                else:
                    mapped[name] = {**data, "unit": ""}
            if mapped:
                label = "SOAK" if any(t.get("kind") == "PRSOAK" for t in results) else "Infraestructura"
                w(infra_chart.render(
                    max(d["t"].max() for d in mapped.values()),
                    mapped, label, args.outdir, "infra-timeline",
                ))

    if len(results) >= 2:
        w(comparison.render(results, args.outdir, "cross-comparison"))

    if len(results) > 1:
        wd = [t for t in results if t["s"].get("dur_p95") is not None]
        w(hbar.render(
            "Comparativa \u00b7 latencia p95",
            "http_req_duration p95 \u2014 menor es mejor",
            sorted([(t["label"], t["s"]["dur_p95"]) for t in wd], key=lambda x: x[1]),
            formatter=fmt_ms, color=theme.palette.s1,
            outdir=args.outdir, file_id="cmp-p95",
        ))
        w(hbar.render(
            "Comparativa \u00b7 throughput (RPS)",
            "peticiones por segundo \u2014 mayor es mejor",
            sorted(
                [(t["label"], t["s"]["rps"]) for t in results if t["s"].get("rps") is not None],
                key=lambda x: -x[1],
            ),
            formatter=lambda v: f"{v:.2f}/s",
            color=theme.palette.s2,
            outdir=args.outdir, file_id="cmp-rps",
        ))
        w(hbar.render(
            "Comparativa \u00b7 tasa de error",
            "% de peticiones fallidas \u2014 menor es mejor",
            sorted(
                [(t["label"], t["s"]["err_rate"]) for t in results if t["s"].get("err_rate") is not None],
                key=lambda x: -x[1],
            ),
            formatter=lambda v: f"{v:.2f}%",
            color=lambda i: (
                theme.palette.good if i[1] <= 0.5
                else theme.palette.warn if i[1] <= 2
                else theme.palette.crit
            ),
            outdir=args.outdir, file_id="cmp-err",
        ))
        w(grouped.render(wd, args.outdir, "cmp-latencia"))

    METRICS = [
        ("Tipo", lambda s, t: t.get("kind") or "\u2014"),
        ("Duraci\u00f3n", lambda s, t: fmt_dur(s.get("durationMs") or (t["ts"]["span"] * 1000 if t["ts"] else None))),
        ("VUs m\u00e1x", lambda s, t: fmt_int(s.get("vus_max"))),
        ("Peticiones", lambda s, t: fmt_int(s.get("reqs"))),
        ("Throughput (req/s)", lambda s, t: "\u2014" if s.get("rps") is None else f"{s['rps']:.2f}"),
        ("Latencia mediana", lambda s, t: fmt_ms(s.get("dur_med"))),
        ("Latencia p90", lambda s, t: fmt_ms(s.get("dur_p90"))),
        ("Latencia p95", lambda s, t: fmt_ms(s.get("dur_p95"))),
        ("Latencia p99", lambda s, t: fmt_ms(s.get("dur_p99"))),
        ("Latencia m\u00e1x", lambda s, t: fmt_ms(s.get("dur_max"))),
        ("TTFB p95", lambda s, t: fmt_ms(s.get("ttfb_p95"))),
        ("Tasa de error", lambda s, t: "\u2014" if s.get("err_rate") is None else f"{s['err_rate']:.2f}%"),
        ("Checks OK", lambda s, t: "\u2014" if s.get("checks_rate") is None else f"{s['checks_rate']:.1f}%"),
        ("Umbrales", lambda s, t: _pf(t)[0]),
    ]
    headers = ["M\u00e9trica"] + [t["label"] for t in results]
    trows = [[name] + [fn(t["s"], t) for t in results] for name, fn in METRICS]
    aligns = ["left"] + ["right"] * len(results)

    w(render_table(
        "Resumen de pruebas de rendimiento (k6)", headers, trows,
        args.outdir, "tabla-resumen", aligns,
        _resumen_color_factory(METRICS, theme.palette),
        col_scale=[1.15] + [1.0] * len(results),
        theme=theme,
    ))

    th_rows: list[list[str]] = []
    th_ok: list[bool] = []
    for t in results:
        for name, expr, ok in (t["s"].get("thresholds") or []):
            th_rows.append([t["label"], name, expr, "\u2713 OK" if ok else "\u2717 FALLA"])
            th_ok.append(ok)
    if th_rows:
        w(render_table(
            "Umbrales (thresholds)",
            ["Prueba", "M\u00e9trica", "Condici\u00f3n", "Resultado"],
            th_rows, args.outdir, "tabla-umbrales",
            ["left", "left", "left", "left"],
            lambda r, c, v: (theme.palette.good if th_ok[r] else theme.palette.crit) if c == 3 else None,
            theme=theme,
        ))

    ck_rows: list[list[str]] = []
    ck_fail_cnt: list[int] = []
    for t in results:
        agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for c in (t["s"].get("checks") or []):
            agg[c["name"]][0] += c.get("passes", 0)
            agg[c["name"]][1] += c.get("fails", 0)
        for name, (p, f_val) in agg.items():
            tot = p + f_val
            ck_rows.append([
                t["label"], name, fmt_int(p), fmt_int(f_val),
                f"{p / tot * 100:.1f}%" if tot else "\u2014",
            ])
            ck_fail_cnt.append(f_val)
    if ck_rows:
        w(render_table(
            "Checks (validaciones)",
            ["Prueba", "Check", "Pasa", "Falla", "% \u00e9xito"],
            ck_rows, args.outdir, "tabla-checks",
            ["left", "left", "right", "right", "right"],
            lambda r, c, v: (
                theme.palette.crit if ck_fail_cnt[r] > 0 else theme.palette.ink2
            ) if c == 3 else None,
            theme=theme,
        ))

    with open(os.path.join(args.outdir, "tabla-resumen.csv"), "w") as fh:
        fh.write(",".join(headers) + "\n")
        for row in trows:
            fh.write(",".join(f'"{str(v)}"' for v in row) + "\n")

    with open(os.path.join(args.outdir, "resumen.json"), "w") as fh:
        json.dump(
            [
                dict(
                    id=t["id"], kind=t.get("kind"),
                    **{k: v for k, v in t["s"].items() if k != "checks"},
                )
                for t in results
            ],
            fh, ensure_ascii=False, indent=2, default=str,
        )

    log.info("\u2714 Listo. %d figuras (PNG 300dpi + PDF) en: %s", len(written), args.outdir)
    for name in written:
        log.info("  \u00b7 %s.png / %s.pdf", name, name)
    log.info("  \u00b7 tabla-resumen.csv \u00b7 resumen.json")
