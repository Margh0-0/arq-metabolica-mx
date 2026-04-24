"""
ui/components/tarjeta.py — Contenedor con sombra suave, esquinas redondeadas y borde opcional.
"""

import flet as ft
from ui.theme import CARD, BORDER


def tarjeta(content, padding=14, color=CARD, border=True):
    return ft.Container(
        content=content,
        bgcolor=color,
        border_radius=16,
        padding=padding,
        border=ft.border.all(1, BORDER) if border else None,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color="#0000000d",
            offset=ft.Offset(0, 2),
        ),
    )
