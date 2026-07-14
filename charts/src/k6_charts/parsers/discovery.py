"""Descubrimiento de datasets k6 en un directorio."""

from __future__ import annotations

import os
import re


def normalize_name(filename: str) -> str:
    """Normaliza el nombre de un archivo a un identificador de dataset limpio.

    Patrones soportados:
      - entity.load-raw-metrics.csv
      - entity.stress.json
      - PRSTRESS-entity.json
    """
    basename = os.path.basename(filename)

    type_match = re.search(
        r"\.(load|stress|spike|soak|smoke)[-_]?(?:raw[-_]?metrics)?\.csv$",
        basename,
        flags=re.I,
    )
    if not type_match:
        type_match = re.search(
            r"\.(load|stress|spike|soak|smoke)\.json$",
            basename,
            flags=re.I,
        )

    pr_match = re.match(
        r"^(PRLOAD|PRSPIKE|PRSTRESS|PRSOAK|PRSMOKE)",
        basename,
        flags=re.I,
    )

    test_type = ""
    if type_match:
        test_type = type_match.group(1).lower()
    elif pr_match:
        test_type = pr_match.group(1).lower().replace("pr", "")

    name = basename
    for pattern in [
        r"\.load-raw-metrics\.csv$",
        r"-raw-metrics\.csv$",
        r"\.json$",
        r"\.(load|stress|spike|soak|smoke)$",
        r"^(PRLOAD|PRSPIKE|PRSTRESS|PRSOAK|PRSMOKE|PR)[-_]?",
    ]:
        name = re.sub(pattern, "", name, flags=re.I)

    name = name.lower()
    if test_type:
        name = f"{name}.{test_type}"

    return name


def detect_kind(filename: str) -> str | None:
    """Detecta el tipo de prueba (PRLOAD, PRSTRESS, etc.) desde el nombre."""
    match = re.match(
        r"^(PRLOAD|PRSPIKE|PRSTRESS|PRSOAK|PRSMOKE)",
        os.path.basename(filename),
        flags=re.I,
    )
    return match.group(1).upper() if match else None


def discover(indir: str) -> list[dict[str, object]]:
    """Descubre archivos k6 (JSON + CSV) en un directorio y los agrupa en datasets."""
    datasets: dict[str, dict[str, object]] = {}

    for filename in sorted(os.listdir(indir)):
        filepath = os.path.join(indir, filename)
        ds_id = normalize_name(filename)

        if re.search(r"-raw-metrics\.csv$", filename, flags=re.I):
            ds = datasets.setdefault(ds_id, {"id": ds_id})
            ds["csv"] = filepath
            ds.setdefault("label", ds_id)

        elif re.search(r"\.json$", filename, flags=re.I):
            ds = datasets.setdefault(ds_id, {"id": ds_id})
            is_rich = bool(
                re.match(
                    r"^(PRLOAD|PRSPIKE|PRSTRESS|PRSOAK|PRSMOKE)",
                    filename,
                    flags=re.I,
                )
            )
            if "summary" not in ds or is_rich:
                ds["summary"] = filepath
            kind = detect_kind(filename)
            if kind:
                ds["kind"] = kind
            ds.setdefault("label", ds_id)

    return [d for d in datasets.values() if d.get("summary") or d.get("csv")]
