#!/usr/bin/env python3
"""Genera tablas y gráficos de las pruebas de rendimiento (k6) desde los JSON
de resumen (handleSummary) y, opcionalmente, series temporales de k6 --out json.

Reutilizable: apunta -i a la carpeta de resultados y -o a la de salida. Pensado
para correr igual en local o en un VPS tras ejecutar la suite k6.

Uso:
    python3 tests/performance/scripts/perf-charts.py \
        -i tests/performance/reports \
        -o tests/performance/docs/img

Salida:
    <out>/test_<caso>.png      un gráfico por test (percentiles p50/p90/p95/max)
    <out>/serie_<caso>.png     latencia en el tiempo (si hay <caso>.ndjson)
    <out>/comparativa_p95.png  comparativa de p95 entre tests
    <out>/comparativa_rps.png  comparativa de throughput (RPS)
    <out>/comparativa_ttfb.png comparativa de TTFB p95
    <out>/tabla_metricas.md    tabla Markdown
    <out>/tabla_metricas.csv   tabla CSV

Requisitos: matplotlib  (pip install matplotlib)

Para obtener las series temporales (grafico latencia-en-el-tiempo por test),
ejecutar cada escenario de k6 añadiendo:  --out json=<caso>.ndjson
"""
import argparse
import csv
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- helpers

def val(metrics, name, key):
    try:
        v = metrics.get(name, {}).get("values", {}).get(key)
        return v if isinstance(v, (int, float)) else None
    except Exception:
        return None

def fmt(ms):
    if ms is None:
        return "—"
    return f"{ms/1000:.2f} s" if ms >= 1000 else f"{ms:.0f} ms"

def load_summaries(indir):
    rows = []
    for path in sorted(glob.glob(os.path.join(indir, "*.json"))):
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[warn] no se pudo leer {path}: {e}", file=sys.stderr)
            continue
        m = data.get("metrics", {})
        failed = val(m, "http_req_failed", "rate")
        if failed is None:
            failed = m.get("http_req_failed", {}).get("values", {}).get("value", 0)
        rows.append({
            "name": name,
            "p50": val(m, "http_req_duration", "med"),
            "p90": val(m, "http_req_duration", "p(90)"),
            "p95": val(m, "http_req_duration", "p(95)"),
            "p99": val(m, "http_req_duration", "p(99)"),
            "max": val(m, "http_req_duration", "max"),
            "avg": val(m, "http_req_duration", "avg"),
            "ttfb95": val(m, "crm_ttfb", "p(95)") or val(m, "http_req_waiting", "p(95)"),
            "rps": val(m, "http_reqs", "rate") or 0,
            "reqs": val(m, "http_reqs", "count"),
            "err": (failed or 0) * 100,
            "checks": (val(m, "checks", "rate") or 0) * 100,
        })
    return rows

def color_for(p95):
    if p95 is None:
        return "#9ca3af"
    if p95 < 500:
        return "#22c55e"
    if p95 < 1500:
        return "#f59e0b"
    return "#ef4444"

# ---------------------------------------------------------------- charts

def chart_per_test(row, outdir):
    labels = ["p50", "p90", "p95", "max"]
    vals = [(row[k] or 0) / 1000 for k in ["p50", "p90", "p95", "max"]]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    bars = ax.bar(labels, vals, color=color_for(row["p95"]))
    ax.set_ylabel("segundos")
    ax.set_title(row["name"], fontsize=12, fontweight="bold")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}s",
                ha="center", va="bottom", fontsize=9)
    sub = f"RPS {row['rps']:.2f} · reqs {row['reqs']} · error {row['err']:.2f}% · checks {row['checks']:.0f}% · TTFB p95 {fmt(row['ttfb95'])}"
    ax.text(0.5, -0.22, sub, transform=ax.transAxes, ha="center", fontsize=8, color="#555")
    fig.tight_layout()
    path = os.path.join(outdir, f"test_{row['name']}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path

def chart_compare(rows, outdir, key, title, fname, unit="s"):
    rows_s = sorted(rows, key=lambda r: (r[key] or 0))
    names = [r["name"] for r in rows_s]
    if unit == "s":
        vals = [(r[key] or 0) / 1000 for r in rows_s]
        cols = [color_for(r["p95"]) for r in rows_s] if key == "p95" else ["#3b82f6"] * len(rows_s)
        vlabel = lambda v: f"{v:.2f}s"
    else:
        vals = [r[key] or 0 for r in rows_s]
        cols = ["#3b82f6"] * len(rows_s)
        vlabel = lambda v: f"{v:.2f}"
    fig, ax = plt.subplots(figsize=(8.5, 0.5 * len(rows_s) + 1.6))
    bars = ax.barh(names, vals, color=cols)
    ax.set_xlabel(title)
    ax.set_title(title, fontsize=12, fontweight="bold")
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2, " " + vlabel(v), va="center", fontsize=9)
    fig.tight_layout()
    path = os.path.join(outdir, fname)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path

def chart_timeseries(name, ndjson, outdir):
    """Latencia (http_req_duration) en el tiempo desde un stream k6 --out json."""
    ts, dur = [], []
    t0 = None
    try:
        with open(ndjson) as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if o.get("type") == "Point" and o.get("metric") == "http_req_duration":
                    d = o["data"]
                    t = d["time"]
                    if t0 is None:
                        t0 = t
                    ts.append(len(ts))  # índice; el eje real requiere parseo ISO
                    dur.append(d["value"])
    except Exception as e:
        print(f"[warn] serie {ndjson}: {e}", file=sys.stderr)
        return None
    if not dur:
        return None
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    ax.plot(range(len(dur)), [x / 1000 for x in dur], lw=0.6, color="#6366f1")
    ax.set_title(f"{name} · latencia por request", fontsize=12, fontweight="bold")
    ax.set_xlabel("request #")
    ax.set_ylabel("segundos")
    fig.tight_layout()
    path = os.path.join(outdir, f"serie_{name}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path

# ---------------------------------------------------------------- tables

def write_tables(rows, outdir):
    cols = ["name", "p50", "p95", "p99", "max", "ttfb95", "rps", "reqs", "err", "checks"]
    head = ["Escenario", "p50", "p95", "p99", "máx", "TTFB p95", "RPS", "reqs", "error%", "checks%"]
    md = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    for r in rows:
        md.append("| " + " | ".join([
            r["name"], fmt(r["p50"]), fmt(r["p95"]), fmt(r["p99"]), fmt(r["max"]),
            fmt(r["ttfb95"]), f"{r['rps']:.2f}", str(r["reqs"]),
            f"{r['err']:.2f}", f"{r['checks']:.0f}",
        ]) + " |")
    with open(os.path.join(outdir, "tabla_metricas.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    with open(os.path.join(outdir, "tabla_metricas.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        for r in rows:
            w.writerow([r["name"], r["p50"], r["p95"], r["p99"], r["max"],
                        r["ttfb95"], round(r["rps"], 3), r["reqs"],
                        round(r["err"], 3), round(r["checks"], 1)])

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Gráficos y tablas de pruebas de rendimiento k6")
    ap.add_argument("-i", "--input", default="tests/performance/reports",
                    help="carpeta con los *.json de resumen de k6")
    ap.add_argument("-o", "--output", default="tests/performance/docs/img",
                    help="carpeta de salida para PNG/tablas")
    args = ap.parse_args()

    os.makedirs(args.output, exist_ok=True)
    rows = load_summaries(args.input)
    if not rows:
        print(f"[error] no hay *.json en {args.input}", file=sys.stderr)
        sys.exit(1)

    per = [chart_per_test(r, args.output) for r in rows]
    for r in rows:
        nd = os.path.join(args.input, r["name"] + ".ndjson")
        if os.path.exists(nd):
            chart_timeseries(r["name"], nd, args.output)
    chart_compare(rows, args.output, "p95", "Comparativa p95 (s)", "comparativa_p95.png", "s")
    chart_compare(rows, args.output, "rps", "Comparativa throughput (RPS)", "comparativa_rps.png", "n")
    chart_compare(rows, args.output, "ttfb95", "Comparativa TTFB p95 (s)", "comparativa_ttfb.png", "s")
    write_tables(rows, args.output)

    print(f"OK: {len(rows)} tests · {len(per)} gráficos por test + 3 comparativas + tabla")
    for r in rows:
        print(f"  {r['name']:<28} p95={fmt(r['p95']):>9}  rps={r['rps']:.2f}  err={r['err']:.2f}%")


if __name__ == "__main__":
    main()
