
"""
ARQ-Metabólica MX — App Móvil con Flet (Python + Flutter)
Índice Arquitectónico de Riesgo de Resistencia a la Insulina (IARRI-MX)

Instalar:  pip install flet numpy scipy
Correr:    python main.py
APK:       flet build apk
iOS:       flet build ipa
"""

import flet as ft
import numpy as np
import threading
import math
# ═══════════════════════════════════════════════════════════
#  UI — Theme + Components (extraídos a módulos)
#  F4 del refactor arquitectural — 2026-04-23
# ═══════════════════════════════════════════════════════════
from ui.theme import (
    COLORES, PALETAS, get_paleta,
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.badge_riesgo import badge_riesgo
from ui.components.barra_progreso import barra_progreso, progress_bar_row
from ui.components.encuesta_widget import build_encuesta, titulo_seccion

# ═══════════════════════════════════════════════════════════
#  CORE — Lógica científica y datos (extraídos a módulos)
#  F2 del refactor arquitectural — 2026-04-23
# ═══════════════════════════════════════════════════════════
from core.iarri import calc_iarri, nivel_riesgo, prob_ri, monte_carlo, WEIGHTS
from core.datos import (
    MUNICIPIOS, DATOS_TERRITORIALES, ENCUESTA, VARIABLES,
    RECOMENDACIONES, BADGES, LECCIONES, _csv_datos,
)


# (tarjeta, badge_riesgo, barra_progreso, progress_bar_row, build_encuesta,
#  titulo_seccion → importados desde ui.components al inicio del archivo)


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
                ft.Container(
                    content=ft.Container(bgcolor=v["color"], border_radius=3, height=5,
                                         width=max(2, val * 130)),
                    bgcolor=BORDER, border_radius=3, height=5,
                    margin=ft.margin.only(top=4),
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

    # Sensibilidad
    sens_items = [
        ("IC",  0.25, ACCENT,  "Mayor impacto (protector)"),
        ("EAR", 0.25, ACCENT2, "Mayor impacto (riesgo)"),
        ("AV",  0.20, LOW,     "Impacto medio"),
        ("ED",  0.15, ACCENT3, "Impacto moderado"),
        ("IMP",  0.15, MID,     "Impacto moderado"),
    ]
    sens_rows = []
    for k, val, c, hint in sens_items:
        sens_rows.append(
            ft.Row([
                ft.Text(k, size=12, color=MUTED, width=36, font_family="monospace",
                        weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Container(bgcolor=c, border_radius=3,
                                          height=8, width=val * 300),
                    bgcolor=BORDER, border_radius=3, height=8, expand=True,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Text(f"{val:.2f}", size=11, color=c, width=36,
                        text_align=ft.TextAlign.RIGHT, font_family="monospace"),
            ], spacing=8)
        )

    sens_card = tarjeta(ft.Column([ #analisis de derivada parcial
        ft.Text("∂IARRI — Derivadas Parciales", size=13,
                weight=ft.FontWeight.BOLD, color=TEXT),
        ft.Text("Mayor impacto: Caminabilidad (IC) y Entorno Alimentario (EAR)",
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


# ═══════════════════════════════════════════════════════════
#  PANTALLA 2 — MÓDULO 2: ANÁLISIS TERRITORIAL INEGI
# ═══════════════════════════════════════════════════════════

def build_mapa(page, state):
    """
    Mapa interactivo con flet_map (OpenStreetMap).
    - Desktop/Web: muestra mapa embebido + botón para abrir HTML en navegador
    - Android/iOS: mapa embebido con marcadores y zonas de riesgo
    Tiles: OpenStreetMap (gratis, sin API key).
    """
    import json as _json
    import os as _os2

    muni_idx  = state.get("muni_idx", 0)
    muni_data = MUNICIPIOS[muni_idx]
    muni_nom  = muni_data["nombre"]

    if _csv_datos and muni_nom in _csv_datos:
        _base = DATOS_TERRITORIALES.get(muni_nom, {})
        _csv  = _csv_datos[muni_nom]
        datos_ter = {**_base, **_csv,
                     "densidad_max": _base.get("densidad_max", 12000),
                     "oms_standard": 9.0,
                     "equip_ideal":  _base.get("equip_ideal", 6.0),
                     "colonias":     _base.get("colonias", [])}
    else:
        datos_ter = DATOS_TERRITORIALES.get(muni_nom, {})

    iarri_val = calc_iarri(muni_data["AV"], muni_data["IC"],
                           muni_data["ED"], muni_data["EAR"], muni_data["IMP"])
    nivel_txt, col_niv = nivel_riesgo(iarri_val)

    # ── Selector de municipio ─────────────────────────────────
    def cambiar_muni(idx):
        state["muni_idx"] = idx
        state["refresh"]()

    chips = ft.Row([
        ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(
                    m["nombre"].split()[0] + (" " + m["nombre"].split()[1]
                     if len(m["nombre"].split()) > 1 else ""),
                    size=11, weight=ft.FontWeight.W_600,
                    color=WHITE if i == muni_idx else MUTED,
                ),
                bgcolor=ACCENT if i == muni_idx else CARD,
                border=ft.border.all(1, ACCENT if i == muni_idx else BORDER),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
            ),
            on_tap=lambda e, i=i: cambiar_muni(i),
        )
        for i, m in enumerate(MUNICIPIOS)
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

    # ── Header ────────────────────────────────────────────────
    pop_fmt = f"{datos_ter.get('poblacion', 0):,}".replace(",", " ")
    perfil_header = ft.Container(
        content=ft.Column([
            ft.Text("PERFIL METABÓLICO AMBIENTAL", size=10,
                    color=MUTED, weight=ft.FontWeight.BOLD, font_family="monospace"),
            chips,
            ft.Container(height=4),
            ft.Row([
                ft.Column([
                    ft.Text(muni_nom, size=18, weight=ft.FontWeight.W_900, color=TEXT),
                    ft.Text(f"👥 {pop_fmt} hab · Puebla, México", size=11, color=MUTED),
                ], spacing=2, expand=True),
                ft.Column([
                    ft.Text(f"{iarri_val:.2f}", size=42,
                            weight=ft.FontWeight.W_900, color=col_niv, height=52),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=6, height=6, border_radius=3, bgcolor=col_niv),
                            ft.Text(f"Riesgo {nivel_txt}", size=10,
                                    color=col_niv, weight=ft.FontWeight.BOLD),
                        ], spacing=4, tight=True),
                        bgcolor=col_niv + "18",
                        border=ft.border.all(1, col_niv + "55"),
                        border_radius=16,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    ),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=8),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=["#e0f2fe", "#ede9fe"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=20,
        padding=18,
        margin=ft.margin.only(bottom=4),
    )

    # ── Coordenadas y POIs ────────────────────────────────────
    _coords = {
        "San Andrés Cholula":      (19.0514, -98.3020),
        "San Pablo Xochimehuacan": (19.0310, -98.2360),
        "Cuautlancingo":           (19.0897, -98.2730),
    }
    _pois = {
        "San Andrés Cholula": [
            {"lat":19.0540,"lon":-98.3060,"tipo":"verde",   "titulo":"Parque Paseo Cholula",    "desc":"Área verde · AV +0.12"},
            {"lat":19.0490,"lon":-98.2980,"tipo":"verde",   "titulo":"Jardines de Zavaleta",     "desc":"Corredor verde · AV +0.08"},
            {"lat":19.0514,"lon":-98.3020,"tipo":"deporte", "titulo":"Unidad Deportiva SAC",    "desc":"Canchas y gimnasio · ED +0.10"},
            {"lat":19.0475,"lon":-98.3040,"tipo":"peatonal","titulo":"Zona Peatonal Centro",    "desc":"Caminabilidad alta · IC +0.15"},
            {"lat":19.0530,"lon":-98.2990,"tipo":"ultra",   "titulo":"Zona Comercial Galerías", "desc":"Ultraprocesados densos"},
        ],
        "San Pablo Xochimehuacan": [
            {"lat":19.0320,"lon":-98.2350,"tipo":"ultra",   "titulo":"Corredor Comercial",      "desc":"Tiendas · EAR +0.18"},
            {"lat":19.0290,"lon":-98.2380,"tipo":"verde",   "titulo":"Área verde escasa",       "desc":"Solo 2.8 m²/hab"},
            {"lat":19.0310,"lon":-98.2340,"tipo":"deporte", "titulo":"Campo Municipal",         "desc":"ED básico"},
        ],
        "Cuautlancingo": [
            {"lat":19.0920,"lon":-98.2750,"tipo":"ultra",   "titulo":"Corredor OXXO/7Eleven",   "desc":"EAR +0.22"},
            {"lat":19.0880,"lon":-98.2710,"tipo":"ultra",   "titulo":"Zona Industrial",         "desc":"Ultraprocesados"},
            {"lat":19.0897,"lon":-98.2730,"tipo":"deporte", "titulo":"Campo Municipal",         "desc":"ED 0.08"},
            {"lat":19.0870,"lon":-98.2760,"tipo":"verde",   "titulo":"Área verde crítica",      "desc":"Solo 1.1 m²/hab"},
        ],
    }
    _tipos_poi = {
        "verde":    {"color": "#22c55e", "emoji": "🌳"},
        "deporte":  {"color": "#8b5cf6", "emoji": "⚽"},
        "peatonal": {"color": "#0ea5e9", "emoji": "🚶"},
        "ultra":    {"color": "#ef4444", "emoji": "🍟"},
    }

    lat_c, lon_c = _coords.get(muni_nom, (19.05, -98.26))

    # ════════════════════════════════════════════════════════
    # INTENTO 1: flet_map embebido (funciona en todos lados)
    # ════════════════════════════════════════════════════════
    mapa_widget = None
    _ftm = None

    try:
        import flet_map as _ftm
    except ImportError:
        try:
            import flet.map as _ftm
        except ImportError:
            _ftm = None

    if _ftm is not None:
        try:
            # Construir marcadores para todos los municipios
            _markers = []
            _circles = []

            for _m in MUNICIPIOS:
                _iv = calc_iarri(_m["AV"], _m["IC"], _m["ED"], _m["EAR"], _m["IMP"])
                _nv, _cv = nivel_riesgo(_iv)
                _mlat, _mlon = _coords.get(_m["nombre"], (lat_c, lon_c))
                _activo = _m["nombre"] == muni_nom

                # Etiqueta del municipio
                _markers.append(_ftm.Marker(
                    coordinates=_ftm.MapLatitudeLongitude(_mlat, _mlon),
                    content=ft.Tooltip(
                        message=f"{_m['nombre']}\nIARRI: {_iv:.2f} — Riesgo {_nv}",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(_m["nombre"].split()[0], size=9,
                                        color=WHITE, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{_iv:.2f}", size=13,
                                        color=WHITE, weight=ft.FontWeight.W_900),
                            ], spacing=0,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=_cv,
                            padding=ft.padding.symmetric(horizontal=8, vertical=5),
                            border_radius=10,
                            border=ft.border.all(2 if _activo else 0, WHITE),
                            shadow=ft.BoxShadow(blur_radius=8, color="#00000066"),
                        ),
                    ),
                ))

                # Zona de riesgo como CircleMarker
                _circles.append(_ftm.CircleMarker(
                    coordinates=_ftm.MapLatitudeLongitude(_mlat, _mlon),
                    radius=700 + _iv * 1800,
                    use_radius_in_meter=True,
                    color=_cv,
                    fill_color=_cv,
                    fill_opacity=0.15,
                    border_stroke_width=2,
                    border_color=_cv,
                ))

            # POIs del municipio activo
            for _poi in _pois.get(muni_nom, []):
                _t = _tipos_poi.get(_poi["tipo"], {"color":"#888","emoji":"📍"})
                _markers.append(_ftm.Marker(
                    coordinates=_ftm.MapLatitudeLongitude(_poi["lat"], _poi["lon"]),
                    content=ft.Tooltip(
                        message=f"{_poi['titulo']}\n{_poi['desc']}",
                        content=ft.Container(
                            content=ft.Text(_t["emoji"], size=16),
                            bgcolor=_t["color"] + "DD",
                            width=30, height=30,
                            border_radius=15,
                            alignment=ft.alignment.Alignment(0, 0),
                            border=ft.border.all(1, WHITE),
                        ),
                    ),
                ))

            mapa_widget = ft.Column([
                _ftm.Map(
                    height=300,
                    initial_center=_ftm.MapLatitudeLongitude(lat_c, lon_c),
                    initial_zoom=12.5,
                    layers=[
                        _ftm.TileLayer(
                            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                            user_agent_package_name="arq_metabolica_mx",
                        ),
                        _ftm.CircleLayer(circles=_circles),
                        _ftm.MarkerLayer(markers=_markers),
                    ],
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MAP_ROUNDED, size=13, color=MUTED),
                        ft.Text("OpenStreetMap · toca un marcador para ver datos",
                                size=10, color=MUTED, italic=True),
                        ft.Container(expand=True),
                        ft.Text("OSM Contributors", size=9, color=MUTED, italic=True),
                    ], spacing=6),
                    padding=ft.padding.symmetric(horizontal=8, vertical=5),
                ),
            ], spacing=0)

        except Exception as _ex:
            print(f"[mapa] flet_map error: {_ex}")
            mapa_widget = None

    # ════════════════════════════════════════════════════════
    # INTENTO 2: Mapa HTML en navegador (fallback Desktop)
    # ════════════════════════════════════════════════════════
    if mapa_widget is None:
        _munis_js = []
        for _m in MUNICIPIOS:
            _iv = calc_iarri(_m["AV"], _m["IC"], _m["ED"], _m["EAR"], _m["IMP"])
            _nv, _cv = nivel_riesgo(_iv)
            _mlat, _mlon = _coords.get(_m["nombre"], (lat_c, lon_c))
            _munis_js.append({
                "nombre": _m["nombre"], "lat": _mlat, "lon": _mlon,
                "iarri": round(_iv,3), "nivel": _nv, "color": _cv,
                "AV":_m["AV"],"IC":_m["IC"],"ED":_m["ED"],
                "EAR":_m["EAR"],"IMP":_m["IMP"],
                "pois": _pois.get(_m["nombre"],[]),
            })
        _mj = _json.dumps(_munis_js, ensure_ascii=False)
        _tj = _json.dumps(_tipos_poi, ensure_ascii=False)

        _html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{height:100%;font-family:sans-serif}}
#map{{height:100vh;width:100vw}}
#panel{{position:absolute;top:10px;right:10px;z-index:1000;background:rgba(15,23,42,.93);
border-radius:14px;padding:12px 14px;width:185px;border:1px solid #334155;
color:#e2e8f0;max-height:80vh;overflow-y:auto}}
#panel h3{{font-size:11px;color:#38bdf8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase}}
.mi{{padding:6px 0;border-bottom:1px solid #1e293b;cursor:pointer}}
.mi:last-child{{border-bottom:none}}.mn{{font-size:11px;font-weight:600}}
.mv{{font-size:14px;font-weight:900}}.ml{{font-size:10px;color:#64748b}}
.leaflet-popup-content-wrapper{{background:#0f172a;border:1px solid #334155;
border-radius:12px;color:#e2e8f0}}
.leaflet-popup-tip{{background:#0f172a}}
.pt{{font-size:13px;font-weight:700;color:#38bdf8;margin-bottom:4px}}
.pi{{font-size:24px;font-weight:900;margin:2px 0}}
.ps{{font-size:11px;color:#64748b}}
.pv{{display:flex;justify-content:space-between;font-size:11px;margin:2px 0}}
.pb{{background:#1e293b;border-radius:3px;height:5px;width:100%;margin-top:2px}}
.pf{{height:5px;border-radius:3px}}
</style></head><body>
<div id="map"></div>
<div id="panel"><h3>IARRI Municipal</h3><div id="lm"></div></div>
<script>
const MU={_mj};const TI={_tj};
const map=L.map('map',{{center:[{lat_c},{lon_c}],zoom:13}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'OpenStreetMap',maxZoom:19}}).addTo(map);
function popM(m){{
  const vs=[{{k:'AV',l:'Areas Verdes',i:'🌳',inv:true}},
    {{k:'IC',l:'Caminabilidad',i:'🚶',inv:true}},
    {{k:'ED',l:'Equip Dep',i:'⚽',inv:true}},
    {{k:'EAR',l:'Entorno Alim',i:'🍟',inv:false}},
    {{k:'IMP',l:'Marginacion',i:'📉',inv:false}}];
  const f=vs.map(v=>{{const val=m[v.k],r=v.inv?(1-val):val,
    c=r<.33?'#22c55e':r<.66?'#f59e0b':'#ef4444';
    return `<div class="pv"><span>${{v.i}} ${{v.l}}</span>
    <span style="color:${{c}};font-weight:700">${{val.toFixed(2)}}</span></div>
    <div class="pb"><div class="pf" style="width:${{val*100}}%;background:${{c}}"></div></div>`;}}).join('');
  return `<div style="min-width:185px"><div class="pt">${{m.nombre}}</div>
    <div class="pi" style="color:${{m.color}}">${{m.iarri.toFixed(2)}}</div>
    <div class="ps">Riesgo ${{m.nivel}} · Prob RI ${{(10+50*m.iarri).toFixed(0)}}%</div>
    <div style="margin-top:8px;border-top:1px solid #1e293b;padding-top:6px">${{f}}</div></div>`;}}
function icoP(tipo){{const c=TI[tipo]||{{color:'#888',emoji:'📍'}};
  return L.divIcon({{html:`<div style="background:${{c.color}};width:28px;height:28px;
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.5)">${{c.emoji}}</div>`,
    className:'',iconSize:[28,28],iconAnchor:[14,14]}});}}
const lm=document.getElementById('lm');
MU.forEach(m=>{{
  L.circle([m.lat,m.lon],{{radius:700+m.iarri*1800,color:m.color,fillColor:m.color,fillOpacity:.15,weight:2}})
    .bindPopup(popM(m),{{maxWidth:260}}).addTo(map);
  const ico=L.divIcon({{html:`<div style="background:${{m.color}};padding:3px 8px;
    border-radius:8px;font-size:11px;font-weight:700;color:#000;
    box-shadow:0 2px 10px rgba(0,0,0,.4);white-space:nowrap">
    ${{m.nombre.split(' ')[0]}} ${{m.iarri.toFixed(2)}}</div>`,className:'',iconAnchor:[45,12]}});
  L.marker([m.lat,m.lon],{{icon:ico}}).bindPopup(popM(m),{{maxWidth:260}}).addTo(map);
  (m.pois||[]).forEach(p=>{{
    L.marker([p.lat,p.lon],{{icon:icoP(p.tipo)}})
      .bindPopup(`<div style="min-width:145px"><b style="color:#38bdf8">${{p.titulo}}</b><br>
        <span style="font-size:11px;color:#64748b">${{p.desc}}</span></div>`,{{maxWidth:220}}).addTo(map);}});
  const d=document.createElement('div');d.className='mi';
  d.innerHTML=`<div class="mn">${{m.nombre}}</div>
    <div class="mv" style="color:${{m.color}}">${{m.iarri.toFixed(2)}}</div>
    <div class="ml">Riesgo ${{m.nivel}}</div>`;
  d.onclick=()=>map.flyTo([m.lat,m.lon],14,{{duration:1}});lm.appendChild(d);}});
</script></body></html>"""

        _ruta = _os2.path.abspath("mapa_arq.html")
        with open(_ruta, "w", encoding="utf-8") as _fh:
            _fh.write(_html)

        import webbrowser as _wb
        def _abrir(e=None):
            _wb.open(f"file:///{_ruta.replace(_os2.sep, '/')}")

        # Detectar si estamos en web
        _es_web = getattr(page, "web", False)

        if _es_web:
            mapa_widget = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WEB_ROUNDED, size=36, color=ACCENT),
                    ft.Text("Mapa en ejecución en web", size=14,
                            weight=ft.FontWeight.W_600, color=TEXT),
                    ft.Text("Instala flet-map para ver el mapa aquí:\npip install flet-map",
                            size=11, color=MUTED, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.Alignment(0, 0),
                height=180,
                bgcolor=ACCENT + "08",
                border=ft.border.all(1, ACCENT + "33"),
                border_radius=16,
            )
        else:
            mapa_widget = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("🗺️  Mapa Interactivo IARRI", size=13,
                                weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text("Instala flet-map para ver aquí, o abre en navegador:",
                                size=10, color=MUTED),
                        ft.Text("pip install flet-map", size=10,
                                color=ACCENT, font_family="monospace"),
                    ], spacing=3, expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.OPEN_IN_BROWSER_ROUNDED, color=WHITE, size=16),
                            ft.Text("Abrir mapa", size=12,
                                    weight=ft.FontWeight.BOLD, color=WHITE),
                        ], spacing=6, tight=True),
                        on_click=_abrir,
                        style=ft.ButtonStyle(
                            bgcolor=ACCENT,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        ),
                    ),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ACCENT + "10",
                border=ft.border.all(1, ACCENT + "44"),
                border_radius=14, padding=14,
            )

    # ── Leyenda ───────────────────────────────────────────────
    leyenda = ft.Row([
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=LOW),
                ft.Text("Bajo",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=MID),
                ft.Text("Medio",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=HIGH),
                ft.Text("Alto",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Text("🌳",size=11),ft.Text("🚶",size=11),
                ft.Text("⚽",size=11),ft.Text("🍟",size=11)]),
        ft.Text("OSM · INEGI 2020",size=9,color=MUTED,italic=True),
    ], spacing=10, wrap=True)

    # ── Mini-mapa de barras (siempre visible) ─────────────────
    def _mini():
        rows = []
        for _m in MUNICIPIOS:
            _iv = calc_iarri(_m["AV"],_m["IC"],_m["ED"],_m["EAR"],_m["IMP"])
            _nv, _cv = nivel_riesgo(_iv)
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(_m["nombre"].split()[0], size=9,
                                    weight=ft.FontWeight.BOLD, color=_cv),
                            ft.Text(f"{_iv:.2f}", size=13,
                                    weight=ft.FontWeight.W_900, color=_cv),
                        ], spacing=1,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=_cv+"20", border=ft.border.all(1,_cv+"66"),
                        border_radius=10, padding=8, width=70,
                    ),
                    ft.Column([
                        *[ft.Row([
                            ft.Text(_ico, size=10),
                            ft.Container(
                                content=ft.Container(bgcolor=_vc,border_radius=2,
                                                     height=5,width=_vv*130),
                                bgcolor=BORDER,border_radius=2,height=5,
                                width=130,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            ),
                            ft.Text(f"{_vv:.2f}",size=9,color=_vc,
                                    width=26,text_align=ft.TextAlign.RIGHT),
                        ],spacing=4)
                        for _ico,_key,_inv in [("🌳","AV",True),("🚶","IC",True),
                                               ("⚽","ED",True),("🍟","EAR",False)]
                        for _vv in [_m[_key]]
                        for _vc in [LOW if (_vv if not _inv else 1-_vv)<0.33
                                    else MID if (_vv if not _inv else 1-_vv)<0.66
                                    else HIGH]
                        ],
                    ], spacing=3, expand=True),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD, border=ft.border.all(1,_cv+"33"),
                border_radius=14, padding=10,
                margin=ft.margin.only(bottom=6),
                shadow=ft.BoxShadow(blur_radius=4,color="#0000000a",offset=ft.Offset(0,1)),
            ))
        return rows

    # ── Variables territoriales ───────────────────────────────
    def _var_card(icon,titulo,valor_str,sub,pct,color,nota_izq="",nota_der=""):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(icon,size=20),bgcolor=color+"20",
                                 border_radius=10,width=38,height=38,
                                 alignment=ft.alignment.Alignment(0,0)),
                    ft.Column([ft.Text(titulo,size=11,weight=ft.FontWeight.W_600,color=TEXT),
                               ft.Text(sub,size=10,color=MUTED)],spacing=1,expand=True),
                    ft.Text(valor_str,size=18,weight=ft.FontWeight.W_900,color=color),
                ],spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Container(bgcolor=color,border_radius=4,height=7,
                                         width=max(4,min(1.0,pct))*300),
                    bgcolor=BORDER,border_radius=4,height=7,
                    expand=True,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Row([ft.Text(nota_izq,size=9,color=MUTED),
                        ft.Container(expand=True),
                        ft.Text(nota_der,size=9,color=MUTED)]),
            ],spacing=2),
            bgcolor=CARD, border=ft.border.all(1,color+"44"),
            border_radius=16, padding=14,
            shadow=ft.BoxShadow(blur_radius=6,color="#0000000a",offset=ft.Offset(0,1)),
            margin=ft.margin.only(bottom=10),
        )

    av_m2    = datos_ter.get("areas_verdes_m2",0)
    av_pct   = av_m2/datos_ter.get("oms_standard",9.0)
    av_col   = LOW if av_pct>=0.8 else MID if av_pct>=0.4 else HIGH
    dens     = datos_ter.get("densidad_pob",0)
    dens_pct = dens/datos_ter.get("densidad_max",12000)
    dens_col = HIGH if dens_pct>=0.8 else MID if dens_pct>=0.5 else LOW
    marg     = datos_ter.get("marginacion",0)
    marg_col = HIGH if marg>=0.6 else MID if marg>=0.3 else LOW
    equip    = datos_ter.get("equipamiento_dep",0)
    equip_pct= equip/datos_ter.get("equip_ideal",6.0)
    equip_col= LOW if equip_pct>=0.6 else MID if equip_pct>=0.3 else HIGH
    movil    = datos_ter.get("movilidad_peat",0)
    movil_col= LOW if movil>=0.6 else MID if movil>=0.35 else HIGH
    ultra    = datos_ter.get("tiendas_ultra",0)
    ultra_col= HIGH if ultra>=0.6 else MID if ultra>=0.4 else LOW

    # ── Ranking ───────────────────────────────────────────────
    munis_sorted = sorted(
        [{**_m,"iarri":calc_iarri(_m["AV"],_m["IC"],_m["ED"],_m["EAR"],_m["IMP"])}
         for _m in MUNICIPIOS], key=lambda x:x["iarri"])
    rank_rows = []
    for _i,_m in enumerate(munis_sorted):
        _nv,_cv = nivel_riesgo(_m["iarri"])
        rank_rows.append(ft.Container(
            content=ft.Row([
                ft.Text(f"#{_i+1}",size=16,weight=ft.FontWeight.W_900,color=MUTED,width=28),
                ft.Column([
                    ft.Text(_m["nombre"],size=12,weight=ft.FontWeight.W_600,color=TEXT),
                    ft.Container(
                        content=ft.Container(bgcolor=_cv,border_radius=3,height=5,
                                             width=_m["iarri"]*200),
                        bgcolor=BORDER,border_radius=3,height=5,
                        expand=True,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        margin=ft.margin.only(top=4),
                    ),
                ],spacing=2,expand=True),
                ft.Column([
                    ft.Text(f"{_m['iarri']:.2f}",size=16,
                            weight=ft.FontWeight.W_900,color=_cv),
                    ft.Text(f"Prob RI {prob_ri(_m['iarri'])*100:.0f}%",
                            size=9,color=MUTED),
                ],spacing=0,horizontal_alignment=ft.CrossAxisAlignment.END),
            ],spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD,border=ft.border.all(1,_cv+"33"),
            border_radius=14,padding=14,
            margin=ft.margin.only(bottom=8),
            shadow=ft.BoxShadow(blur_radius=4,color="#0000000a",offset=ft.Offset(0,1)),
        ))

    # ── Layout final ──────────────────────────────────────────
    return ft.Column([
        perfil_header,
        ft.Container(height=10),
        ft.Container(
            content=mapa_widget,
            border=ft.border.all(1, BORDER),
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=6,color="#0000000a",offset=ft.Offset(0,2)),
        ),
        ft.Container(height=6),
        leyenda,
        ft.Container(height=14),
        titulo_seccion("COMPARATIVA RÁPIDA"),
        ft.Container(height=6),
        *_mini(),
        ft.Container(height=14),
        titulo_seccion("VARIABLES TERRITORIALES — INEGI / DENUE / CONAPO"),
        ft.Container(height=8),
        _var_card("🌳","Acceso a Áreas Verdes",f"{av_m2} m²/hab",
                  "OMS: 9 m²/hab",av_pct,av_col,"0 m²",
                  f"OMS 9 m² {'✓' if av_pct>=1 else '✗'}"),
        _var_card("🏘️","Densidad Poblacional",f"{dens:,}/km²".replace(",","  "),
                  "INEGI Censo 2020",dens_pct,dens_col,"Baja","Alta"),
        _var_card("📉","Índice de Marginación",f"{marg:.2f}",
                  "CONAPO",marg,marg_col,"Sin marginación","Muy alto"),
        _var_card("⚽","Equipamiento Deportivo",f"{equip}/10k hab",
                  "Instalaciones activas",equip_pct,equip_col,"0",
                  f"Ideal: {datos_ter.get('equip_ideal',6)}/10k"),
        _var_card("🚶","Movilidad Peatonal",f"{movil*100:.0f}%",
                  "Banquetas en buen estado",movil,movil_col,"0%","100%"),
        _var_card("🍟","Entorno Alimentario Riesgoso",f"{ultra*100:.0f}%",
                  "Ultraprocesados/total DENUE",ultra,ultra_col,"Sin riesgo","100%"),
        titulo_seccion("RANKING MUNICIPAL"),
        ft.Container(height=8),
        *rank_rows,
        ft.Container(height=28),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)



# ═══════════════════════════════════════════════════════════
#  PANTALLA 3 — CALCULADORA IARRI
# ═══════════════════════════════════════════════════════════
def build_calculadora(page, state):
    # Bloqueo invitado
    if state.get("es_invitado"):
        def _ir_reg():
            state.get("logout", lambda: None)()
        _dialogo_registro(page, _ir_reg)
        return _pantalla_bloqueada(
            "🧮 Calculadora IARRI",
            "Calcula el índice de riesgo de tu municipio.",
            lambda: state.get("logout", lambda: None)(),
        )

    slider_vals = {v["key"]: state.get(f"slider_{v['key']}", 0.5) for v in VARIABLES}

    result_txt   = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    nivel_txt    = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)
    prob_txt     = ft.Text("Prob. RI: —", size=12, color=MUTED)
    guardar_btn_txt = ft.Text("💾  Guardar Resultado", size=13,
                               weight=ft.FontWeight.BOLD, color=WHITE)
    #mc_resultado = ft.Column([], visible=False)
    mc_btn_txt   = ft.Text("⚡  Simulación Monte Carlo (1000 iter.)", size=13,
                            weight=ft.FontWeight.BOLD, color=WHITE)
    
    #Barras de desglose — reactivas a cada cambio de slider
    MAX_CONTRIB = 0.25   # peso máximo posible por variable (IC y EAR)
    BAR_MAX_PX  = 200    # píxeles que representa MAX_CONTRIB

    # Barras de desglose
    desglose_bars = {}
    desglose_rows = []
    for v in VARIABLES:
        bar_inner = ft.Container(bgcolor=v["color"], border_radius=3,height=8, width=4)
        bar_track = ft.Container(
            content=bar_inner,bgcolor=BORDER, border_radius=3, height=8,
            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=42,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace",weight=ft.FontWeight.BOLD)
        pct_lbl = ft.Text("0.0%", size=9, color=MUTED, width=28,
                           text_align=ft.TextAlign.RIGHT)
        desglose_bars[v["key"]] = (bar_inner, val_lbl,pct_lbl)
        desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=36,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_track,
                val_lbl,
                pct_lbl,

            ], spacing=6)
        )

    def actualizar_resultado():
        iarri = calc_iarri(**slider_vals)
        niv, col = nivel_riesgo(iarri)
        pr = prob_ri(iarri)
        result_txt.value = f"{iarri:.4f}"
        result_txt.color = col
        nivel_txt.value  = f"● Riesgo {niv}"
        nivel_txt.color  = col
        prob_txt.value   = f"Prob. RI: {pr*100:.1f}%"
        prob_txt.color   = col
        # Desglose
        contribs = {
            "AV":  WEIGHTS["AV"]  * (1 - slider_vals["AV"]),
            "IC":  WEIGHTS["IC"]  * (1 - slider_vals["IC"]),
            "ED":  WEIGHTS["ED"]  * (1 - slider_vals["ED"]),
            "EAR": WEIGHTS["EAR"] * slider_vals["EAR"],
            "IMP": WEIGHTS["IMP"]  * slider_vals["IMP"], #impportante
        }
        total_contrib = max(sum(contribs.values()),0.001) #cambio en las barras con lo del
        for k, (bar, lbl, pct) in desglose_bars.items():
            c = contribs[k] 
            bar.width = max(4, (c / MAX_CONTRIB) * BAR_MAX_PX)
            lbl.value = f"{c:.3f}"
            pct.value = f"{c /total_contrib*100:.1f}%"
        page.update()

    # Sliders
    slider_val_lbls = {}
    slider_widgets = []

    for v in VARIABLES:
        slider_val_lbl = ft.Text(f"{slider_vals[v['key']]:.2f}", size=15,
                                  weight=ft.FontWeight.W_900, color=v["color"], width=44)
        s = ft.Slider(
            min=0, max=1, divisions=100,
            value=slider_vals[v["key"]],
            active_color=v["color"],
            inactive_color=BORDER,
            thumb_color=v["color"],
            on_change=None,
            expand=True,
        )
        slider_widgets.append((v["key"], slider_val_lbl, s))
        slider_val_lbls[v["key"]] = slider_val_lbl

    for key, lbl, s in slider_widgets:
        def make_change(k):
            def on_change(e):
                slider_vals[k] = e.control.value
                state[f"slider_{k}"] = e.control.value
                slider_val_lbls[k].value = f"{e.control.value:.2f}"
                actualizar_resultado()
            return on_change
        s.on_change = make_change(key)

    origen_txt = ft.Text("", size=11, color=MUTED, italic=True)

    encuesta_w = build_encuesta(page, lambda r: None)
    encuesta_card = ft.Container(content=encuesta_w, visible=False)

    def aplicar_valorslider(nuevos_valores: dict, origen: str = ""):
        for k, valor in nuevos_valores.items():
            slider_vals[k] = valor
            state[f"slider_{k}"] = valor
            slider_val_lbls[k].value = f"{valor:.2f}"
            for key2, lbl2, s2 in slider_widgets:
                if key2 == k:
                    s2.value = valor
                    lbl2.value = f"{valor:.2f}"
        if origen:
            origen_txt.value = f"Valores cargados desde {origen}"
            origen_txt.color = ACCENT
        actualizar_resultado()

    def encuesta_completa(respuestas: dict):
        encuesta_card.visible = False
        aplicar_valorslider(respuestas, "Encuesta")
            
    def set_preset(idx):
        m = MUNICIPIOS[idx]
        for v in VARIABLES:
            slider_vals[v["key"]] = m[v["key"]]
            state[f"slider_{v['key']}"] = m[v["key"]]
        for k, lbl, s in slider_widgets:
            lbl.value = f"{slider_vals[k]:.2f}"
            s.value   = slider_vals[k]
        actualizar_resultado()

    # Crear botones presets
    preset_names = ["San Andrés", "San Pablo Xochimehuacan", "Cuautlancingo"]
    preset_buttons = []
    for i, m in enumerate(MUNICIPIOS):
        def make_on_click(idx):
            return lambda e: set_preset(idx)
        preset_buttons.append(
            ft.FilledTonalButton(
                preset_names[i] if i < len(preset_names) else m["nombre"].split()[0],
                on_click=make_on_click(i),
                style=ft.ButtonStyle(bgcolor=CARD, color=TEXT),
            )
        )
    preset_buttons.append(
        ft.FilledTonalButton(
            "",
            on_click=lambda e: None,
            style=ft.ButtonStyle(bgcolor=CARD, color=TEXT),
        )
    )

    presets_row = ft.Row(preset_buttons, spacing=8, scroll=ft.ScrollMode.AUTO)
    
    toggle_btn_txt = ft.Text("Llenar desde encuesta", size=13, weight=ft.FontWeight.BOLD, color=WHITE)

    def togg_encuesta(e):
        encuesta_card.visible = not encuesta_card.visible
        toggle_btn_txt.value = (
            "Ocultar encuesta" if encuesta_card.visible
            else "Llenar desde encuesta"
        )
        page.update()
    # Tarjetas slider
    slider_cards = []
    for v, (key, val_lbl, s) in zip(VARIABLES, slider_widgets):
        card = tarjeta(ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text(v["icon"], size=15),
                        bgcolor=v["color"]+"22", border_radius=8,
                        width=30, height=30, alignment=ft.alignment.Alignment(0,0),
                    ),
                    ft.Column([
                        ft.Text(v["label"], size=13, weight=ft.FontWeight.W_600, color=TEXT),
                        ft.Text(v["desc"], size=10, color=MUTED),
                    ], spacing=1),
                ], spacing=8, expand=True),
                val_lbl,
            ]),
            s,
            ft.Row([
                ft.Text("0.0", size=9, color=MUTED),
                ft.Container(expand=True),
                ft.Text("0.5", size=9, color=MUTED),
                ft.Container(expand=True),
                ft.Text("1.0", size=9, color=MUTED),
            ]),
            #ft.Text("protector ↓" if v["inv"] else "riesgo ↑",
                    #size=9, color=v["color"], italic=True),
        ], spacing=2), padding=14)
        slider_cards.append(card)

    def guardar_resultado(e):
        """Guarda el resultado en el state y cambia a pestaña de intervención."""
        guardar_btn_txt.value = "⏳  Guardando..."
        page.update()

        def _task():
            try:
                iarri = calc_iarri(**slider_vals)
                nivel, col = nivel_riesgo(iarri)
                pr = prob_ri(iarri)

                muni_idx = state.get("muni_idx", 0)
                # Guardar resultado del municipio actual en el estado compartido
                if "resultados_municipios" not in state:
                    state["resultados_municipios"] = {}
                state["resultados_municipios"][muni_idx] = {
                    "municipio_id": muni_idx + 1,
                    "AV":  slider_vals["AV"],
                    "IC":  slider_vals["IC"],
                    "ED":  slider_vals["ED"],
                    "EAR": slider_vals["EAR"],
                    "IMP": slider_vals["IMP"],
                    "iarri": iarri,
                    "nivel": nivel,
                    "prob":  pr,
                }

                def cerrar_dialogo(e=None):
                    dlg.open = False
                    page.update()
                    # Cambiar a pestaña de Intervención (índice 3)
                    state.get("_switch_tab", lambda x: None)(3)

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("✅ Resultado Guardado", weight=ft.FontWeight.BOLD, color=LOW),
                    content=ft.Column([
                        ft.Text(
                            "Tu cálculo de IARRI se ha guardado correctamente.",
                            size=13,
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Valor IARRI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{iarri:.4f}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Nivel de Riesgo:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"● {nivel}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Probabilidad RI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{pr*100:.1f}%", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                            ], spacing=6),
                            bgcolor=CARD,
                            border=ft.border.all(1, col + "44"),
                            border_radius=12,
                            padding=12,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Se procederá a la pestaña de Intervención para ver recomendaciones y su intervencion.",
                            size=12, color=MUTED, italic=True,
                        ),
                    ], spacing=8),
                    actions=[
                        ft.ElevatedButton(
                            "Ir a Intervención",
                            on_click=cerrar_dialogo,
                            style=ft.ButtonStyle(
                                bgcolor=ACCENT, color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            except Exception as ex:
                print(f"[ERROR] guardar_resultado: {ex}")
                dlg_err = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("❌ Error", weight=ft.FontWeight.BOLD, color=HIGH),
                    content=ft.Text(f"Hubo un error al guardar: {str(ex)}", size=13),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: (setattr(dlg_err, 'open', False), page.update())),
                    ],
                )
                page.overlay.append(dlg_err)
                dlg_err.open = True
                page.update()
            finally:
                guardar_btn_txt.value = "💾  Guardar Resultado"
                page.update()

        threading.Thread(target=_task, daemon=True).start()

    # Resultado card
    resultado_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("IARRI Calculado", size=11, color=MUTED),
                    result_txt,
                ]),
                ft.Column([
                    ft.Text("Nivel de Riesgo", size=11, color=MUTED),
                    nivel_txt,
                    prob_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.END),
            ft.Divider(height=1, color=BORDER),
            ft.Text("Desglose de Contribuciones", size=11, color=MUTED),
            *desglose_rows,
            ft.Divider(height=1, color=BORDER),
            ft.Row([
                ft.ElevatedButton(
                    content=mc_btn_txt,
                    bgcolor=ACCENT,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46,
                    expand=True,
                    on_click=lambda e: run_mc(e),
                ),
                ft.ElevatedButton(
                    content=guardar_btn_txt,
                    bgcolor=ACCENT3,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46,
                    expand=True,
                    on_click=guardar_resultado,
                ),
            ], spacing=8),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1,-1),
            end=ft.alignment.Alignment(1,1),
            colors=["#e0f2fe", "#ede9fe"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    # Monte Carlo
    mc_mean_txt = ft.Text("", size=12, color=ACCENT, font_family="monospace")
    mc_std_txt  = ft.Text("", size=12, color=ACCENT3, font_family="monospace")
    mc_ci_txt   = ft.Text("", size=12, color=MID, font_family="monospace")
    mc_hist     = ft.Row([], spacing=2, height=80,
                          vertical_alignment=ft.CrossAxisAlignment.END)

    mc_card = ft.Container(
        content=ft.Column([
            ft.Text("📊 Monte Carlo — 1000 simulaciones", size=13,
                    weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Text("σ = ±0.12 perturbación aleatoria por variable",
                    size=10, color=MUTED),
            mc_hist,
            ft.Row([ft.Text("0.0",size=9,color=MUTED), ft.Container(expand=True),
                    ft.Text("0.5",size=9,color=MUTED), ft.Container(expand=True),
                    ft.Text("1.0",size=9,color=MUTED)]),
            mc_mean_txt, mc_std_txt, mc_ci_txt,
        ], spacing=8),
        bgcolor=CARD, border=ft.border.all(1,BORDER),
        border_radius=16, padding=16,
        visible=False,
    )
    
    def guardar_resultado(e):
        """Guarda el resultado en el state y cambia a pestaña de intervención."""
        guardar_btn_txt.value = "⏳  Guardando..."
        page.update()

        def _task():
            try:
                iarri = calc_iarri(**slider_vals)
                nivel, col = nivel_riesgo(iarri)
                pr = prob_ri(iarri)

                muni_idx = state.get("muni_idx", 0)
                # Guardar resultado del municipio actual en el estado compartido
                if "resultados_municipios" not in state:
                    state["resultados_municipios"] = {}
                state["resultados_municipios"][muni_idx] = {
                    "municipio_id": muni_idx + 1,
                    "AV":  slider_vals["AV"],
                    "IC":  slider_vals["IC"],
                    "ED":  slider_vals["ED"],
                    "EAR": slider_vals["EAR"],
                    "IMP": slider_vals["IMP"],
                    "iarri": iarri,
                    "nivel": nivel,
                    "prob":  pr,
                }

                def cerrar_dialogo(e=None):
                    dlg.open = False
                    page.update()
                    # Cambiar a pestaña de Intervención (índice 3)
                    state.get("_switch_tab", lambda x: None)(3)

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("✅ Resultado Guardado", weight=ft.FontWeight.BOLD, color=LOW),
                    content=ft.Column([
                        ft.Text(
                            "Tu cálculo de IARRI se ha guardado correctamente.",
                            size=13,
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Valor IARRI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{iarri:.4f}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Nivel de Riesgo:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"● {nivel}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Probabilidad RI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{pr*100:.1f}%", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                            ], spacing=6),
                            bgcolor=CARD,
                            border=ft.border.all(1, col + "44"),
                            border_radius=12,
                            padding=12,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Se procederá a la pestaña de Intervención para ver recomendaciones y su intervencion.",
                            size=12, color=MUTED, italic=True,
                        ),
                    ], spacing=8),
                    actions=[
                        ft.ElevatedButton(
                            "Ir a Intervención",
                            on_click=cerrar_dialogo,
                            style=ft.ButtonStyle(
                                bgcolor=ACCENT, color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            except Exception as ex:
                print(f"[ERROR] guardar_resultado: {ex}")
                dlg_err = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("❌ Error", weight=ft.FontWeight.BOLD, color=HIGH),
                    content=ft.Text(f"Hubo un error al guardar: {str(ex)}", size=13),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: (setattr(dlg_err, 'open', False), page.update())),
                    ],
                )
                page.overlay.append(dlg_err)
                dlg_err.open = True
                page.update()
            finally:
                guardar_btn_txt.value = "💾  Guardar Resultado"
                page.update()

    
    def run_mc(e):
        mc_btn_txt.value = "⏳  Calculando..."
        page.update()

        def _task():
            res, media, desv, ci_lo, ci_hi = monte_carlo(slider_vals, 1000, 0.12)
            # histograma 20 bins
            counts, _ = np.histogram(res, bins=20, range=(0,1))
            max_c = counts.max()
            mc_hist.controls = []
            for i, c in enumerate(counts):
                h = max(2, int(c / max_c * 76))
                left = i / 20
                col_bar = LOW if left < 0.33 else (MID if left < 0.66 else HIGH)
                mc_hist.controls.append(
                    ft.Container(
                        bgcolor=ACCENT if abs(left - media) < 0.05 else col_bar,
                        border_radius=ft.border_radius.only(top_left=2, top_right=2),
                        height=h, expand=True, opacity=0.85,
                    )
                )
            mc_mean_txt.value = f"Promedio: {media:.4f}"
            mc_std_txt.value  = f"Desv. Est: {desv:.4f}"
            mc_ci_txt.value   = f"IC 95%: [{ci_lo:.3f}, {ci_hi:.3f}]"
            mc_card.visible   = True
            mc_btn_txt.value  = "⚡  Simulación Monte Carlo (1000 iter.)"
            page.update()

        threading.Thread(target=_task, daemon=True).start()

    actualizar_resultado()

    return ft.Column([
        titulo_seccion("Calculadora sobre Municipio"),
        ft.Container(height=6),
        presets_row,
        ft.Container(height=8),
        tarjeta(ft.Text(
            "Instrucciones: Modifique las barras deslizantes para ajustar su indice y obtener la precision posible.",
            size=12, color=ACCENT, font_family="monospace",
        )),
        ft.Container(height=10),
        titulo_seccion("Indice Arquitectonico de Riesgo"),
        ft.Container(height=10),
        *slider_cards,
        ft.Container(height=10),
        resultado_card,
        ft.Container(height=10),
        mc_card,
        ft.Container(height=20),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 4 — RECOMENDACIONES + GAMIFICACIÓN
# ═══════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════
#  TEST DE SÍNTOMAS — RESISTENCIA A LA INSULINA
# ═══════════════════════════════════════════════════════════

PREGUNTAS_TEST = [
    # Síntomas físicos
    {"texto": "¿Sientes cansancio frecuente después de comer?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí, me pasa seguido",      "resp_no": "No, me siento bien"},
    {"texto": "¿Tienes antojos intensos de azúcar o carbohidratos?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí, son muy intensos",     "resp_no": "No los tengo"},
    {"texto": "¿Te cuesta bajar de peso, especialmente en abdomen?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí, es muy difícil",       "resp_no": "No tengo ese problema"},
    {"texto": "¿Presentas grasa abdominal (tipo 'panza')?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí la presento",           "resp_no": "No la presento"},
    {"texto": "¿Tienes piel oscura en cuello/axilas (acantosis)?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí la tengo",              "resp_no": "No la tengo"},
    {"texto": "¿Sientes hambre constante aunque hayas comido?",
     "categoria": "Síntomas físicos",   "resp_si": "Sí, siempre tengo hambre", "resp_no": "No, como normal"},
    # Indicadores metabólicos
    {"texto": "¿Tienes triglicéridos altos?",
     "categoria": "Indicadores metabólicos", "resp_si": "Sí me lo han dicho",  "resp_no": "No o no lo sé"},
    {"texto": "¿Tienes colesterol HDL bajo ('colesterol bueno')?",
     "categoria": "Indicadores metabólicos", "resp_si": "Sí me lo han dicho",  "resp_no": "No o no lo sé"},
    {"texto": "¿Te han dicho que tienes glucosa ligeramente elevada?",
     "categoria": "Indicadores metabólicos", "resp_si": "Sí me lo han dicho",  "resp_no": "No me lo han dicho"},
    {"texto": "¿Tienes presión arterial elevada?",
     "categoria": "Indicadores metabólicos", "resp_si": "Sí la tengo alta",    "resp_no": "No, está normal"},
    # Estilo de vida
    {"texto": "¿Haces poco o nada de ejercicio?",
     "categoria": "Estilo de vida",     "resp_si": "Casi nunca me muevo",      "resp_no": "Hago ejercicio regular"},
    {"texto": "¿Consumes bebidas azucaradas frecuentemente?",
     "categoria": "Estilo de vida",     "resp_si": "Sí, casi a diario",        "resp_no": "Casi no las tomo"},
    {"texto": "¿Duermes menos de 6–7 horas regularmente?",
     "categoria": "Estilo de vida",     "resp_si": "Sí, duermo poco",          "resp_no": "Duermo bien"},
    {"texto": "¿Tienes estrés constante?",
     "categoria": "Estilo de vida",     "resp_si": "Sí, todo el tiempo",       "resp_no": "No, estoy tranquilo/a"},
]

def build_test(page, state):
    respuestas = [None] * len(PREGUNTAS_TEST)
    resultado_ref = [None]

    resultado_container = ft.Column([], visible=False, spacing=10)
    botones_refs = []

    def calcular_resultado():
        total_si = sum(1 for r in respuestas if r is True)
        if total_si <= 3:
            nivel = "Bajo riesgo"
            color = LOW
            emoji = "✅"
            desc  = "Tu perfil no muestra señales significativas de resistencia a la insulina. Mantén tus hábitos saludables."
        elif total_si <= 7:
            nivel = "Riesgo moderado"
            color = MID
            emoji = "⚠️"
            desc  = "Tienes algunos indicadores de riesgo. Te recomendamos mejorar hábitos de alimentación y actividad física."
        else:
            nivel = "Alto riesgo"
            color = HIGH
            emoji = "🔴"
            desc  = "Presentas varios indicadores de resistencia a la insulina. Consulta a un médico y solicita estudios de glucosa e insulina en ayuno."

        resultado_container.controls = [
            ft.Container(height=8),
            tarjeta(ft.Column([
                ft.Row([
                    ft.Text(emoji, size=32),
                    ft.Column([
                        ft.Text(nivel, size=18, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(f"{total_si} de 14 síntomas presentes", size=12, color=MUTED),
                    ], spacing=2),
                ], spacing=12),
                ft.Container(height=6),
                ft.Text(desc, size=13, color=TEXT),
                ft.Container(height=8),
                ft.Divider(height=1, color=BORDER),
                ft.Container(height=8),
                ft.Text("Pruebas médicas recomendadas", size=12,
                        weight=ft.FontWeight.BOLD, color=ACCENT),
                ft.Text("• Glucosa en ayuno\n• Insulina en ayuno\n• Índice HOMA-IR\n• Hemoglobina glucosilada (HbA1c)",
                        size=12, color=TEXT),
                ft.Container(height=8),
                ft.Text("💡 Consejo clave", size=12, weight=ft.FontWeight.BOLD, color=MID),
                ft.Text("La resistencia a la insulina es reversible en muchos casos con cambios constantes (no extremos).",
                        size=12, color=TEXT),
            ], spacing=6)),
            ft.Container(height=8),
            ft.ElevatedButton(
                "Hacer el test de nuevo",
                on_click=lambda e: reiniciar_test(),
                width=300,
                style=ft.ButtonStyle(
                    bgcolor=ACCENT, color=WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ]
        resultado_container.visible = True
        page.update()

    def reiniciar_test():
        for i in range(len(respuestas)):
            respuestas[i] = None
        for row in botones_refs:
            for btn in row:
                btn.style = ft.ButtonStyle(
                    bgcolor=CARD, color=TEXT,
                    side=ft.BorderSide(1, BORDER),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
        resultado_container.visible = False
        resultado_container.controls = []
        page.update()

    def on_respuesta(idx, valor, btn_si, btn_no):
        def handler(e):
            respuestas[idx] = valor
            # Resaltar botón seleccionado
            if valor is True:
                btn_si.style = ft.ButtonStyle(
                    bgcolor=HIGH + "33", color=HIGH,
                    side=ft.BorderSide(2, HIGH),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
                btn_no.style = ft.ButtonStyle(
                    bgcolor=CARD, color=MUTED,
                    side=ft.BorderSide(1, BORDER),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            else:
                btn_no.style = ft.ButtonStyle(
                    bgcolor=LOW + "33", color=LOW,
                    side=ft.BorderSide(2, LOW),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
                btn_si.style = ft.ButtonStyle(
                    bgcolor=CARD, color=MUTED,
                    side=ft.BorderSide(1, BORDER),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            page.update()
            # Si todas contestadas → mostrar resultado
            if all(r is not None for r in respuestas):
                calcular_resultado()
        return handler

    # Construir tarjetas de preguntas
    preguntas_cards = []
    categoria_actual = ""

    for idx, p in enumerate(PREGUNTAS_TEST):
        if p["categoria"] != categoria_actual:
            categoria_actual = p["categoria"]
            preguntas_cards.append(ft.Container(height=6))
            preguntas_cards.append(titulo_seccion(categoria_actual.upper()))
            preguntas_cards.append(ft.Container(height=4))

        btn_si = ft.ElevatedButton(
            p["resp_si"],
            style=ft.ButtonStyle(
                bgcolor=CARD, color=TEXT,
                side=ft.BorderSide(1, BORDER),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        btn_no = ft.ElevatedButton(
            p["resp_no"],
            style=ft.ButtonStyle(
                bgcolor=CARD, color=TEXT,
                side=ft.BorderSide(1, BORDER),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )
        btn_si.on_click = on_respuesta(idx, True,  btn_si, btn_no)
        btn_no.on_click = on_respuesta(idx, False, btn_si, btn_no)
        botones_refs.append([btn_si, btn_no])

        preguntas_cards.append(
            tarjeta(ft.Column([
                ft.Text(f"{idx+1}. {p['texto']}", size=13, color=TEXT),
                ft.Container(height=6),
                ft.Row([btn_si, btn_no], spacing=10),
            ], spacing=4))
        )

    return ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🩺", size=28),
                    ft.Column([
                        ft.Text("Test de Síntomas", size=16,
                                weight=ft.FontWeight.BOLD, color=ACCENT),
                        ft.Text("Resistencia a la Insulina", size=11, color=MUTED),
                    ], spacing=1),
                ], spacing=10),
                ft.Container(height=4),
                ft.Text("Responde Sí o No a cada pregunta. Al terminar verás tu resultado automáticamente.",
                        size=12, color=MUTED),
            ], spacing=4),
            bgcolor=SURFACE,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        ),
        ft.Column([
            *preguntas_cards,
            resultado_container,
            ft.Container(height=24),
        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=0, expand=True)


# ═══════════════════════════════════════════════════════════
#  MÓDULO EDUCATIVO — LECCIONES + QUIZ
#  LECCIONES se importa desde core/datos.py (F2 del refactor — 2026-04-23)
# ═══════════════════════════════════════════════════════════

# LECCIONES — importado desde core/datos.py (ver import al inicio de archivo)
# Definición inline eliminada en F2 del refactor arquitectural (2026-04-23)
_LECCIONES_ARCHIVO_ORIGINAL = [  # bloque conservado para referencia, NO usado en runtime
    {
        "id": 0,
        "titulo": "¿Qué es la Resistencia a la Insulina?",
        "emoji": "🔬",
        "color": ACCENT,
        "contenido": [
            ("¿Qué es la insulina?", "La insulina es una hormona producida por el páncreas. Su función es permitir que el azúcar (glucosa) de los alimentos entre a las células para usarse como energía."),
            ("¿Qué pasa con la resistencia?", "Cuando las células dejan de responder bien a la insulina, el páncreas produce cada vez más para compensar. Con el tiempo esto puede llevar a prediabetes y diabetes tipo 2."),
            ("¿Es común?", "En México, más del 30% de la población adulta tiene algún grado de resistencia a la insulina, muchas veces sin saberlo."),
            ("Señales de alerta", "Cansancio después de comer, antojos de azúcar, dificultad para bajar de peso en el abdomen y piel oscura en cuello o axilas (acantosis nigricans)."),
        ],
        "quiz": [
            {"pregunta": "¿Cuál es la función principal de la insulina?",
             "opciones": ["Quemar grasa directamente", "Permitir que la glucosa entre a las células", "Producir energía en el páncreas", "Regular la presión arterial"],
             "correcta": 1},
            {"pregunta": "¿Cómo se llama la mancha oscura en cuello/axilas?",
             "opciones": ["Melanoma", "Acantosis nigricans", "Dermatitis", "Psoriasis"],
             "correcta": 1},
            {"pregunta": "¿Qué porcentaje aprox. de adultos en México tiene resistencia a la insulina?",
             "opciones": ["5%", "10%", "30%", "60%"],
             "correcta": 2},
        ],
    },
    {
        "id": 1,
        "titulo": "Entorno Urbano y Metabolismo",
        "emoji": "🏙️",
        "color": ACCENT3,
        "contenido": [
            ("El entorno construido afecta tu salud", "El lugar donde vives influye directamente en tu metabolismo. Las ciudades diseñadas para el auto, sin banquetas ni áreas verdes, promueven el sedentarismo."),
            ("Áreas verdes y actividad física", "Según la OMS, cada habitante debería tener acceso a 9 m² de área verde. En municipios como Cuautlancingo este valor es muy bajo, reduciendo la actividad física espontánea."),
            ("Entorno alimentario riesgoso", "La alta densidad de tiendas de ultraprocesados en una colonia aumenta el consumo de azúcar y grasas trans, factores directos de resistencia a la insulina."),
            ("Índice IARRI-MX", "Este índice mide el riesgo metabólico de tu municipio combinando: acceso a áreas verdes, caminabilidad, equipamiento deportivo, entorno alimentario e índice de marginación."),
        ],
        "quiz": [
            {"pregunta": "¿Cuántos m² de área verde por habitante recomienda la OMS?",
             "opciones": ["3 m²", "6 m²", "9 m²", "15 m²"],
             "correcta": 2},
            {"pregunta": "¿Qué mide el índice IARRI-MX?",
             "opciones": ["La calidad del aire", "El riesgo metabólico del entorno urbano", "La temperatura promedio", "El tráfico vehicular"],
             "correcta": 1},
            {"pregunta": "¿Cuál de estos factores NO forma parte del IARRI-MX?",
             "opciones": ["Acceso a áreas verdes", "Equipamiento deportivo", "Número de hospitales", "Entorno alimentario"],
             "correcta": 2},
        ],
    },
    {
        "id": 2,
        "titulo": "Arquitectura Preventiva",
        "emoji": "🏛️",
        "color": LOW,
        "contenido": [
            ("¿Qué es la arquitectura preventiva?", "Es el diseño del espacio construido para promover hábitos saludables. Va desde el diseño de una vivienda hasta la planificación urbana de una ciudad."),
            ("Diseño que invita al movimiento", "Escaleras visibles y accesibles, pasillos amplios, patios activos y rutas peatonales seguras aumentan la actividad física sin que la persona lo note."),
            ("Ventilación y luz natural", "Espacios bien ventilados y con luz natural reducen el estrés y mejoran el sueño, dos factores clave en la prevención de resistencia a la insulina."),
            ("Microhuertos urbanos", "Los microhuertos en azoteas, patios o espacios comunitarios mejoran el acceso a vegetales frescos. Son una intervención de bajo costo y alto impacto metabólico."),
        ],
        "quiz": [
            {"pregunta": "¿Cuál es el objetivo principal de la arquitectura preventiva?",
             "opciones": ["Construir hospitales", "Diseñar espacios que promuevan hábitos saludables", "Reducir costos de construcción", "Aumentar la densidad de vivienda"],
             "correcta": 1},
            {"pregunta": "¿Qué elemento arquitectónico simple aumenta la actividad física?",
             "opciones": ["Elevadores modernos", "Escaleras visibles y accesibles", "Estacionamientos amplios", "Ventanas pequeñas"],
             "correcta": 1},
            {"pregunta": "¿Cómo ayuda la luz natural a prevenir la resistencia a la insulina?",
             "opciones": ["Quema calorías directamente", "Reduce el estrés y mejora el sueño", "Aumenta la producción de insulina", "No tiene relación"],
             "correcta": 1},
        ],
    },
    {
        "id": 3,
        "titulo": "Alimentación Saludable",
        "emoji": "🥗",
        "color": LOW,
        "tipo_quiz": "ordena_plato",
        "contenido": [
            ("¿Qué comemos y cómo nos afecta?", "La alimentación es uno de los factores más importantes en la resistencia a la insulina. Los alimentos ultraprocesados, ricos en azúcares simples y grasas trans, elevan rápidamente la glucosa en sangre."),
            ("El plato del buen comer", "Una alimentación saludable incluye: 50% verduras y frutas, 25% cereales integrales y 25% proteínas de calidad. Limitar azúcares, harinas refinadas y bebidas azucaradas es clave."),
            ("Índice glucémico", "Los alimentos con alto índice glucémico (pan blanco, refresco, papas fritas) elevan rápidamente el azúcar en sangre. Los de bajo índice (avena, legumbres, verduras) la elevan lentamente, protegiendo al páncreas."),
        ],
        "quiz": [
            {"tipo": "ordena_plato",
             "pregunta": "Clasifica cada alimento: ¿es SALUDABLE o NO SALUDABLE para prevenir resistencia a la insulina?",
             "alimentos": [
                 {"nombre": "Brócoli",      "saludable": True},
                 {"nombre": "Refresco",     "saludable": False},
                 {"nombre": "Avena",        "saludable": True},
                 {"nombre": "Papas fritas", "saludable": False},
                 {"nombre": "Manzana",      "saludable": True},
                 {"nombre": "Pan blanco",   "saludable": False},
             ]},
        ],
    },
    {
        "id": 4,
        "titulo": "Actividad Física Preventiva",
        "emoji": "🏃",
        "color": ACCENT,
        "tipo_quiz": "verdadero_falso",
        "contenido": [
            ("¿Por qué moverse previene la resistencia?", "El músculo en movimiento consume glucosa sin necesitar insulina. 30 minutos de caminata diaria pueden reducir el riesgo de diabetes tipo 2 hasta en un 30%."),
            ("Tipos de ejercicio recomendados", "El ejercicio aeróbico (caminar, nadar, bicicleta) mejora la sensibilidad a la insulina. El ejercicio de fuerza aumenta la masa muscular que consume glucosa. La combinación es ideal."),
            ("Barreras arquitectónicas", "La falta de banquetas seguras, parques y ciclovías en colonias de Puebla reduce la actividad física involuntaria. El entorno construido puede ser aliado o enemigo de tu salud metabólica."),
        ],
        "quiz": [
            {"tipo": "verdadero_falso", "pregunta": "El músculo en movimiento puede consumir glucosa SIN necesitar insulina.", "correcta": True},
            {"tipo": "verdadero_falso", "pregunta": "Solo el ejercicio intenso de más de 1 hora tiene beneficios metabólicos.", "correcta": False},
            {"tipo": "verdadero_falso", "pregunta": "Caminar 30 minutos diarios puede reducir el riesgo de diabetes tipo 2.", "correcta": True},
            {"tipo": "verdadero_falso", "pregunta": "El entorno urbano NO influye en cuánto ejercicio hace una persona.", "correcta": False},
        ],
    },
    {
        "id": 5,
        "titulo": "Estres, Sueño y Metabolismo",
        "emoji": "😴",
        "color": ACCENT3,
        "tipo_quiz": "sopa_letras",
        "contenido": [
            ("El estres eleva el azucar en sangre", "Cuando estas estresado, tu cuerpo libera cortisol. Esta hormona eleva la glucosa en sangre. Si el estres es cronico, el pancreas trabaja en exceso y puede desarrollarse resistencia a la insulina."),
            ("Dormir poco empeora la insulina", "Dormir menos de 6 horas aumenta la resistencia a la insulina en solo una semana. Durante el sueño, el cuerpo regula hormonas metabolicas clave como la leptina, grelina e insulina."),
            ("Diseño del espacio para reducir estres", "Espacios con luz natural, ventilacion cruzada y acceso a areas verdes reducen el cortisol. La arquitectura puede ser una intervencion directa contra el estres cronico."),
        ],
        "quiz": [
            {"tipo": "sopa_letras",
             "instruccion": "Escribe las palabras clave que aprendiste (una por cada pista):",
             "palabras": ["cortisol", "insulina", "glucosa", "sueño", "estres"],
             "pistas":   ["Hormona del estres", "Hormona del pancreas", "Azucar en sangre", "Descanso nocturno", "Tension cronica"]},
        ],
    },
    {
        "id": 6,
        "titulo": "Puebla y sus Datos IARRI",
        "emoji": "🗺️",
        "color": MID,
        "tipo_quiz": "relaciona",
        "contenido": [
            ("Tres municipios, tres realidades", "San Andres Cholula, San Pablo Xochimehuacan y Cuautlancingo tienen indices IARRI muy diferentes. Sus condiciones de areas verdes, caminabilidad y entorno alimentario varian significativamente."),
            ("¿Que dicen los datos?", "San Andres Cholula tiene el mejor acceso a areas verdes (AV=0.80). Cuautlancingo tiene el mayor indice de entorno alimentario riesgoso (EAR=0.80), con alta densidad de tiendas de ultraprocesados."),
            ("Intervencion prioritaria", "Cuautlancingo requiere intervencion urgente: incrementar areas verdes, mejorar caminabilidad y fomentar equipamiento deportivo reduciria su IARRI de 0.78 a 0.64 (-18.2%)."),
        ],
        "quiz": [
            {"tipo": "relaciona",
             "pregunta": "Une cada municipio con su valor IARRI correcto:",
             "pares": [
                 {"municipio": "San Andres Cholula",      "iarri": "0.36", "nivel": "Bajo",  "col": LOW},
                 {"municipio": "San Pablo Xochimehuacan", "iarri": "0.62", "nivel": "Medio", "col": MID},
                 {"municipio": "Cuautlancingo",           "iarri": "0.78", "nivel": "Alto",  "col": HIGH},
             ]},
        ],
    },
]


def build_educacion(page, state):
    # Bloqueo invitado
    if state.get("es_invitado"):
        def _ir_reg_educ():
            state.get("logout", lambda: None)()
        _dialogo_registro(page, _ir_reg_educ)
        return _pantalla_bloqueada(
            "📚 Módulo Educativo",
            "Accede a lecciones interactivas y quizzes.",
            lambda: state.get("logout", lambda: None)(),
        )
    vista_actual  = [None]
    contenido_area = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)

    def mostrar_lista(update=True):
        vista_actual[0] = None
        tarjetas = []
        for lec in LECCIONES:
            completado = state.get(f"leccion_{lec['id']}_completada", False)
            puntaje    = state.get(f"leccion_{lec['id']}_puntaje", 0)
            tarjetas.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(lec["emoji"], size=28),
                            bgcolor=lec["color"] + "22",
                            border_radius=12,
                            width=52, height=52,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(lec["titulo"], size=13,
                                    weight=ft.FontWeight.BOLD, color=TEXT),
                            ft.Text(
                                f"✅ Completada — {puntaje}/{len(lec['quiz'])} correctas"
                                if completado else f"{len(lec['quiz'])} preguntas de quiz",
                                size=11,
                                color=LOW if completado else MUTED,
                            ),
                        ], spacing=3, expand=True),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if completado else ft.Icons.ARROW_FORWARD_IOS,
                            color=LOW if completado else MUTED,
                            size=18,
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CARD,
                    border=ft.border.all(1, lec["color"] + "55" if completado else BORDER),
                    border_radius=14,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ink=True,
                    on_click=lambda e, l=lec: mostrar_leccion(l),
                )
            )
        _controls_lista = [
            ft.Container(
                content=ft.Row([
                    ft.Text("📚", size=26),
                    ft.Column([
                        ft.Text("Módulo Educativo", size=16,
                                weight=ft.FontWeight.BOLD, color=ACCENT),
                        ft.Text("Aprende sobre resistencia a la insulina",
                                size=11, color=MUTED),
                    ], spacing=1),
                ], spacing=10),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=8),
                    *tarjetas,
                    ft.Container(height=24),
                ], spacing=10),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido_area.controls = _controls_lista
        if update:
            page.update()

    def mostrar_leccion(lec):
        vista_actual[0] = lec["id"]
        seccion_actual  = [0]
        total_secciones = len(lec["contenido"])
        resp_quiz       = [None] * len(lec["quiz"])
        quiz_enviado    = [False]
        quiz_area       = ft.Column([], spacing=10)

        def render_seccion():
            idx = seccion_actual[0]
            if idx < total_secciones:
                titulo_s, texto_s = lec["contenido"][idx]
                quiz_area.controls = [
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(lec["emoji"], size=24),
                                    bgcolor=lec["color"] + "22",
                                    border_radius=10,
                                    width=44, height=44,
                                    alignment=ft.alignment.Alignment(0, 0),
                                ),
                                ft.Text(titulo_s, size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=lec["color"], expand=True),
                            ], spacing=10),
                            ft.Container(height=8),
                            ft.Text(texto_s, size=13, color=TEXT),
                            ft.Container(height=12),
                            ft.Row([
                                ft.Text(f"Sección {idx+1} de {total_secciones}",
                                        size=11, color=MUTED),
                                ft.ElevatedButton(
                                    "Siguiente →" if idx < total_secciones - 1 else "Ir al Quiz →",
                                    on_click=lambda e: avanzar(),
                                    style=ft.ButtonStyle(
                                        bgcolor=lec["color"], color=WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=4),
                        bgcolor=CARD,
                        border=ft.border.all(1, BORDER),
                        border_radius=14,
                        padding=14,
                    ),
                ]
            else:
                render_quiz()
            page.update()

        def avanzar():
            seccion_actual[0] += 1
            render_seccion()

        def render_quiz():
            preg_cards = []
            tipo_quiz = lec.get("tipo_quiz", "multiple")

            for qi, q in enumerate(lec["quiz"]):
                q_tipo = q.get("tipo", "multiple")

                # ── ORDENA EL PLATO ─────────────────────────────
                if q_tipo == "ordena_plato":
                    if resp_quiz[qi] is None:
                        resp_quiz[qi] = {}
                    alimento_rows = []
                    for al in q["alimentos"]:
                        sel = resp_quiz[qi].get(al["nombre"])
                        def make_clasif(nombre, valor):
                            def h(e):
                                if quiz_enviado[0]: return
                                resp_quiz[qi][nombre] = valor
                                render_quiz()
                            return h
                        btn_s = ft.ElevatedButton(
                            "✅ Saludable",
                            on_click=make_clasif(al["nombre"], True),
                            style=ft.ButtonStyle(
                                bgcolor=LOW if sel is True else CARD,
                                color=WHITE if sel is True else TEXT,
                                side=ft.BorderSide(2 if sel is True else 1, LOW if sel is True else BORDER),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        )
                        btn_n = ft.ElevatedButton(
                            "❌ No saludable",
                            on_click=make_clasif(al["nombre"], False),
                            style=ft.ButtonStyle(
                                bgcolor=HIGH if sel is False else CARD,
                                color=WHITE if sel is False else TEXT,
                                side=ft.BorderSide(2 if sel is False else 1, HIGH if sel is False else BORDER),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        )
                        alimento_rows.append(ft.Container(
                            content=ft.Column([
                                ft.Text(al["nombre"], size=13, weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Row([btn_s, btn_n], spacing=8),
                            ], spacing=6),
                            bgcolor=CARD, border=ft.border.all(1, BORDER),
                            border_radius=10, padding=10,
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text("🥗 " + q["pregunta"], size=13, color=TEXT, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(alimento_rows, spacing=8),
                    ], spacing=4)))

                # ── VERDADERO O FALSO ────────────────────────────
                elif q_tipo == "verdadero_falso":
                    sel = resp_quiz[qi]
                    def make_vf(qi=qi, valor=True):
                        def h(e):
                            if quiz_enviado[0]: return
                            resp_quiz[qi] = valor
                            render_quiz()
                        return h
                    btn_v = ft.ElevatedButton(
                        "✅  Verdadero",
                        on_click=make_vf(qi, True),
                        height=46, expand=True,
                        style=ft.ButtonStyle(
                            bgcolor=LOW if sel is True else CARD,
                            color=WHITE if sel is True else TEXT,
                            side=ft.BorderSide(2 if sel is True else 1, LOW if sel is True else BORDER),
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    )
                    btn_f = ft.ElevatedButton(
                        "❌  Falso",
                        on_click=make_vf(qi, False),
                        height=46, expand=True,
                        style=ft.ButtonStyle(
                            bgcolor=HIGH if sel is False else CARD,
                            color=WHITE if sel is False else TEXT,
                            side=ft.BorderSide(2 if sel is False else 1, HIGH if sel is False else BORDER),
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    )
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text(f"{qi+1}. {q['pregunta']}", size=13, color=TEXT, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Row([btn_v, btn_f], spacing=10),
                    ], spacing=4)))

                # ── SOPA DE LETRAS ───────────────────────────────
                elif q_tipo == "sopa_letras":
                    if resp_quiz[qi] is None:
                        resp_quiz[qi] = [""] * len(q["palabras"])
                    campos = []
                    for pi, (pista, pal) in enumerate(zip(q["pistas"], q["palabras"])):
                        def make_change(pi=pi):
                            def h(e):
                                if quiz_enviado[0]: return
                                resp_quiz[qi][pi] = e.control.value.strip().lower()
                            return h
                        campos.append(ft.Container(
                            content=ft.Column([
                                ft.Text(f"Pista: {pista}", size=11, color=MUTED, italic=True),
                                ft.TextField(
                                    hint_text="Escribe la palabra...",
                                    on_change=make_change(pi),
                                    bgcolor=SURFACE, color=TEXT,
                                    border_color=BORDER,
                                    focused_border_color=ACCENT3,
                                    hint_style=ft.TextStyle(color=MUTED),
                                    height=42,
                                ),
                            ], spacing=4),
                            bgcolor=CARD, border=ft.border.all(1, BORDER),
                            border_radius=10, padding=10,
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text("💬 " + q["instruccion"], size=13, color=TEXT, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(campos, spacing=8),
                    ], spacing=4)))

                # ── RELACIONA ────────────────────────────────────
                elif q_tipo == "relaciona":
                    if resp_quiz[qi] is None:
                        resp_quiz[qi] = {}
                    iarri_opts = [p["iarri"] for p in q["pares"]]
                    par_rows = []
                    for par in q["pares"]:
                        sel_val = resp_quiz[qi].get(par["municipio"])
                        def make_rel(muni, iarri_val):
                            def h(e):
                                if quiz_enviado[0]: return
                                resp_quiz[qi][muni] = iarri_val
                                render_quiz()
                            return h
                        opt_btns = []
                        for opt in iarri_opts:
                            is_sel = sel_val == opt
                            opt_btns.append(ft.ElevatedButton(
                                opt,
                                on_click=make_rel(par["municipio"], opt),
                                style=ft.ButtonStyle(
                                    bgcolor=par["col"] if is_sel else CARD,
                                    color=WHITE if is_sel else TEXT,
                                    side=ft.BorderSide(2 if is_sel else 1, par["col"] if is_sel else BORDER),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ))
                        par_rows.append(ft.Container(
                            content=ft.Column([
                                ft.Text(par["municipio"], size=12, weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Row(opt_btns, spacing=6, wrap=True),
                            ], spacing=6),
                            bgcolor=CARD, border=ft.border.all(1, BORDER),
                            border_radius=10, padding=10,
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text("🔗 " + q["pregunta"], size=13, color=TEXT, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(par_rows, spacing=8),
                    ], spacing=4)))

                # ── MULTIPLE CHOICE (default) ────────────────────
                else:
                    opciones_btns = []
                    for oi, op in enumerate(q["opciones"]):
                        def make_op(qi=qi, oi=oi):
                            def handler(e):
                                if quiz_enviado[0]: return
                                resp_quiz[qi] = oi
                                render_quiz()
                            return handler
                        sel = resp_quiz[qi] == oi
                        opciones_btns.append(ft.Container(
                            content=ft.Text(op, size=12, color=WHITE if sel else TEXT),
                            bgcolor=lec["color"] if sel else CARD,
                            border=ft.border.all(2 if sel else 1, lec["color"] if sel else BORDER),
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=10),
                            ink=True,
                            on_click=make_op(),
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text(f"{qi+1}. {q['pregunta']}", size=13, color=TEXT, weight=ft.FontWeight.W_500),
                        ft.Container(height=6),
                        ft.Column(opciones_btns, spacing=6),
                    ], spacing=4)))

            # Check if all answered
            def all_answered():
                for qi, q in enumerate(lec["quiz"]):
                    q_tipo = q.get("tipo", "multiple")
                    if q_tipo == "ordena_plato":
                        if resp_quiz[qi] is None or len(resp_quiz[qi]) < len(q["alimentos"]):
                            return False
                    elif q_tipo == "sopa_letras":
                        if resp_quiz[qi] is None or any(v == "" for v in resp_quiz[qi]):
                            return False
                    elif q_tipo == "relaciona":
                        if resp_quiz[qi] is None or len(resp_quiz[qi]) < len(q["pares"]):
                            return False
                    else:
                        if resp_quiz[qi] is None:
                            return False
                return True

            btn_enviar = ft.ElevatedButton(
                "Ver resultados",
                on_click=lambda e: enviar_quiz(),
                disabled=not all_answered(),
                style=ft.ButtonStyle(
                    bgcolor=lec["color"], color=WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            )
            quiz_area.controls = [
                ft.Text("📝 Mini-juego de la lección", size=14,
                        weight=ft.FontWeight.BOLD, color=lec["color"]),
                ft.Container(height=4),
                *preg_cards,
                ft.Container(height=8),
                btn_enviar,
            ]
            page.update()

        def enviar_quiz():
            if quiz_enviado[0]:
                return
            quiz_enviado[0] = True
            correctas = 0
            total_items = 0
            for qi, q in enumerate(lec["quiz"]):
                q_tipo = q.get("tipo", "multiple")
                if q_tipo == "ordena_plato":
                    for al in q["alimentos"]:
                        total_items += 1
                        if resp_quiz[qi] and resp_quiz[qi].get(al["nombre"]) == al["saludable"]:
                            correctas += 1
                elif q_tipo == "verdadero_falso":
                    total_items += 1
                    if resp_quiz[qi] == q["correcta"]:
                        correctas += 1
                elif q_tipo == "sopa_letras":
                    for pi, pal in enumerate(q["palabras"]):
                        total_items += 1
                        user_ans = (resp_quiz[qi][pi] if resp_quiz[qi] else "").lower().strip()
                        if user_ans == pal.lower().strip():
                            correctas += 1
                elif q_tipo == "relaciona":
                    for par in q["pares"]:
                        total_items += 1
                        if resp_quiz[qi] and resp_quiz[qi].get(par["municipio"]) == par["iarri"]:
                            correctas += 1
                else:
                    total_items += 1
                    if resp_quiz[qi] == q["correcta"]:
                        correctas += 1
            if total_items == 0:
                total_items = len(lec["quiz"])
            state[f"leccion_{lec['id']}_completada"] = True
            state[f"leccion_{lec['id']}_puntaje"]    = correctas
            total      = total_items
            color_res  = LOW if correctas == total else MID if correctas >= total // 2 else HIGH
            quiz_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("¡Leccion completada!", size=15,
                                weight=ft.FontWeight.BOLD, color=color_res),
                        ft.Text(f"Obtuviste {correctas} de {total} respuestas correctas",
                                size=13, color=TEXT),
                        ft.Container(height=8),
                        ft.ElevatedButton(
                            "← Volver a lecciones",
                            on_click=lambda e: mostrar_lista(),
                            style=ft.ButtonStyle(
                                bgcolor=ACCENT, color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        ),
                    ], spacing=6),
                    bgcolor=color_res + "22",
                    border=ft.border.all(1, color_res),
                    border_radius=14,
                    padding=14,
                )
            )
            page.update()

        render_seccion()
        contenido_area.controls = [
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        ft.Icons.ARROW_BACK_IOS,
                        icon_color=ACCENT,
                        on_click=lambda e: mostrar_lista(),
                    ),
                    ft.Text(lec["titulo"], size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT, expand=True),
                ], spacing=4),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=ft.Column([
                    quiz_area,
                    ft.Container(height=24),
                ], spacing=12, scroll=ft.ScrollMode.AUTO),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),
        ]
        page.update()

    mostrar_lista(update=False)
    return ft.Column([contenido_area], expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 5 — PERFIL DE USUARIO
# ═══════════════════════════════════════════════════════════

# PALETAS importado desde ui.theme al inicio del archivo.

def _aplicar_paleta(nombre_paleta):
    """Cambia SOLO las variables globales de color. No toca la UI."""
    import ui.theme as _theme
    global BG, SURFACE, CARD, BORDER, TEXT, MUTED, ACCENT
    p = _theme.get_paleta(nombre_paleta)
    BG      = p["BG"]
    SURFACE = p["SURFACE"]
    CARD    = p["CARD"]
    BORDER  = p["BORDER"]
    TEXT    = p["TEXT"]
    MUTED   = p["MUTED"]
    ACCENT  = p["ACCENT"]


def build_perfil(page, state):
    """Pantalla de perfil: nombre usuario (Supabase), quizzes, tema y cerrar sesión."""

    # ── Datos del usuario desde Supabase (o fallback local) ──
    nombre_usuario   = ft.Ref[ft.Text]()
    email_usuario    = ft.Ref[ft.Text]()
    municipio_usuario = ft.Ref[ft.Text]()
    logout_feedback  = ft.Text("", size=12, color=HIGH)

    def _cargar_perfil_supabase():
        """Carga nombre/email desde Supabase usando el cliente de auth.py."""
        # Modo invitado
        if state.get("es_invitado"):
            nombre_usuario.current.value    = "Invitado"
            email_usuario.current.value     = "Registrate para guardar tu progreso"
            municipio_usuario.current.value = f"📍 {MUNICIPIOS[state.get('muni_idx',0)]['nombre']}"
            page.update()
            return
        try:
            import auth as _auth
            sb  = _auth.supabase
            ses = sb.auth.get_session()
            if ses and ses.user:
                uid    = ses.user.id
                email  = ses.user.email or "—"
                try:
                    perfil = sb.table("perfiles").select("nombre, municipio_actual") \
                               .eq("id", uid).single().execute()
                    nombre = perfil.data.get("nombre", "Usuario") if perfil.data else "Usuario"
                    muni   = perfil.data.get("municipio_actual", "—") if perfil.data else "—"
                except Exception:
                    nombre = email.split("@")[0]
                    muni   = MUNICIPIOS[state.get("muni_idx", 0)]["nombre"]
                nombre_usuario.current.value    = nombre
                email_usuario.current.value     = email
                municipio_usuario.current.value = f"📍 {muni}"
            else:
                nombre_usuario.current.value    = "Sin sesión activa"
                email_usuario.current.value     = "Inicia sesión para ver tus datos"
                municipio_usuario.current.value = ""
        except Exception as ex:
            print(f"[perfil] error cargando perfil: {ex}")
            nombre_usuario.current.value    = "Usuario Demo"
            email_usuario.current.value     = "Modo sin conexión"
            municipio_usuario.current.value = f"📍 {MUNICIPIOS[state.get('muni_idx',0)]['nombre']}"
        page.update()

    def _cerrar_sesion(e):
        """Delega al logout completo de main() que usa auth.py correctamente."""
        logout_feedback.value = "✓ Cerrando sesión..."
        page.update()
        logout_fn = state.get("logout")
        if logout_fn:
            logout_fn()
        else:
            # Fallback si no hay auth.py
            keys = [k for k in list(state.keys())
                    if k.startswith("leccion_") or k.startswith("slider_")]
            for k in keys:
                del state[k]
            state["muni_idx"] = 0
            state["tab"]      = 0
            logout_feedback.value = "✓ Sesión cerrada"
            nombre_usuario.current.value    = "Sin sesión activa"
            email_usuario.current.value     = "Inicia sesión para ver tus datos"
            municipio_usuario.current.value = ""
            page.update()

    # ── Estadísticas de quizzes ──────────────────────────────
    lecciones_completadas = []
    for lec in LECCIONES:
        completada = state.get(f"leccion_{lec['id']}_completada", False)
        puntaje    = state.get(f"leccion_{lec['id']}_puntaje", 0)
        total_preg = sum(
            len(q.get("alimentos", [])) if q.get("tipo") == "ordena_plato"
            else len(q.get("palabras", [])) if q.get("tipo") == "sopa_letras"
            else len(q.get("pares", [])) if q.get("tipo") == "relaciona"
            else 1
            for q in lec["quiz"]
        )
        if total_preg == 0:
            total_preg = len(lec["quiz"])
        pct = int(puntaje / total_preg * 100) if completada and total_preg > 0 else 0
        lecciones_completadas.append({
            "lec": lec, "completada": completada,
            "puntaje": puntaje, "total": total_preg, "pct": pct,
        })

    num_completadas = sum(1 for l in lecciones_completadas if l["completada"])
    promedio_quiz   = (
        sum(l["pct"] for l in lecciones_completadas if l["completada"]) // max(1, num_completadas)
        if num_completadas > 0 else 0
    )
    badges_ganadas = sum(1 for b in BADGES if b["earned"])

    # IARRI del municipio activo
    muni      = MUNICIPIOS[state.get("muni_idx", 0)]
    iarri_val = calc_iarri(muni["AV"], muni["IC"], muni["ED"], muni["EAR"], muni["IMP"])
    nivel, col_r = nivel_riesgo(iarri_val)

    # ── Header ───────────────────────────────────────────────
    perfil_header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Text("👤", size=32),
                    bgcolor=ACCENT + "22",
                    border_radius=40,
                    width=72, height=72,
                    alignment=ft.alignment.Alignment(0, 0),
                    border=ft.border.all(2, ACCENT),
                ),
                ft.Column([
                    ft.Text("Usuario Demo", size=18, weight=ft.FontWeight.W_900,
                            color=TEXT, ref=nombre_usuario),
                    ft.Text("Cargando...", size=11, color=MUTED, ref=email_usuario),
                    ft.Text("", size=11, color=MUTED, ref=municipio_usuario),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=8, height=8, border_radius=4, bgcolor=col_r),
                            ft.Text(f"IARRI {iarri_val:.2f} — Riesgo {nivel}", size=11,
                                    color=col_r, weight=ft.FontWeight.BOLD),
                        ], spacing=6, tight=True),
                        bgcolor=col_r + "18",
                        border=ft.border.all(1, col_r + "55"),
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        margin=ft.margin.only(top=4),
                    ),
                ], spacing=2, expand=True),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=0),
        bgcolor=SURFACE,
        border_radius=20,
        padding=18,
        border=ft.border.all(1, BORDER),
        shadow=ft.BoxShadow(blur_radius=10, color="#0000000d", offset=ft.Offset(0, 2)),
        margin=ft.margin.only(bottom=4),
    )

    # ── KPIs ─────────────────────────────────────────────────
    kpis = ft.Row([
        _perfil_kpi("📚", f"{num_completadas}/{len(LECCIONES)}", "Lecciones", ACCENT),
        _perfil_kpi("🏅", f"{promedio_quiz}%", "Promedio",
                    LOW if promedio_quiz >= 70 else MID),
        _perfil_kpi("🏆", f"{badges_ganadas}", "Insignias", ACCENT3),
    ], spacing=10)

    # ── Selector de tema ─────────────────────────────────────
    paleta_actual = state.get("paleta_nombre", "Claro (actual)")

    def _on_paleta(e):
        nombre = e.control.value
        state["paleta_nombre"] = nombre
        _aplicar_paleta(nombre)           # actualiza variables globales
        rebuild = state.get("rebuild_app")
        if rebuild:
            rebuild()                     # reconstruye TODA la app con nuevos colores

    dd_tema = ft.Dropdown(
        value=paleta_actual,
        options=[ft.dropdown.Option(k) for k in PALETAS],
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        bgcolor=SURFACE,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=12,
        expand=True,
    )
    dd_tema.on_change = _on_paleta

    tema_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("🎨", size=20),
                ft.Column([
                    ft.Text("Tema de color", size=13,
                            weight=ft.FontWeight.W_600, color=TEXT),
                    ft.Text("Cambia la paleta visual de la app",
                            size=11, color=MUTED),
                ], spacing=1, expand=True),
            ], spacing=10),
            ft.Container(height=10),
            dd_tema,
        ], spacing=0),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=16,
        padding=16,
        shadow=ft.BoxShadow(blur_radius=6, color="#0000000a", offset=ft.Offset(0, 1)),
    )

    # ── Cerrar sesión / Registrarse ─────────────────────────
    es_inv = state.get("es_invitado", False)
    if es_inv:
        logout_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("👋", size=20),
                    ft.Column([
                        ft.Text("Modo invitado", size=13,
                                weight=ft.FontWeight.W_600, color=TEXT),
                        ft.Text("Crea una cuenta para guardar tu progreso",
                                size=11, color=MUTED),
                    ], spacing=1, expand=True),
                ], spacing=10),
                ft.Container(height=12),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, color=WHITE, size=18),
                        ft.Text("Crear cuenta / Iniciar sesión", size=13,
                                weight=ft.FontWeight.BOLD, color=WHITE),
                    ], spacing=8, tight=True,
                       alignment=ft.MainAxisAlignment.CENTER),
                    on_click=_cerrar_sesion,
                    style=ft.ButtonStyle(
                        bgcolor=ACCENT,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.padding.symmetric(horizontal=20, vertical=14),
                    ),
                    expand=True,
                ),
                logout_feedback,
            ], spacing=0),
            bgcolor=CARD,
            border=ft.border.all(1, ACCENT + "44"),
            border_radius=16,
            padding=16,
            shadow=ft.BoxShadow(blur_radius=6, color="#0000000a", offset=ft.Offset(0, 1)),
        )
    else:
        logout_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🔐", size=20),
                    ft.Column([
                        ft.Text("Sesión", size=13,
                                weight=ft.FontWeight.W_600, color=TEXT),
                        ft.Text("Cerrar sesión y limpiar datos locales",
                                size=11, color=MUTED),
                    ], spacing=1, expand=True),
                ], spacing=10),
                ft.Container(height=12),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=WHITE, size=18),
                        ft.Text("Cerrar sesión", size=13,
                                weight=ft.FontWeight.BOLD, color=WHITE),
                    ], spacing=8, tight=True,
                       alignment=ft.MainAxisAlignment.CENTER),
                    on_click=_cerrar_sesion,
                    style=ft.ButtonStyle(
                        bgcolor=HIGH,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.padding.symmetric(horizontal=20, vertical=14),
                    ),
                    expand=True,
                ),
                logout_feedback,
            ], spacing=0),
            bgcolor=CARD,
            border=ft.border.all(1, HIGH + "33"),
            border_radius=16,
            padding=16,
            shadow=ft.BoxShadow(blur_radius=6, color="#0000000a", offset=ft.Offset(0, 1)),
        )

    # ── Barras de progreso por lección ───────────────────────
    quiz_cards = []
    for item in lecciones_completadas:
        lec       = item["lec"]
        pct       = item["pct"]
        done      = item["completada"]
        bar_color = LOW if pct >= 80 else MID if pct >= 50 else (HIGH if done else BORDER)

        quiz_cards.append(
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(lec["emoji"], size=18),
                            bgcolor=lec["color"] + "22",
                            border_radius=10,
                            width=36, height=36,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(lec["titulo"], size=12, weight=ft.FontWeight.W_600,
                                    color=TEXT, max_lines=1),
                            ft.Text(
                                f"{item['puntaje']}/{item['total']} correctas — {pct}%"
                                if done else "No completada aún",
                                size=11, color=MUTED,
                            ),
                        ], spacing=2, expand=True),
                        ft.Text(
                            f"{pct}%" if done else "—",
                            size=16, weight=ft.FontWeight.W_900,
                            color=bar_color,
                        ),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Container(
                            bgcolor=bar_color,
                            border_radius=4,
                            height=6,
                            width=max(0, pct / 100) * 320 if done else 0,
                        ),
                        bgcolor=BORDER,
                        border_radius=4,
                        height=6,
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                ], spacing=2),
                bgcolor=CARD,
                border=ft.border.all(1, lec["color"] + "44" if done else BORDER),
                border_radius=14,
                padding=14,
                shadow=ft.BoxShadow(blur_radius=6, color="#0000000a", offset=ft.Offset(0, 1)),
            )
        )

    # ── Insignias ────────────────────────────────────────────
    badge_items = []
    for b in BADGES:
        badge_items.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(b["emoji"], size=26, opacity=1.0 if b["earned"] else 0.3),
                    ft.Text(b["nombre"], size=9, text_align=ft.TextAlign.CENTER,
                            color=TEXT if b["earned"] else MUTED,
                            weight=ft.FontWeight.W_600 if b["earned"] else ft.FontWeight.NORMAL),
                    ft.Text("✓" if b["earned"] else "🔒",
                            size=9, color=ACCENT3 if b["earned"] else MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                bgcolor=ACCENT3 + "12" if b["earned"] else CARD,
                border=ft.border.all(1, ACCENT3 if b["earned"] else BORDER),
                border_radius=14, padding=10,
                expand=True,
            )
        )

    badges_grid = ft.Column([
        ft.Row(badge_items[:3], spacing=8),
        ft.Row(badge_items[3:], spacing=8),
    ], spacing=8)

    # Cargar datos de Supabase en hilo separado (no bloquea UI)
    threading.Thread(target=_cargar_perfil_supabase, daemon=True).start()

    return ft.Column([
        perfil_header,
        ft.Container(height=4),
        titulo_seccion("RESUMEN"),
        ft.Container(height=8),
        kpis,
        ft.Container(height=14),
        titulo_seccion("APARIENCIA"),
        ft.Container(height=8),
        tema_card,
        ft.Container(height=14),
        titulo_seccion("CUENTA"),
        ft.Container(height=8),
        logout_card,
        ft.Container(height=14),
        titulo_seccion("PROGRESO POR LECCIÓN"),
        ft.Container(height=8),
        *quiz_cards,
        ft.Container(height=14),
        titulo_seccion("INSIGNIAS OBTENIDAS"),
        ft.Container(height=8),
        badges_grid,
        ft.Container(height=32),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


def _perfil_kpi(emoji, valor, etiqueta, color):
    return ft.Container(
        content=ft.Column([
            ft.Text(emoji, size=22, text_align=ft.TextAlign.CENTER),
            ft.Text(valor, size=18, weight=ft.FontWeight.W_900, color=color,
                    text_align=ft.TextAlign.CENTER),
            ft.Text(etiqueta, size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        bgcolor=CARD,
        border=ft.border.all(1, color + "44"),
        border_radius=14,
        padding=ft.padding.symmetric(vertical=12, horizontal=8),
        expand=True,
        shadow=ft.BoxShadow(blur_radius=6, color="#0000000a", offset=ft.Offset(0, 1)),
    )


# ═══════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ═══════════════════════════════════════════════════════════
def main(page: ft.Page):
    page.title        = "ARQ-Metabólica MX"
    page.bgcolor      = BG
    page.padding      = 0
    page.theme_mode   = ft.ThemeMode.LIGHT
    page.fonts        = {}
    page.window.width     = 390
    page.window.height    = 844
    page.window.resizable = False
    page.window.center()

    # ── Intentar restaurar sesión guardada ───────────────────
    _usuario_activo = None
    _pantalla_login = None
    _auth_cerrar    = None
    try:
        from auth import cargar_sesion, pantalla_login as _pl, cerrar_sesion as _ac
        _usuario_activo = cargar_sesion()
        _pantalla_login = _pl
        _auth_cerrar    = _ac
    except Exception as ex:
        print(f"[main] auth no disponible: {ex}")

    # Estado compartido
    state = {"muni_idx": 0, "tab": 0, "refresh": None, "usuario": _usuario_activo}

    # Área de contenido principal
    content_area = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    nav_labels = ["Inicio", "Mapa", "Calcular", "Intervención"]
    nav_icons  = ["🏠", "🗺️", "🧮", "🛡️"]
    nav_items  = []

    def build_screen(idx):
        builders = [build_inicio, build_mapa, build_calculadora, build_recomendaciones, build_perfil]
        return builders[idx](page, state)

    def switch_tab(idx):
        # Si hay un switch_tab actualizado post-rebuild, usarlo
        override = state.get("_switch_tab")
        if override:
            override(idx)
            return
        state["tab"] = idx
        nav_items.clear()
        for i in range(4):
            nav_items.append(make_nav(i, active=(i == idx)))
        nav_bar.content = ft.Row(nav_items, expand=True,
                                 alignment=ft.MainAxisAlignment.SPACE_AROUND)
        content_area.content = build_screen(idx)
        page.update()

    def make_nav(idx, active=False):
        return ft.GestureDetector(
            content=ft.Column([
                ft.Text(nav_icons[idx], size=22,
                        color=ACCENT if active else MUTED,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(nav_labels[idx], size=10,
                        color=ACCENT if active else MUTED,
                        weight=ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               spacing=3, expand=True),
            on_tap=lambda e, i=idx: switch_tab(i),
            expand=True,
        )

    def refresh():
        if state.get("tab") == 0:
            content_area.content = build_screen(0)
            page.update()
    state["refresh"] = refresh

    def abrir_test():
        test_view = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color=ACCENT,
                                  on_click=lambda e: switch_tab(0)),
                    ft.Text("Test de Síntomas", size=14,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                ], spacing=4),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(content=build_test(page, state), expand=True),
        ], spacing=0, expand=True)
        content_area.content = test_view
        page.update()
    state["ir_test"] = abrir_test

    # ── Cerrar sesión completo ────────────────────────────────
    def logout_completo():
        # Solo cerrar sesión real si no es invitado
        if not state.get("es_invitado") and _auth_cerrar:
            try:
                _auth_cerrar()
            except Exception:
                pass
        # Limpiar estado completo
        keys = [k for k in list(state.keys())
                if k.startswith("leccion_") or k.startswith("slider_")]
        for k in keys:
            del state[k]
        state["muni_idx"]    = 0
        state["tab"]         = 0
        state["usuario"]     = None
        state["es_invitado"] = False
        mostrar_login()
    state["logout"] = logout_completo

    # ── Reconstruir toda la app con nueva paleta ──────────────
    def rebuild_app():
        """Llama mostrar_app() de nuevo — reconstruye todos los widgets con los colores globales actualizados."""
        p = PALETAS.get(state.get("paleta_nombre", "Claro (actual)"))
        page.bgcolor    = BG
        page.theme_mode = p["modo"] if p else ft.ThemeMode.LIGHT
        mostrar_app(state.get("usuario"))
    state["rebuild_app"] = rebuild_app

    # ── Barra de navegación ───────────────────────────────────
    for i in range(4):
        nav_items.append(make_nav(i, active=(i == 0)))

    nav_bar = ft.Container(
        content=ft.Row(nav_items, expand=True,
                       alignment=ft.MainAxisAlignment.SPACE_AROUND),
        bgcolor=SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(vertical=10),
        height=62,
        shadow=ft.BoxShadow(blur_radius=8, color="#00000012", offset=ft.Offset(0, -2)),
    )

    top_bar = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("ARQ-Metabólica MX", size=18, weight=ft.FontWeight.W_900,
                        color=ACCENT),
                ft.Text("IARRI-MX  ·  Puebla, México", size=11, color=MUTED),
            ], spacing=0),
            ft.Container(
                content=ft.Text("v1.0", size=11, color=WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=ACCENT,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        shadow=ft.BoxShadow(blur_radius=4, color="#0000000a", offset=ft.Offset(0, 1)),
    )

    app_shell = ft.Column([
        top_bar,
        ft.Container(content=content_area, expand=True),
        nav_bar,
    ], spacing=0, expand=True)

    # ── Mostrar app principal ─────────────────────────────────
    def mostrar_app(usuario=None):
        """Reconstruye TODOS los widgets con los colores globales actuales."""
        if usuario:
            state["usuario"] = usuario

        tab_activo = state.get("tab", 0)
        content_area.content = build_screen(tab_activo)

        # Reconstruir nav items frescos
        nav_items.clear()
        for i in range(4):
            nav_items.append(make_nav(i, active=(i == tab_activo)))

        # Reconstruir nav_bar con colores actuales
        nuevo_nav_bar = ft.Container(
            content=ft.Row(nav_items, expand=True,
                           alignment=ft.MainAxisAlignment.SPACE_AROUND),
            bgcolor=SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, BORDER)),
            padding=ft.padding.symmetric(vertical=10),
            height=62,
            shadow=ft.BoxShadow(blur_radius=8, color="#00000012", offset=ft.Offset(0, -2)),
        )

        # Reconstruir top_bar con colores actuales + botón Perfil
        nuevo_top_bar = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("ARQ-Metabólica MX", size=18, weight=ft.FontWeight.W_900,
                            color=ACCENT),
                    ft.Text("IARRI-MX  ·  Puebla, México", size=11, color=MUTED),
                ], spacing=0),
                ft.IconButton(
                    icon=ft.Icons.PERSON,
                    icon_size=24,
                    icon_color=ACCENT if tab_activo == 4 else MUTED,
                    on_click=lambda e: state.get("_switch_tab", lambda x: None)(4),
                    tooltip="Mi Perfil",
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            shadow=ft.BoxShadow(blur_radius=4, color="#0000000a", offset=ft.Offset(0, 1)),
        )

        nuevo_shell = ft.Column([
            nuevo_top_bar,
            ft.Container(content=content_area, expand=True),
            nuevo_nav_bar,
        ], spacing=0, expand=True)

        page.bgcolor = BG
        page.views.clear()
        page.views.append(ft.View(
            route="/app", bgcolor=BG, padding=0,
            controls=[nuevo_shell],
        ))
        page.update()

        # Actualizar switch_tab para usar el nav_bar nuevo
        def _new_switch_tab(idx):
            state["tab"] = idx
            nav_items.clear()
            for i in range(4):
                nav_items.append(make_nav(i, active=(i == idx)))
            nuevo_nav_bar.content = ft.Row(nav_items, expand=True,
                                           alignment=ft.MainAxisAlignment.SPACE_AROUND)
            content_area.content = build_screen(idx)
            page.update()
        # Patch switch_tab in closures via state
        state["_switch_tab"] = _new_switch_tab

    # ── Mostrar login ─────────────────────────────────────────
    def entrar_como_invitado():
        """Entra a la app sin cuenta, con funciones restringidas."""
        state["es_invitado"] = True
        state["usuario"]     = None
        mostrar_app(None)

    def mostrar_login():
        page.views.clear()
        if _pantalla_login:
            vista_login = _pantalla_login(page, mostrar_app)
            # Inyectar botón invitado al final de la vista de login
            btn_invitado = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            width=120, height=1, bgcolor="#33ffffff",
                        ),
                        ft.Text("  o  ", size=12, color="#80ffffff"),
                        ft.Container(
                            width=120, height=1, bgcolor="#33ffffff",
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=4),
                    ft.TextButton(
                        "Continuar como invitado →",
                        on_click=lambda e: entrar_como_invitado(),
                        style=ft.ButtonStyle(color="#99ffffff"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                padding=ft.padding.only(bottom=20),
            )
            vista_login.controls.append(btn_invitado)
            page.views.append(vista_login)
        else:
            mostrar_app()
        page.update()

    # ── Arranque: sesión activa → app, sin sesión → login ─────
    state["es_invitado"] = False
    if _usuario_activo:
        mostrar_app(_usuario_activo)
    else:
        mostrar_login()


if __name__ == "__main__":
    ft.app(target=main)