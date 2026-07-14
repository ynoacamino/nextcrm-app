from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any

from k6_charts.config import Theme
from k6_charts.parsers import discover, parse_summary, parse_csv
from k6_charts.charts.timeline import TimelineChart
from k6_charts.charts.cdf import CdfChart
from k6_charts.charts.bar import HorizontalBarChart, GroupedBarChart
from k6_charts.charts.stress import StressDegradationChart
from k6_charts.charts.spike import SpikeRecoveryChart
from k6_charts.charts.comparison import CrossComparisonChart
from k6_charts.charts.dashboard_grid import DashboardGridChart
from k6_charts.charts.comparison_grid import ComparisonGridChart
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
        "--verbose", "-v", action="store_true", help="Salida detallada",
    )
    return ap


def _merge_summary_and_timeseries(
    summary: dict[str, Any],
    ts: dict[str, Any] | None,
) -> dict[str, Any]:
    if ts and ts.get("raw"):
        if summary.get("dur_p99") is None:
            summary["dur_p99"] = ts["raw"]["p99"]
        if summary.get("dur_max") is None:
            summary["dur_max"] = ts["raw"]["max"]
    return summary


def _pf(result: dict[str, Any]) -> tuple[str, bool | None]:
    th = result["s"].get("thresholds") or []
    if not th:
        return ("\u2014", None)
    bad = sum(1 for x in th if not x[2])
    return (f"\u2717 {bad}/{len(th)}", False) if bad else (f"\u2713 {len(th)}/{len(th)}", True)


def main(argv: list[str] | None = None) -> None:
    ap = _build_argparser()
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    base = args.outdir
    dirs = {
        "timeline": os.path.join(base, "timeline"),
        "cdf": os.path.join(base, "cdf"),
        "dashboard": os.path.join(base, "dashboard"),
        "stress": os.path.join(base, "stress"),
        "spike": os.path.join(base, "spike"),
        "comparison": os.path.join(base, "comparison"),
        "data": os.path.join(base, "data"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    theme = Theme()
    theme.apply_rcparams()

    sets = discover(args.indir)
    if not sets:
        log.error("No se encontraron archivos k6 en %s", args.indir)
        sys.exit(1)

    log.info("Datasets: %s", ", ".join(str(d["id"]) for d in sets))

    results: list[dict[str, Any]] = []
    for d in sets:
        log.info("\u00b7 %s: resumen...", d["id"])
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
    stress = StressDegradationChart(theme)
    spike = SpikeRecoveryChart(theme)
    comparison = CrossComparisonChart(theme)
    dashboard_grid = DashboardGridChart(theme)
    comparison_grid = ComparisonGridChart(theme)

    written: list[str] = []

    def w(name: str | None) -> None:
        if name is not None:
            written.append(name)

    for t in results:
        if t["ts"] is not None:
            w(timeline.render(t["ts"], t["label"], dirs["timeline"], f"timeline-{t['id']}"))
            if t["ts"]["all_dur"].size:
                w(cdf.render(t["ts"]["all_dur"], t["label"], dirs["cdf"], f"cdf-{t['id']}"))
            if t.get("kind") == "PRSTRESS":
                w(stress.render(t["ts"], t["label"], dirs["stress"], f"stress-degradation-{t['id']}"))
            if t.get("kind") == "PRSPIKE":
                w(spike.render(t["ts"], t["label"], dirs["spike"], f"spike-recovery-{t['id']}"))
            w(dashboard_grid.render(t["ts"], t["label"], dirs["dashboard"], f"dashboard-{t['id']}"))

    if len(results) >= 2:
        w(comparison.render(results, dirs["comparison"], "cross-comparison"))
        w(comparison_grid.render(results, dirs["comparison"], "comparison-grid"))

    if len(results) > 1:
        wd = [t for t in results if t["s"].get("dur_p95") is not None]
        w(hbar.render(
            "Comparativa \u00b7 latencia p95",
            "http_req_duration p95 \u2014 menor es mejor",
            sorted([(t["label"], t["s"]["dur_p95"]) for t in wd], key=lambda x: x[1]),
            formatter=fmt_ms, color=theme.palette.s1,
            outdir=dirs["comparison"], file_id="cmp-p95",
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
            outdir=dirs["comparison"], file_id="cmp-rps",
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
            outdir=dirs["comparison"], file_id="cmp-err",
        ))
        w(grouped.render(wd, dirs["comparison"], "cmp-latencia"))

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

    th_rows: list[list[str]] = []
    for t in results:
        for name, expr, ok in (t["s"].get("thresholds") or []):
            th_rows.append([t["label"], name, expr, "\u2713 OK" if ok else "\u2717 FALLA"])

    ck_rows: list[list[str]] = []
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

    def _write_csv(path: str, header: list[str], rows: list[list[str]]) -> None:
        with open(path, "w") as fh:
            fh.write(",".join(header) + "\n")
            for row in rows:
                fh.write(",".join(f'"{str(v)}"' for v in row) + "\n")

    data_dir = dirs["data"]
    _write_csv(os.path.join(data_dir, "tabla-resumen.csv"), headers, trows)
    if th_rows:
        _write_csv(
            os.path.join(data_dir, "tabla-umbrales.csv"),
            ["Prueba", "M\u00e9trica", "Condici\u00f3n", "Resultado"],
            th_rows,
        )
    if ck_rows:
        _write_csv(
            os.path.join(data_dir, "tabla-checks.csv"),
            ["Prueba", "Check", "Pasa", "Falla", "% \u00e9xito"],
            ck_rows,
        )

    with open(os.path.join(data_dir, "resumen.json"), "w") as fh:
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

    log.info("\u2714 Listo. %d figuras (SVG vectorial) en: %s", len(written), base)
    log.info("  timeline/  cdf/  dashboard/  stress/  spike/  comparison/  data/")
    for name in written:
        log.info("  \u00b7 %s.svg", name)
    log.info("  \u00b7 data/tabla-resumen.csv \u00b7 data/tabla-umbrales.csv \u00b7 data/tabla-checks.csv \u00b7 data/resumen.json")
