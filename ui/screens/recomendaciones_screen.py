"""
ui/screens/recomendaciones_screen.py
Pantalla 4 — RECOMENDACIONES + GAMIFICACIÓN (intervenciones, simulación, badges)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import nivel_riesgo
from core.datos import MUNICIPIOS, RECOMENDACIONES, BADGES


def build_recomendaciones(page, state):

    muni_idx = state.get("muni_idx", 0)
    municipio_actual = MUNICIPIOS[muni_idx]["nombre"]
    resultado_guardado = state.get("resultados_municipios", {}).get(muni_idx)

    if resultado_guardado:
        col_res = nivel_riesgo(resultado_guardado["iarri"])[1]
        resumen_card = tarjeta(ft.Column([
            ft.Text("Resultado guardado", size=13, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text(f"Municipio: {municipio_actual}", size=12, color=TEXT),
            ft.Container(height=10),
            ft.Row([
                ft.Column([
                    ft.Text("IARRI", size=10, color=MUTED),
                    ft.Text(f"{resultado_guardado['iarri']:.4f}", size=22, weight=ft.FontWeight.W_900, color=col_res),
                ]),
                ft.Column([
                    ft.Text("Nivel", size=10, color=MUTED),
                    ft.Text(resultado_guardado['nivel'], size=22, weight=ft.FontWeight.W_900, color=col_res),
                ]),
                ft.Column([
                    ft.Text("Prob. RI", size=10, color=MUTED),
                    ft.Text(f"{resultado_guardado['prob']*100:.1f}%", size=22, weight=ft.FontWeight.W_900, color=col_res),
                ]),
            ], spacing=20, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Container(height=4),
            ft.Text("Estos valores vienen del ajuste personalizado guardado en Calculadora.", size=11, color=MUTED),
        ], spacing=10), padding=14)
        kpis = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("IARRI guardado", size=11, color=MUTED),
                    ft.Text(f"{resultado_guardado['iarri']:.4f}", size=22, weight=ft.FontWeight.W_900, color=col_res),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Riesgo", size=11, color=MUTED),
                    ft.Text(resultado_guardado['nivel'], size=22, weight=ft.FontWeight.W_900, color=col_res),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Prob. RI", size=11, color=MUTED),
                    ft.Text(f"{resultado_guardado['prob']*100:.0f}%", size=22, weight=ft.FontWeight.W_900, color=col_res),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
        ], spacing=8)
    else:
        resumen_card = tarjeta(ft.Column([
            ft.Text("Aún no hay un cálculo guardado", size=13, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text("Ve a la pestaña Calcular y guarda tu IARRI para ver recomendaciones personalizadas.", size=12, color=MUTED),
        ], spacing=10), padding=14)
        kpis = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("18.2%", size=22, weight=ft.FontWeight.W_900, color=ACCENT),
                    ft.Text("Reducción", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("0.78→0.64", size=16, weight=ft.FontWeight.W_900, color=MID),
                    ft.Text("IARRI post-interv.", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("3", size=22, weight=ft.FontWeight.W_900, color=ACCENT3),
                    ft.Text("Insignias", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
                padding=12, expand=True,
            ),
        ], spacing=8)

    # Recomendaciones expandibles
    rec_cards = []
    for r in RECOMENDACIONES:
        expanded = ft.Ref[bool]()
        body = ft.Container(
            content=ft.Column([
                ft.Text(r["desc"], size=12, color=MUTED),
                ft.Container(
                    content=ft.Text(r["impacto"], size=11, color=r["color"],
                                    weight=ft.FontWeight.BOLD),
                    bgcolor=r["color"]+"11",
                    border=ft.border.all(1, r["color"]+"33"),
                    border_radius=8, padding=8,
                ),
            ], spacing=6),
            visible=False,
            padding=ft.padding.only(top=10, left=4),
        )

        def toggle(e, b=body):
            b.visible = not b.visible
            page.update()

        rec_cards.append(
            ft.Container(
                content=ft.Column([
                    ft.GestureDetector(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(r["icon"], size=22),
                                bgcolor=r["color"]+"22", border_radius=10,
                                width=44, height=44, alignment=ft.alignment.Alignment(0,0),
                            ),
                            ft.Column([
                                ft.Text(r["titulo"], size=13, weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Text(r["impacto"], size=11, color=r["color"],
                                        weight=ft.FontWeight.BOLD),
                            ], spacing=2, expand=True),
                            ft.Text("›", size=22, color=MUTED),
                        ], spacing=12),
                        on_tap=toggle,
                    ),
                    body,
                ], spacing=0),
                bgcolor=CARD, border=ft.border.all(1,BORDER),
                border_radius=16, padding=14,
                margin=ft.margin.only(bottom=8),
            )
        )

    # Simulación Cuautlancingo
    antes   = {"AV":0.30,"IC":0.20,"ED":0.10,"EAR":0.80,"IMP":0.70}
    despues = {"AV":0.55,"IC":0.45,"ED":0.30,"EAR":0.80,"IMP":0.70}
    cambios = [("AV","0.30→0.55",LOW),("IC","0.20→0.45",ACCENT),("ED","0.10→0.30",ACCENT3)]
    sim_rows = [
        ft.Row([
            ft.Text(k, size=12, width=32, color=MUTED, weight=ft.FontWeight.BOLD,
                    font_family="monospace"),
            ft.Container(
                content=ft.Container(bgcolor=col, border_radius=3,
                                      height=7, width=float(cambio.split("→")[1])*160),
                bgcolor=BORDER, border_radius=3, height=7,
                expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Text(cambio, size=10, color=col, font_family="monospace", width=80),
        ], spacing=8)
        for k, cambio, col in cambios
    ]

    sim_card = tarjeta(ft.Column([
        ft.Text("Simulación: Cuautlancingo", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        *sim_rows,
        ft.Divider(height=1, color=BORDER),
        ft.Row([
            ft.Column([
                ft.Text("Antes", size=10, color=MUTED),
                ft.Text("0.78", size=28, weight=ft.FontWeight.W_900, color=HIGH),
                ft.Text("Alto", size=11, color=HIGH),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("→", size=24, color=ACCENT),
            ft.Column([
                ft.Text("Después", size=10, color=MUTED),
                ft.Text("0.64", size=28, weight=ft.FontWeight.W_900, color=MID),
                ft.Text("Medio", size=11, color=MID),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Reducción", size=10, color=MUTED),
                ft.Text("−18.2%", size=22, weight=ft.FontWeight.W_900, color=ACCENT),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        ft.Container(
            content=ft.Text("↓ Potencial preventivo del diseño urbano (ENSANUT)",
                             size=11, color=ACCENT, text_align=ft.TextAlign.CENTER),
            bgcolor=ACCENT+"11", border=ft.border.all(1,ACCENT+"33"),
            border_radius=10, padding=10,
        ),
    ], spacing=10))

    # Badges
    badge_items = []
    for b in BADGES:
        badge_items.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(b["emoji"], size=28, opacity=1.0 if b["earned"] else 0.3),
                    ft.Text(b["nombre"], size=10, text_align=ft.TextAlign.CENTER,
                            color=TEXT if b["earned"] else MUTED,
                            weight=ft.FontWeight.W_600 if b["earned"] else ft.FontWeight.NORMAL),
                    ft.Text("✓ Ganada" if b["earned"] else "🔒",
                            size=9, color=ACCENT3 if b["earned"] else MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=CARD if not b["earned"] else ACCENT3+"11",
                border=ft.border.all(1, ACCENT3 if b["earned"] else BORDER),
                border_radius=14, padding=12,
                expand=True,
            )
        )

    badges_grid = ft.Column([
        ft.Row(badge_items[:3], spacing=8),
        ft.Row(badge_items[3:], spacing=8),
    ], spacing=8)

    # Metodología
    fases = [
        ("Fase 1", "Integración de datos (INEGI, CONAPO, DENUE)"),
        ("Fase 2", "Modelado matemático IARRI-MX"),
        ("Fase 3", "Validación estadística (Moran I, Regresión)"),
        ("Fase 4", "Desarrollo tecnológico (app móvil)"),
        ("Fase 5", "Implementación piloto — Puebla"),
    ]
    fase_rows = [
        ft.Row([
            ft.Container(width=8, height=8, border_radius=4, bgcolor=ACCENT,
                          margin=ft.margin.only(top=2)),
            ft.Column([
                ft.Text(f, size=11, color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Text(d, size=11, color=MUTED),
            ], spacing=1),
        ], spacing=10)
        for f, d in fases
    ]
    ods_row = ft.Row([
        ft.Container(
            content=ft.Text("🎯 ODS 3 — Salud y Bienestar", size=11, color=ACCENT3),
            bgcolor=ACCENT3+"11", border=ft.border.all(1,ACCENT3+"33"),
            border_radius=8, padding=ft.padding.symmetric(horizontal=10, vertical=5),
        ),
        ft.Container(
            content=ft.Text("🌆 ODS 11 — Ciudades Sostenibles", size=11, color=ACCENT3),
            bgcolor=ACCENT3+"11", border=ft.border.all(1,ACCENT3+"33"),
            border_radius=8, padding=ft.padding.symmetric(horizontal=10, vertical=5),
        ),
    ], wrap=True, spacing=8)

    meto_card = tarjeta(ft.Column([
        ft.Text("Metodología y Fuentes", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        *fase_rows,
        ft.Divider(height=1, color=BORDER),
        ods_row,
    ], spacing=8))

    return ft.Column([
        resumen_card,
        ft.Container(height=12),
        kpis,
        ft.Container(height=12),
        titulo_seccion("INTERVENCIONES PRIORITARIAS"),
        ft.Container(height=6),
        *rec_cards,
        titulo_seccion("SIMULACIÓN ARQUITECTÓNICA"),
        ft.Container(height=8),
        sim_card,
        ft.Container(height=12),
        titulo_seccion("INSIGNIAS — GAMIFICACIÓN"),
        ft.Container(height=8),
        badges_grid,
        ft.Container(height=12),
        meto_card,
        ft.Container(height=24),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)
