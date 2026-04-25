"""
ui/app_shell.py
App Shell — bottom nav + routing + state dict + auth initialization
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
    PALETAS,
)
from ui.screens.inicio_screen import build_inicio
from ui.screens.mapa_screen import build_mapa
from ui.screens.calculadora_screen import build_calculadora
from ui.screens.recomendaciones_screen import build_recomendaciones
from ui.screens.test_screen import build_test
from ui.screens.educacion_screen import build_educacion
from ui.screens.gamificacion_screen import build_gamificacion
from ui.screens.perfil_screen import build_perfil


def main(page: ft.Page):
    page.title        = "ARQ-Metabólica MX"
    page.bgcolor      = BG
    page.padding      = 0
    page.theme_mode   = ft.ThemeMode.LIGHT
    page.fonts        = {}
    page.window.center()

    # ── Intentar restaurar sesión guardada ───────────────────
    _usuario_activo = None
    _pantalla_login = None
    _auth_cerrar    = None
    try:
        from data.auth_repository import cargar_sesion, cerrar_sesion as _ac
        from ui.screens.login_screen import pantalla_login as _pl
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

    nav_labels = ["Inicio", "Mapa", "Calcular", "Intervención", "Aprender", "Retos"]
    nav_icons  = ["🏠", "🗺️", "🧮", "🛡️", "📚", "🏆"]
    nav_items  = []

    def build_screen(idx):
        builders = [build_inicio, build_mapa, build_calculadora, build_recomendaciones,
                    build_educacion, build_gamificacion, build_perfil]
        return builders[idx](page, state)

    def switch_tab(idx):
        # Si hay un switch_tab actualizado post-rebuild, usarlo
        override = state.get("_switch_tab")
        if override:
            override(idx)
            return
        state["tab"] = idx
        nav_items.clear()
        for i in range(6):
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
        tab_actual = state.get("tab", 0)
        content_area.content = build_screen(tab_actual)
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
                if k.startswith("leccion_") or k.startswith("slider_")
                or k.startswith("mc_") or k.startswith("reto_")
                or k.startswith("badge_") or k == "gamificacion_xp"
                or k == "iarri_guardado"]
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
    for i in range(6):
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
        for i in range(6):
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
                    icon_color=ACCENT if tab_activo == 6 else MUTED,
                    on_click=lambda e: state.get("_switch_tab", lambda x: None)(6),
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
            for i in range(6):
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

    # ── on_resize: refrescar layout al cambiar tamaño de ventana ──
    def on_resize(e):
        page.update()
    page.on_resize = on_resize

    # ── Arranque: sesión activa → app, sin sesión → login ─────
    state["es_invitado"] = False
    if _usuario_activo:
        mostrar_app(_usuario_activo)
    else:
        mostrar_login()
