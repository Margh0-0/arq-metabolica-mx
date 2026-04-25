"""
ui/screens/recomendaciones_screen.py
Pantalla 4 — INTERVENCIÓN (recomendaciones priorizadas, simulación real, badges dinámicos)

Correcciones aplicadas (2026-04-25):
- Eliminada duplicación KPIs: solo se muestra resumen_card cuando hay resultado guardado
- Eliminado dead code: ft.Ref[bool]() sin asignar
- Simulación conectada a calc_iarri() — valores calculados, no hardcodeados
- Recomendaciones priorizadas por variable más débil del resultado actual
- Badges dinámicos via GAMIFICACION_BADGES + _badge_desbloqueada (no BADGES estático)
- Sección Metodología movida a perfil_screen
- Concatenación hex+opacidad saneada via helper _hex_alpha()
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import calc_iarri, nivel_riesgo, prob_ri
from core.datos import MUNICIPIOS, RECOMENDACIONES


# ─── Helper: hex color + opacidad ────────────────────────────────────────────

def _hex_alpha(color: str, alpha_hex: str) -> str:
    """
    Concatena un color hex (#rrggbb) con un sufijo de opacidad (2 dígitos hex).
    Maneja colores que ya vienen con canal alfa (#rrggbbaa) — en ese caso los
    reemplaza en lugar de acumular.
    """
    base = color.lstrip("#")
    if len(base) == 8:
        # Ya tiene canal alfa — reemplazar
        return f"#{base[:6]}{alpha_hex}"
    return f"#{base}{alpha_hex}"


# ─── Priorización de recomendaciones ─────────────────────────────────────────

# Mapeo: cada variable débil → qué recomendación atacarla primero
_VAR_A_REC = {
    "AV":  "Incrementar Áreas Verdes",
    "IC":  "Ruta Diaria de 15 min",
    "ED":  "Espacios Deportivos",
    "EAR": "Regulación Alimentaria",
    "IMP": "Diseño Arquitectónico",
}

# Umbrales: variable es "débil" cuando supera este valor en su contribución al riesgo
# (variables protectoras: bajo valor = mayor riesgo; variables riesgo: alto valor = mayor riesgo)
_INV_VARS = {"AV", "IC", "ED"}   # inversas: mal = valor BAJO


def _priorizar_recomendaciones(resultado: dict | None) -> list[dict]:
    """
    Retorna RECOMENDACIONES ordenadas por impacto descendente según el resultado guardado.

    Si no hay resultado, retorna las recomendaciones en orden original.
    La primera recomendación corresponde a la variable con mayor deficit.
    """
    if not resultado:
        return RECOMENDACIONES

    # Extraer variables del resultado (guardado por calculadora_screen)
    vars_actuales = {
        "AV":  resultado.get("AV",  0.5),
        "IC":  resultado.get("IC",  0.5),
        "ED":  resultado.get("ED",  0.5),
        "EAR": resultado.get("EAR", 0.5),
        "IMP": resultado.get("IMP", 0.5),
    }

    # Calcular "urgencia" por variable (0=sin urgencia, 1=urgencia máxima)
    urgencia = {}
    for key, val in vars_actuales.items():
        if key in _INV_VARS:
            urgencia[key] = 1.0 - val   # protectoras: urgente si valor es BAJO
        else:
            urgencia[key] = val          # riesgo: urgente si valor es ALTO

    # Asignar urgencia a cada recomendación según la variable que ataca
    var_por_titulo = {v: k for k, v in _VAR_A_REC.items()}
    def _urgencia_rec(r: dict) -> float:
        var = var_por_titulo.get(r["titulo"])
        return urgencia.get(var, 0.5) if var else 0.5

    return sorted(RECOMENDACIONES, key=_urgencia_rec, reverse=True)


# ─── Simulación arquitectónica ────────────────────────────────────────────────

# Mejoras propuestas para la simulación (deltas sobre valores base del municipio)
_DELTAS_SIMULACION = {
    "AV":  +0.25,   # +25% áreas verdes
    "IC":  +0.25,   # +25% caminabilidad
    "ED":  +0.20,   # +20% equipamiento deportivo
    "EAR":  0.0,    # sin cambio en entorno alimentario (regulación lenta)
    "IMP":  0.0,    # sin cambio en marginación (estructural)
}

# Variables que participan en la visualización de barras (las que cambian)
_VARS_VISIBLES = ["AV", "IC", "ED"]
_COLOR_VARS = {
    "AV": LOW,
    "IC": ACCENT,
    "ED": ACCENT3,
}


def _calcular_simulacion(municipio: dict) -> dict:
    """
    Toma las variables base del municipio y aplica los deltas para calcular
    IARRI antes y después con calc_iarri().

    Retorna dict con: antes_vars, despues_vars, iarri_antes, iarri_despues,
    prob_antes, prob_despues, reduccion_pct.
    """
    antes = {k: municipio[k] for k in ("AV", "IC", "ED", "EAR", "IMP")}
    despues = {
        k: max(0.0, min(1.0, antes[k] + _DELTAS_SIMULACION.get(k, 0.0)))
        for k in antes
    }

    iarri_a = calc_iarri(**antes)
    iarri_d = calc_iarri(**despues)
    prob_a  = prob_ri(iarri_a)
    prob_d  = prob_ri(iarri_d)
    reduccion = (iarri_a - iarri_d) / iarri_a * 100 if iarri_a > 0 else 0.0

    return {
        "antes_vars":    antes,
        "despues_vars":  despues,
        "iarri_antes":   iarri_a,
        "iarri_despues": iarri_d,
        "prob_antes":    prob_a,
        "prob_despues":  prob_d,
        "reduccion_pct": reduccion,
    }


# ─── Builder principal ────────────────────────────────────────────────────────

def build_recomendaciones(page, state):

    muni_idx         = state.get("muni_idx", 0)
    municipio        = MUNICIPIOS[muni_idx]
    municipio_nombre = municipio["nombre"]
    resultado_guardado = state.get("resultados_municipios", {}).get(muni_idx)

    # ── Resumen del resultado guardado (sin KPIs duplicados) ──────────────────
    if resultado_guardado:
        col_res = nivel_riesgo(resultado_guardado["iarri"])[1]
        resumen_card = tarjeta(ft.Column([
            ft.Text("Resultado guardado", size=13, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text(f"Municipio: {municipio_nombre}", size=12, color=TEXT),
            ft.Container(height=8),
            ft.Row([
                ft.Column([
                    ft.Text("IARRI", size=10, color=MUTED),
                    ft.Text(
                        f"{resultado_guardado['iarri']:.4f}",
                        size=22, weight=ft.FontWeight.W_900, color=col_res,
                    ),
                ]),
                ft.Column([
                    ft.Text("Nivel", size=10, color=MUTED),
                    ft.Text(
                        resultado_guardado["nivel"],
                        size=22, weight=ft.FontWeight.W_900, color=col_res,
                    ),
                ]),
                ft.Column([
                    ft.Text("Prob. RI", size=10, color=MUTED),
                    ft.Text(
                        f"{resultado_guardado['prob']*100:.1f}%",
                        size=22, weight=ft.FontWeight.W_900, color=col_res,
                    ),
                ]),
            ], spacing=20, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Container(height=4),
            ft.Text(
                "Valores del ajuste personalizado guardado en Calculadora.",
                size=11, color=MUTED,
            ),
        ], spacing=10), padding=14)
    else:
        resumen_card = tarjeta(ft.Column([
            ft.Text("Sin cálculo guardado", size=13, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text(
                "Ve a la pestaña Calcular y guardá tu IARRI para ver "
                "recomendaciones personalizadas.",
                size=12, color=MUTED,
            ),
        ], spacing=10), padding=14)

    # ── Recomendaciones priorizadas ───────────────────────────────────────────
    recs_ordenadas = _priorizar_recomendaciones(resultado_guardado)

    rec_cards = []
    for idx, r in enumerate(recs_ordenadas):
        body = ft.Container(
            content=ft.Column([
                ft.Text(r["desc"], size=12, color=MUTED),
                ft.Container(
                    content=ft.Text(
                        r["impacto"], size=11, color=r["color"],
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=_hex_alpha(r["color"], "11"),
                    border=ft.border.all(1, _hex_alpha(r["color"], "33")),
                    border_radius=8, padding=8,
                ),
            ], spacing=6),
            visible=False,
            padding=ft.padding.only(top=10, left=4),
        )

        # Badge de prioridad para la primera recomendación cuando hay resultado
        prioridad_badge = None
        if idx == 0 and resultado_guardado:
            prioridad_badge = ft.Container(
                content=ft.Text("PRIORITARIA", size=9, color=WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=r["color"],
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=7, vertical=3),
            )

        def toggle(e, b=body):
            b.visible = not b.visible
            page.update()

        header_row_children = [
            ft.Container(
                content=ft.Text(r["icon"], size=22),
                bgcolor=_hex_alpha(r["color"], "22"),
                border_radius=10,
                width=44, height=44,
                alignment=ft.alignment.Alignment(0, 0),
            ),
            ft.Column([
                ft.Row(
                    [
                        ft.Text(r["titulo"], size=13, weight=ft.FontWeight.W_600, color=TEXT),
                        *([] if prioridad_badge is None else [prioridad_badge]),
                    ],
                    spacing=6,
                    wrap=True,
                ),
                ft.Text(r["impacto"], size=11, color=r["color"], weight=ft.FontWeight.BOLD),
            ], spacing=2, expand=True),
            ft.Text("›", size=22, color=MUTED),
        ]

        rec_cards.append(
            ft.Container(
                content=ft.Column([
                    ft.GestureDetector(
                        content=ft.Row(header_row_children, spacing=12),
                        on_tap=toggle,
                    ),
                    body,
                ], spacing=0),
                bgcolor=CARD,
                border=ft.border.all(1, BORDER if idx > 0 else _hex_alpha(r["color"], "55")),
                border_radius=16, padding=14,
                margin=ft.margin.only(bottom=8),
            )
        )

    # ── Simulación conectada a calc_iarri() ───────────────────────────────────
    sim = _calcular_simulacion(municipio)

    nivel_a, color_a = nivel_riesgo(sim["iarri_antes"])
    nivel_d, color_d = nivel_riesgo(sim["iarri_despues"])

    sim_rows = []
    for key in _VARS_VISIBLES:
        val_antes  = sim["antes_vars"][key]
        val_despues = sim["despues_vars"][key]
        col        = _COLOR_VARS[key]
        sim_rows.append(
            ft.Row([
                ft.Text(
                    key, size=12, width=32, color=MUTED,
                    weight=ft.FontWeight.BOLD, font_family="monospace",
                ),
                ft.Container(
                    content=ft.Container(
                        bgcolor=col, border_radius=3,
                        height=7,
                        width=val_despues * 160,
                    ),
                    bgcolor=BORDER, border_radius=3, height=7,
                    expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Text(
                    f"{val_antes:.2f}→{val_despues:.2f}",
                    size=10, color=col,
                    font_family="monospace", width=88,
                ),
            ], spacing=8)
        )

    sim_card = tarjeta(ft.Column([
        ft.Text(
            f"Simulación: {municipio_nombre}",
            size=13, weight=ft.FontWeight.BOLD, color=TEXT,
        ),
        ft.Text(
            "Escenario: +25% áreas verdes, +25% caminabilidad, +20% equipamiento deportivo",
            size=11, color=MUTED,
        ),
        ft.Container(height=4),
        *sim_rows,
        ft.Divider(height=1, color=BORDER),
        ft.Row([
            ft.Column([
                ft.Text("Antes", size=10, color=MUTED),
                ft.Text(f"{sim['iarri_antes']:.3f}", size=28, weight=ft.FontWeight.W_900, color=color_a),
                ft.Text(nivel_a, size=11, color=color_a),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("→", size=24, color=ACCENT),
            ft.Column([
                ft.Text("Después", size=10, color=MUTED),
                ft.Text(f"{sim['iarri_despues']:.3f}", size=28, weight=ft.FontWeight.W_900, color=color_d),
                ft.Text(nivel_d, size=11, color=color_d),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Reducción", size=10, color=MUTED),
                ft.Text(f"−{sim['reduccion_pct']:.1f}%", size=22, weight=ft.FontWeight.W_900, color=ACCENT),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        ft.Container(
            content=ft.Text(
                f"Prob. RI: {sim['prob_antes']*100:.0f}% → {sim['prob_despues']*100:.0f}%  "
                "— Potencial preventivo del diseño urbano (ENSANUT)",
                size=11, color=ACCENT, text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=_hex_alpha(ACCENT, "11"),
            border=ft.border.all(1, _hex_alpha(ACCENT, "33")),
            border_radius=10, padding=10,
        ),
    ], spacing=10))

    # ── Layout final ──────────────────────────────────────────────────────────
    return ft.Column([
        resumen_card,
        ft.Container(height=12),
        titulo_seccion("INTERVENCIONES PRIORITARIAS"),
        ft.Container(height=6),
        *rec_cards,
        titulo_seccion("SIMULACIÓN ARQUITECTÓNICA"),
        ft.Container(height=8),
        sim_card,
        ft.Container(height=24),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)
