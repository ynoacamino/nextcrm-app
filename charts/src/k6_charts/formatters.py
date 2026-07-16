from __future__ import annotations

import math


def fmt_ms(v: float | None, _: object = None) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "\u2014"
    if v >= 1000:
        return f"{v / 1000:.2f} s"
    if v >= 100:
        return f"{v:.0f} ms"
    return f"{v:.1f} ms"


def fmt_int(v: float | None) -> str:
    if v is None:
        return "\u2014"
    return f"{round(v):,}".replace(",", " ")


def fmt_dur(ms: float | None) -> str:
    if ms is None:
        return "\u2014"
    s = round(ms / 1000)
    m, r = divmod(s, 60)
    return f"{m}m {r}s" if m else f"{r}s"


def fmt_time_axis(sec: float, span: float) -> str:
    if span > 120:
        m, r = divmod(int(round(sec)), 60)
        return f"{m}:{r:02d}"
    return f"{int(round(sec))}s"
