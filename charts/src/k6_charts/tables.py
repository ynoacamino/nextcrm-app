"""Tables — renderizado de tablas como imagen (PNG + PDF)."""

from __future__ import annotations

from typing import Callable

import matplotlib.pyplot as plt

from k6_charts.config import Theme


def render_table(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    outdir: str,
    file_id: str,
    aligns: list[str] | None = None,
    cell_color: Callable[[int, int, str], str | None] | None = None,
    col_scale: list[float] | None = None,
    theme: Theme | None = None,
) -> str:
    """Renderiza una tabla como imagen PNG (300 dpi) + PDF vectorial.

    Args:
        title: Título de la tabla.
        headers: Lista de encabezados de columna.
        rows: Filas de datos (cada fila es una lista de strings).
        outdir: Directorio de salida.
        file_id: Nombre del archivo sin extensión.
        aligns: Alineación por columna ("left", "right", "center").
        cell_color: Función (row_idx, col_idx, value) -> color | None.
        col_scale: Escalado de anchos por columna.
        theme: Tema de estilo (usa Theme() por defecto).

    Returns:
        Nombre del archivo generado.
    """
    th = theme or Theme()
    p = th.palette
    ncol = len(headers)
    nrow = len(rows)

    if aligns is None:
        aligns = ["left"] * ncol

    widths: list[float] = []
    for c in range(ncol):
        w = max(
            [len(str(headers[c]))] + [len(str(r[c])) for r in rows]
        ) if nrow else len(str(headers[c]))
        widths.append(w)

    if col_scale:
        widths = [w * s for w, s in zip(widths, col_scale)]

    tot = sum(widths)
    figw = min(15.0, max(6.0, tot * 0.115 + 0.6))
    rowin = 0.42
    titlein = 0.6 if title else 0.12
    figh = rowin * (nrow + 1) + titlein + 0.12

    fig = plt.figure(figsize=(figw, figh))
    ax = fig.add_axes([
        0.012, 0.06 / figh, 0.976, 1 - (titlein + 0.06) / figh,
    ])
    ax.axis("off")

    if title:
        fig.text(
            0.012, 1 - 0.34 / figh, title, ha="left", va="center",
            fontsize=13.5, fontweight="bold", color=p.ink,
        )

    tbl = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="center",
        loc="center",
        colWidths=[w / tot for w in widths],
        bbox=[0, 0, 1, 1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)

    amap = {"left": "left", "right": "right", "center": "center"}

    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(p.grid)
        cell.set_linewidth(0.7)
        cell.PAD = 0.04

        cell.get_text().set_horizontalalignment(amap[aligns[c]] if r > 0 else "left")
        if aligns[c] == "left":
            cell.get_text().set_x(0.03)
        elif aligns[c] == "right":
            cell.get_text().set_x(0.97)

        if r == 0:
            cell.set_facecolor(p.zebra)
            cell.get_text().set_color(p.ink2)
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_horizontalalignment("left")
            cell.get_text().set_x(0.03)
            cell.set_edgecolor(p.axis)
        else:
            cell.set_facecolor(p.panel if r % 2 else p.zebra)
            color = None
            if cell_color:
                color = cell_color(r - 1, c, rows[r - 1][c])
            if color is None:
                color = p.ink if c == 0 else p.ink2
            cell.get_text().set_color(color)
            if c == 0:
                cell.get_text().set_fontweight("bold")

    import os
    png_path = os.path.join(outdir, file_id + ".png")
    pdf_path = os.path.join(outdir, file_id + ".pdf")
    fig.savefig(png_path, dpi=th.dpi)
    fig.savefig(pdf_path)
    plt.close(fig)
    return file_id
