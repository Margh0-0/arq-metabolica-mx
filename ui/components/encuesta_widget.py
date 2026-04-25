"""
ui/components/encuesta_widget.py — Widget de encuesta paso a paso con barra de progreso.
"""

import flet as ft
from ui.theme import MUTED, ACCENT, BORDER, CARD, TEXT
from core.datos import ENCUESTA, VARIABLES


def titulo_seccion(texto):
    return ft.Text(texto, size=11, weight=ft.FontWeight.BOLD,
                   color="#94a3b8", font_family="monospace")


def build_encuesta(page, on_complete):  # cambio bb
    respuestas = {}
    paso_actual = [0]
    contenido = ft.Column([], spacing=12, scroll=ft.ScrollMode.AUTO)
    progreso_txt = ft.Text("", size=11, color=MUTED)
    progreso_bar = ft.ProgressBar(value=0, expand=True, color=ACCENT, bgcolor=BORDER, bar_height=4)

    def render_paso():
        idx = paso_actual[0]
        total = len(ENCUESTA)
        progreso_txt.value = f"Pregunta {idx+1} de {total}"
        progreso_bar.value = idx / total

        q = ENCUESTA[idx]
        v = next(var for var in VARIABLES if var["key"] == q["variable"])

        botones = []
        for op in q["opciones"]:
            def make_click(valor, variable):
                def on_click(e):
                    respuestas[variable] = valor
                    if paso_actual[0] < len(ENCUESTA) - 1:
                        paso_actual[0] += 1
                        render_paso()
                    else:
                        on_complete(respuestas)
                return on_click
            botones.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(v["icon"], size=16),
                            bgcolor=v["color"] + "22",
                            border_radius=8,
                            width=34, height=34,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(op["texto"], size=13, color=TEXT, expand=True),
                    ], spacing=10),
                    bgcolor=CARD,
                    border=ft.border.all(1, v["color"] + "55"),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ink=True,
                    on_click=make_click(op["valor"], q["variable"]),
                )
            )

        contenido.controls = [
            ft.Container(height=4),
            ft.Row([
                ft.Container(
                    content=ft.Text(v["icon"], size=22),
                    bgcolor=v["color"] + "22",
                    border_radius=12,
                    width=48, height=48,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(v["label"], size=12, color=v["color"], weight=ft.FontWeight.BOLD),
                    ft.Text(q["pregunta"], size=15, color=TEXT, weight=ft.FontWeight.W_600),
                ], spacing=2, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=8),
            *botones,
        ]
        page.update()

    render_paso()

    return ft.Column([
        ft.Row([progreso_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        progreso_bar,
        ft.Container(height=8),
        contenido,
    ], spacing=8, expand=True)
