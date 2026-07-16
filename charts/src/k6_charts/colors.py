from __future__ import annotations

from k6_charts.config import Palette

_DEFAULT_PALETTE: Palette | None = None


def get_palette() -> Palette:
    global _DEFAULT_PALETTE
    if _DEFAULT_PALETTE is None:
        _DEFAULT_PALETTE = Palette()
    return _DEFAULT_PALETTE


def error_color(err_rate: float, palette: Palette | None = None) -> str:
    p = palette or get_palette()
    if err_rate <= 0.5:
        return p.good
    if err_rate <= 2.0:
        return p.warn
    return p.crit


def threshold_color(value: float, threshold: float, palette: Palette | None = None) -> str:
    p = palette or get_palette()
    return p.good if value <= threshold else p.crit


SERIES_COLORS: dict[str, str] = {
    "p95": "",
    "mediana": "",
    "media": "",
    "rps": "",
    "error": "",
}
