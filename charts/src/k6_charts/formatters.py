"""Funciones de formato para valores de métricas k6."""

from __future__ import annotations

import math


def fmt_ms(v: float | None, _: object = None) -> str:
    """Formatea milisegundos con unidades legibles."""
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    if v >= 1000:
        return f"{v / 1000:.2f} s"
    if v >= 100:
        return f"{v:.0f} ms"
    return f"{v:.1f} ms"


def fmt_int(v: float | None) -> str:
    """Formatea enteros con separador de miles."""
    if v is None:
        return "—"
    return f"{round(v):,}".replace(",", " ")


def fmt_dur(ms: float | None) -> str:
    """Formatea duración en milisegundos a minutos/segundos legibles."""
    if ms is None:
        return "—"
    s = round(ms / 1000)
    m, r = divmod(s, 60)
    return f"{m}m {r}s" if m else f"{r}s"


def fmt_time_axis(sec: float, span: float) -> str:
    """Formatea el eje de tiempo según el span total de la prueba."""
    if span > 120:
        m, r = divmod(int(round(sec)), 60)
        return f"{m}:{r:02d}"
    return f"{int(round(sec))}s"
