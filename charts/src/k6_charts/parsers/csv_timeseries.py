from __future__ import annotations

import csv
import math
from collections import defaultdict
from typing import Any

import numpy as np

csv.field_size_limit(10**7)

_NEEDED = {"http_req_duration", "http_reqs", "http_req_failed", "vus", "iterations"}


def _parse_extra_tags(tags_str: str) -> dict[str, str]:
    if not tags_str:
        return {}
    pairs: dict[str, str] = {}
    for part in tags_str.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            pairs[k.strip()] = v.strip()
    return pairs


def _extract_entity(tags: dict[str, str]) -> tuple[str, str]:
    return tags.get("entity", ""), tags.get("op", "")


def parse_csv(path: str) -> dict[str, Any] | None:
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)

        i_n = header.index("metric_name")
        i_t = header.index("timestamp")
        i_v = header.index("metric_value")
        i_g = header.index("group") if "group" in header else -1
        i_et = header.index("extra_tags") if "extra_tags" in header else -1

        rows: list[tuple[int, str, float]] = []
        t0: int | None = None
        tmax = 0
        all_dur: list[float] = []
        per_action_dur: dict[str, list[float]] = defaultdict(list)
        per_action_err: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])

        for c in reader:
            if len(c) <= i_v:
                continue

            name = c[i_n]
            if name not in _NEEDED:
                continue

            if i_g >= 0:
                grp = c[i_g]
                if grp.startswith("::setup") or grp.startswith("::teardown"):
                    continue

            try:
                ts = int(float(c[i_t]))
                val = float(c[i_v])
            except ValueError:
                continue

            if t0 is None or ts < t0:
                t0 = ts
            if ts > tmax:
                tmax = ts

            rows.append((ts, name, val))

            if name == "http_req_duration":
                all_dur.append(val)
                if 0 <= i_et < len(c) and c[i_et]:
                    tags = _parse_extra_tags(c[i_et])
                    entity, op = _extract_entity(tags)
                    if entity:
                        per_action_dur[f"{entity}:{op}"].append(val)

            elif name == "http_req_failed":
                if 0 <= i_et < len(c) and c[i_et]:
                    tags = _parse_extra_tags(c[i_et])
                    entity, op = _extract_entity(tags)
                    if entity:
                        per_action_err[f"{entity}:{op}"][0] += val
                        per_action_err[f"{entity}:{op}"][1] += 1

    if t0 is None:
        return None

    span = max(1, tmax - t0 + 1)
    bin_size = max(1, math.ceil(span / 380))
    n_bins = math.ceil(span / bin_size)

    dur_bins: list[list[float]] = [[] for _ in range(n_bins)]
    reqs = np.zeros(n_bins)
    fail_sum = np.zeros(n_bins)
    fail_cnt = np.zeros(n_bins)
    vus = np.zeros(n_bins)

    for ts, name, val in rows:
        b = min(n_bins - 1, (ts - t0) // bin_size)
        if name == "http_req_duration":
            if len(dur_bins[b]) < 8000:
                dur_bins[b].append(val)
        elif name == "http_reqs":
            reqs[b] += val
        elif name == "http_req_failed":
            fail_sum[b] += val
            fail_cnt[b] += 1
        elif name == "vus":
            if val > vus[b]:
                vus[b] = val

    t = np.arange(n_bins) * bin_size
    p95 = np.array([np.percentile(d, 95) if d else np.nan for d in dur_bins])
    med = np.array([np.percentile(d, 50) if d else np.nan for d in dur_bins])
    avg = np.array([np.mean(d) if d else np.nan for d in dur_bins])
    rps = reqs / bin_size
    err = np.where(fail_cnt > 0, fail_sum / np.maximum(fail_cnt, 1) * 100, 0.0)
    ad = np.array(all_dur)

    vu_bins: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"dur": [], "reqs": 0.0, "err_sum": 0.0, "err_cnt": 0.0}
    )
    for ts, name, val in rows:
        b = min(n_bins - 1, (ts - t0) // bin_size)
        vu_val = int(round(vus[b]))
        if vu_val <= 0:
            continue
        if name == "http_req_duration":
            if len(vu_bins[vu_val]["dur"]) < 8000:
                vu_bins[vu_val]["dur"].append(val)
        elif name == "http_reqs":
            vu_bins[vu_val]["reqs"] += val
        elif name == "http_req_failed":
            vu_bins[vu_val]["err_sum"] += val
            vu_bins[vu_val]["err_cnt"] += 1

    vu_keys = sorted(vu_bins.keys())
    vu_corr: dict[str, Any] | None = None
    if vu_keys:
        vu_corr = {
            "vu": np.array(vu_keys),
            "p95": np.array([
                np.percentile(vu_bins[v]["dur"], 95) if vu_bins[v]["dur"] else np.nan
                for v in vu_keys
            ]),
            "med": np.array([
                np.percentile(vu_bins[v]["dur"], 50) if vu_bins[v]["dur"] else np.nan
                for v in vu_keys
            ]),
            "rps": np.array([
                vu_bins[v]["reqs"] / max(1, span) for v in vu_keys
            ]),
            "err": np.array([
                vu_bins[v]["err_sum"] / max(vu_bins[v]["err_cnt"], 1) * 100
                for v in vu_keys
            ]),
        }

    raw = None
    if ad.size:
        raw = {
            "p50": float(np.percentile(ad, 50)),
            "p90": float(np.percentile(ad, 90)),
            "p95": float(np.percentile(ad, 95)),
            "p99": float(np.percentile(ad, 99)),
            "max": float(ad.max()),
        }

    return {
        "span": span,
        "bs": bin_size,
        "t": t,
        "p95": p95,
        "med": med,
        "avg": avg,
        "rps": rps,
        "err": err,
        "vus": vus,
        "all_dur": ad,
        "raw": raw,
        "per_action_dur": dict(per_action_dur),
        "per_action_err": dict(per_action_err),
        "vu_corr": vu_corr,
    }
