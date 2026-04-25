"""
ui/components/barra_progreso.py — Barras de progreso reutilizables.
"""

import flet as ft
from ui.theme import BORDER


def barra_progreso(valor, color, height=5):
    """Barra de progreso proporcional — sin píxeles absolutos."""
    pct = max(0.0, min(1.0, valor))
    fill_expand = max(1, int(pct * 100))
    empty_expand = max(1, 100 - fill_expand)
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(bgcolor=color, height=height, expand=fill_expand),
                ft.Container(bgcolor=ft.Colors.TRANSPARENT, height=height, expand=empty_expand),
            ],
            spacing=0,
            expand=True,
        ),
        bgcolor=BORDER,
        border_radius=3,
        height=height,
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


def progress_bar_row(valor, color, height=6):
    """Barra de progreso que usa expand correctamente."""
    pct = max(0.0, min(1.0, valor))
    fill_expand = max(1, int(pct * 100))
    empty_expand = max(1, 100 - fill_expand)
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(bgcolor=color, height=height, expand=fill_expand),
                ft.Container(bgcolor=ft.Colors.TRANSPARENT, height=height, expand=empty_expand),
            ],
            spacing=0,
            expand=True,
        ),
        bgcolor=BORDER,
        border_radius=3,
        height=height,
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
