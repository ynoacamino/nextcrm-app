"""Parser para CSV de métricas de infraestructura (Prometheus/Grafana)."""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from typing import Any

import numpy as np


def parse_infra_csv(path: str | None) -> dict[str, dict[str, Any]] | None:
    """Parsea un CSV exportado de Prometheus/Grafana: timestamp,metric_name,value.

    Returns:
        Diccionario {nombre_metrica: {"t": np.array, "vals": np.array}}, o None.
    """
    if not path or not os.path.isfile(path):
        return None

    series: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"t": [], "vals": []}
    )
    t0: float | None = None

    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)

        i_t = header.index("timestamp") if "timestamp" in header else 0
        i_m = header.index("metric") if "metric" in header else 1
        i_v = header.index("value") if "value" in header else 2

        for c in reader:
            try:
                ts = float(c[i_t])
                val = float(c[i_v])
            except (ValueError, IndexError):
                continue

            if t0 is None:
                t0 = ts

            name = c[i_m]
            series[name]["t"].append(ts - t0)
            series[name]["vals"].append(val)

    if not series:
        return None

    return {
        name: {"t": np.array(data["t"]), "vals": np.array(data["vals"])}
        for name, data in series.items()
    }
