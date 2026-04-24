"""
ui/components/badge_riesgo.py — Badge de nivel de riesgo con color e indicador circular.
"""

import flet as ft


def badge_riesgo(nivel, color):
    return ft.Container(
        content=ft.Row([
            ft.Container(width=8, height=8, border_radius=4, bgcolor=color),
            ft.Text(f"Riesgo {nivel}", size=12, weight=ft.FontWeight.BOLD, color=color),
        ], spacing=6, tight=True),
        bgcolor=color + "22",
        border=ft.border.all(1, color + "55"),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
    )
