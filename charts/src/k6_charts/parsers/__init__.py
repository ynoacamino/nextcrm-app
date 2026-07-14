"""Parsers para archivos de salida de k6."""

from k6_charts.parsers.discovery import discover, normalize_name, detect_kind
from k6_charts.parsers.summary import parse_summary
from k6_charts.parsers.csv_timeseries import parse_csv
from k6_charts.parsers.infra import parse_infra_csv

__all__ = [
    "discover",
    "normalize_name",
    "detect_kind",
    "parse_summary",
    "parse_csv",
    "parse_infra_csv",
]
