"""
ui/screens/inicio_screen.py
Pantalla 1 — INICIO (dashboard municipio, variables territoriales, sensibilidad, fórmula)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import flet as ft

from ui.theme import (
    SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.badge_riesgo import badge_riesgo
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import calc_iarri, nivel_riesgo, prob_ri, WEIGHTS
from core.datos import MUNICIPIOS, VARIABLES


# ═══════════════════════════════════════════════════════════
#  HELPERS MODO INVITADO
# ═══════════════════════════════════════════════════════════

def _banner_registro(on_ir_login):
    """Banner amarillo que aparece arriba en inicio cuando el usuario es invitado."""
    return ft.Container(
        content=ft.Row([
            ft.Text("👋", size=18),
            ft.Column([
                ft.Text("Estás como invitado", size=13,
                        weight=ft.FontWeight.W_700, color="#92400e"),
                ft.Text("Regístrate para guardar tu progreso y acceder a todas las funciones.",
                        size=11, color="#92400e"),
            ], spacing=1, expand=True),
            ft.ElevatedButton(
                "Registrarse",
                on_click=lambda e: on_ir_login(),
                style=ft.ButtonStyle(
                    bgcolor="#f59e0b", color="#1c1917",
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                ),
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#fef3c7",
        border=ft.border.all(1, "#fcd34d"),
        border_radius=14,
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
        margin=ft.margin.only(bottom=12),
    )


def _dialogo_registro(page, on_ir_login):
    """Muestra un diálogo cuando un invitado toca una función restringida."""
    def cerrar(e):
        dlg.open = False
        page.update()
    def ir(e):
        dlg.open = False
        page.update()
        on_ir_login()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔒 Función restringida", weight=ft.FontWeight.BOLD),
        content=ft.Text(
            "Esta función requiere una cuenta registrada. "
            "¡Regístrate gratis para desbloquear todo el contenido!",
            size=13,
        ),
        actions=[
            ft.TextButton("Más tarde", on_click=cerrar),
            ft.ElevatedButton(
                "Registrarse",
                on_click=ir,
                style=ft.ButtonStyle(
                    bgcolor="#0ea5e9", color="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def _pantalla_bloqueada(titulo, desc, on_registrar):
    """Pantalla de reemplazo cuando un invitado toca una función restringida."""
    return ft.Column([
        ft.Container(height=60),
        ft.Column([
            ft.Text("🔒", size=56, text_align=ft.TextAlign.CENTER),
            ft.Container(height=12),
            ft.Text(titulo, size=18, weight=ft.FontWeight.W_800,
                    color=TEXT, text_align=ft.TextAlign.CENTER),
            ft.Text(desc, size=13, color=MUTED, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, color=WHITE, size=18),
                    ft.Text("Crear cuenta gratis", size=13,
                            weight=ft.FontWeight.BOLD, color=WHITE),
                ], spacing=8, tight=True, alignment=ft.MainAxisAlignment.CENTER),
                on_click=lambda e: on_registrar(),
                style=ft.ButtonStyle(
                    bgcolor=ACCENT,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(horizontal=24, vertical=14),
                ),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 1 — INICIO
# ═══════════════════════════════════════════════════════════
def build_inicio(page, state):
    muni_idx = state["muni_idx"]
    muni     = MUNICIPIOS[muni_idx] #municipios
    iarri    = calc_iarri(muni["AV"], muni["IC"], muni["ED"], muni["EAR"], muni["IMP"])
    nivel, col = nivel_riesgo(iarri)
    
    def cambiar_muni(idx):#LLAMADA DE MUNICIOUI
        state["muni_idx"] = idx
        state["refresh"]()

    # Chips de municipio
    #correccion en content para acceder a la segunda pestaña por division de texto del nombre de municipio
    chips = ft.Row([
        ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(m["nombre"].split()[0] + " " + m["nombre"].split()[1] if len(m["nombre"].split()) > 1 else m["nombre"].split()[0],
                                size=11, weight=ft.FontWeight.W_600,
                                color=WHITE if i == muni_idx else MUTED),
                bgcolor=ACCENT if i == muni_idx else CARD,
                border=ft.border.all(1, ACCENT if i == muni_idx else BORDER),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
            ),
            on_tap=lambda e, i=i: cambiar_muni(i),
        )
        for i, m in enumerate(MUNICIPIOS)
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

    # Semáforo
    def dot(c, activo):
        return ft.Container(
            width=16, height=16, border_radius=8,
            bgcolor=c,
            shadow=ft.BoxShadow(blur_radius=10, color=c) if activo else None,
            opacity=1.0 if activo else 0.2,
        )

    semaforo = ft.Row([
        dot(LOW,  iarri <= 0.33),
        dot(MID,  0.33 < iarri <= 0.66),
        dot(HIGH, iarri > 0.66),
        ft.Text(f"Nivel {nivel}", size=12, color=MUTED),
    ], spacing=10)

    # Hero card
    hero = ft.Container(
        content=ft.Column([
            ft.Text("MUNICIPIO ACTIVO", size=10, color=MUTED,
                    weight=ft.FontWeight.BOLD, font_family="monospace"),
            chips,
            ft.Text(muni["nombre"], size=20, weight=ft.FontWeight.W_900, color=TEXT),
            ft.Row([
                ft.Text(f"{iarri:.2f}", size=58, weight=ft.FontWeight.W_900,
                        color=col, height=70),
                ft.Column([
                    ft.Text("IARRI-MX", size=10, color=MUTED, font_family="monospace"),
                    badge_riesgo(nivel, col),
                ], spacing=4, alignment=ft.MainAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.END),
            semaforo,
            ft.Row([
                ft.Text("Prob. Resistencia a la Insulina:", size=12, color=MUTED),
                ft.Text(f"{prob_ri(iarri)*100:.1f}%", size=14,
                        weight=ft.FontWeight.BOLD, color=col),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1,-1),
            end=ft.alignment.Alignment(1,1),
            colors=["#e0f2fe", "#ede9fe"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=22,
        padding=20,
        margin=ft.margin.only(bottom=12),
    )

    # Tarjetas de variables
    var_cards = []
    for v in VARIABLES:
        val = muni[v["key"]]
        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(v["icon"], size=18),
                        bgcolor=v["color"] + "22",
                        border_radius=10, width=36, height=36,
                        alignment=ft.alignment.Alignment(0,0),
                    ),
                    ft.Text(f"{val:.2f}", size=20, weight=ft.FontWeight.W_900,
                            color=v["color"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(v["key"], size=13, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.Text(v["label"], size=10, color=MUTED),
                ft.ProgressBar(
                    value=val,
                    color=v["color"],
                    bgcolor=BORDER,
                    border_radius=3,
                    height=5,
                    expand=True,
                ),
            ], spacing=4),
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            border_radius=16,
            padding=14,
            expand=True,
        )
        var_cards.append(card)

    grid_row1 = ft.Row([var_cards[0], var_cards[1]], spacing=10, expand=True)
    grid_row2 = ft.Row([var_cards[2], var_cards[3]], spacing=10, expand=True)
    grid_row3 = ft.Row([var_cards[4]], spacing=10, expand=True)

    # Sensibilidad — contribución real de cada variable al IARRI del municipio activo
    # contribución = peso × valor_municipal (para vars de riesgo) o peso × (1-valor) (para vars protectoras)
    _SENS_META = {
        "IC":  (ACCENT,  "Caminabilidad (protector)"),
        "EAR": (ACCENT2, "Entorno Alimentario (riesgo)"),
        "AV":  (LOW,     "Áreas Verdes (protector)"),
        "ED":  (ACCENT3, "Equip. Deportivo (protector)"),
        "IMP": (MID,     "Marginación (riesgo)"),
    }
    _RIESGO = {"EAR", "IMP"}  # vars de riesgo — mayor valor = mayor contribución al IARRI
    sens_items = [
        (
            k,
            WEIGHTS[k] * muni[k] if k in _RIESGO else WEIGHTS[k] * (1 - muni[k]),
            color,
            hint,
        )
        for k, (color, hint) in _SENS_META.items()
    ]
    sens_rows = []
    for k, contribucion, c, hint in sens_items:
        sens_rows.append(
            ft.Row([
                ft.Text(k, size=12, color=MUTED, width=36, font_family="monospace",
                        weight=ft.FontWeight.BOLD),
                ft.ProgressBar(
                    value=contribucion,
                    color=c,
                    bgcolor=BORDER,
                    border_radius=3,
                    height=8,
                    expand=True,
                ),
                ft.Text(f"{contribucion:.2f}", size=11, color=c, width=36,
                        text_align=ft.TextAlign.RIGHT, font_family="monospace"),
            ], spacing=8)
        )

    sens_card = tarjeta(ft.Column([
        ft.Text("Contribución al IARRI", size=13,
                weight=ft.FontWeight.BOLD, color=TEXT),
        ft.Text(f"Aporte real de cada variable en {muni['nombre']}",
                size=10, color=MUTED),
        *sens_rows,
    ], spacing=8))

    # Fórmula
    formula_card = tarjeta(ft.Column([
        ft.Text("Fórmula del Modelo", size=11, color=MUTED),
        ft.Text("IARRI = 0.20(1−AV) + 0.25(1−IC)\n       + 0.15(1−ED) + 0.25(EAR) + 0.15(IMP)",
                size=11, color=ACCENT, font_family="monospace"),
        ft.Row([
            ft.Container(content=ft.Text("  0.00–0.33  Bajo  ", size=10, color=LOW),
                         bgcolor=LOW+"22", border=ft.border.all(1,LOW+"44"), border_radius=8),
            ft.Container(content=ft.Text("  0.34–0.66  Medio  ", size=10, color=MID),
                         bgcolor=MID+"22", border=ft.border.all(1,MID+"44"), border_radius=8),
            ft.Container(content=ft.Text("  0.67–1.00  Alto  ", size=10, color=HIGH),
                         bgcolor=HIGH+"22", border=ft.border.all(1,HIGH+"44"), border_radius=8),
        ], wrap=True, spacing=6, run_spacing=4),
    ], spacing=8))

    # Banner para invitados
    banner = []
    if state.get("es_invitado"):
        def _ir_login_desde_inicio():
            state.get("logout", lambda: None)()
        banner = [_banner_registro(_ir_login_desde_inicio)]

    return ft.Column([
        *banner,
        hero,
        titulo_seccion("VARIABLES TERRITORIALES"),
        ft.Container(height=8),
        grid_row1, ft.Container(height=8), grid_row2,
        ft.Container(height=8), grid_row3,
        ft.Container(height=14),
        titulo_seccion("ANÁLISIS DE SENSIBILIDAD"),
        ft.Container(height=6),
        sens_card,
        ft.Container(height=10),
        formula_card,
        ft.Container(height=20),
        titulo_seccion("TEST RÁPIDO DE ENTORNO"),
        ft.Container(height=4),
        tarjeta(ft.Column([
            ft.Text("Responde preguntas sobre tu entorno urbano", size=12, color=MUTED),
            ft.Container(height=8),
            ft.ElevatedButton(
                "Iniciar test",
                icon=ft.Icons.ASSIGNMENT_OUTLINED,
                style=ft.ButtonStyle(
                    bgcolor=ACCENT3, color=WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=lambda e: state.get("ir_test", lambda: None)(),
            ),
        ], spacing=6)),
        ft.Container(height=20),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)
