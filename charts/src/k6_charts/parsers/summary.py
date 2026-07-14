"""Parser para el resumen JSON de k6 (handleSummary)."""

from __future__ import annotations

import json
from typing import Any


def _metric_value(metric: dict[str, Any] | None, stat: str) -> float | None:
    """Extrae un valor de una métrica k6 (soporta formato rich y aplanado)."""
    if not metric:
        return None
    if isinstance(metric.get("values"), dict) and stat in metric["values"]:
        v = metric["values"][stat]
    else:
        v = metric.get(stat)
    return v if isinstance(v, (int, float)) else None


def _flatten_checks(root: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Extrae recursivamente todos los checks del árbol de grupos k6."""
    rows: list[dict[str, Any]] = []

    def walk(group: dict[str, Any] | None) -> None:
        if not group:
            return
        checks = group.get("checks")
        if isinstance(checks, list):
            rows.extend(checks)
        elif isinstance(checks, dict):
            rows.extend(
                v for v in checks.values() if isinstance(v, dict) and v.get("name")
            )
        subgroups = group.get("groups")
        if isinstance(subgroups, list):
            for sg in subgroups:
                walk(sg)
        elif isinstance(subgroups, dict):
            for sg in subgroups.values():
                walk(sg)

    walk(root)
    return rows


def parse_summary(path: str | None) -> dict[str, Any] | None:
    """Parsea el JSON de resumen de k6 y retorna un diccionario normalizado.

    Returns:
        Diccionario con métricas normalizadas, o None si falla el parsing.
    """
    if not path:
        return None

    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None

    metrics = data.get("metrics", {})
    g = lambda name, stat: _metric_value(metrics.get(name), stat)

    check_rows = _flatten_checks(data.get("root_group"))
    passes = sum(c.get("passes", 0) for c in check_rows)
    fails = sum(c.get("fails", 0) for c in check_rows)

    thresholds: list[tuple[str, str, bool]] = []
    for name, met in metrics.items():
        for expr, result in (met.get("thresholds") or {}).items():
            ok = result if isinstance(result, bool) else bool(result.get("ok"))
            thresholds.append((name, expr, ok))

    failed = g("http_req_failed", "rate")
    if failed is None:
        failed = _metric_value(metrics.get("http_req_failed"), "value") or 0

    chk = g("checks", "rate")
    if chk is None:
        chk = _metric_value(metrics.get("checks"), "value")
    if chk is None and (passes + fails):
        chk = passes / (passes + fails)

    return {
        "durationMs": (data.get("state") or {}).get("testRunDurationMs"),
        "reqs": g("http_reqs", "count"),
        "rps": g("http_reqs", "rate"),
        "dur_avg": g("http_req_duration", "avg"),
        "dur_med": g("http_req_duration", "med"),
        "dur_min": g("http_req_duration", "min"),
        "dur_p90": g("http_req_duration", "p(90)"),
        "dur_p95": g("http_req_duration", "p(95)"),
        "dur_p99": g("http_req_duration", "p(99)"),
        "dur_max": g("http_req_duration", "max"),
        "ttfb_med": g("crm_ttfb", "med") or g("http_req_waiting", "med"),
        "ttfb_p95": g("crm_ttfb", "p(95)") or g("http_req_waiting", "p(95)"),
        "vus_max": g("vus_max", "value") or g("vus_max", "max"),
        "err_rate": failed * 100,
        "checks_rate": (chk * 100 if chk is not None else None),
        "checks_passes": passes,
        "checks_fails": fails,
        "data_recv": g("data_received", "count"),
        "data_sent": g("data_sent", "count"),
        "thresholds": thresholds,
        "checks": check_rows,
    }
