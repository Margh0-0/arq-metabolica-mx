"""
ui/components/barra_progreso.py — Barras de progreso reutilizables.
"""

import flet as ft
from ui.theme import BORDER


def barra_progreso(valor, color, height=5):
    return ft.Stack([
        ft.Container(height=height, border_radius=3, bgcolor=BORDER, expand=True),
        ft.Container(
            height=height, border_radius=3, bgcolor=color,
            width=max(0, min(1, valor)) * 300,   # se ajusta con expand abajo
        ),
    ], expand=True)


def progress_bar_row(valor, color, height=6):
    """Barra de progreso que usa expand correctamente."""
    return ft.Container(
        content=ft.Container(
            bgcolor=color,
            border_radius=3,
            height=height,
            expand=False,
        ),
        bgcolor=BORDER,
        border_radius=3,
        height=height,
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        # Usamos overlay para simular el fill
    )
