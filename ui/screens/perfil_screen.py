"""
ui/screens/perfil_screen.py
Pantalla 5 — PERFIL DE USUARIO (datos Supabase, logout, badges)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import threading
import flet as ft

from ui.theme import (
    SURFACE, CARD, BORDER, ACCENT, ACCENT3,
    HIGH, TEXT, MUTED, WHITE,
)


def _hex_alpha(color: str, alpha_hex: str) -> str:
    """Concatena color hex con sufijo de opacidad de 2 dígitos."""
    base = color.lstrip("#")
    if len(base) == 8:
        return f"#{base[:6]}{alpha_hex}"
    return f"#{base}{alpha_hex}"
from ui.components.encuesta_widget import titulo_seccion
from core.datos import MUNICIPIOS, GAMIFICACION_BADGES
from ui.screens.gamificacion_screen import _badge_desbloqueada


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
            from data.supabase_client import get_client as _get_client
            sb  = _get_client()
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

    # ── Estadísticas de badges ───────────────────────────────
    badges_ganadas = sum(1 for b in GAMIFICACION_BADGES if _badge_desbloqueada(b, state))

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
        _perfil_kpi("🏆", f"{badges_ganadas}", "Insignias", ACCENT3),
        _perfil_kpi("⚡", f"{state.get('gamificacion_xp', 0)}", "XP total", ACCENT),
    ], spacing=10)

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

    # ── Insignias ────────────────────────────────────────────
    badge_items = []
    for b in GAMIFICACION_BADGES:
        ganada = _badge_desbloqueada(b, state)
        badge_items.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(b["emoji"], size=26, opacity=1.0 if ganada else 0.3),
                    ft.Text(b["nombre"], size=9, text_align=ft.TextAlign.CENTER,
                            color=TEXT if ganada else MUTED,
                            weight=ft.FontWeight.W_600 if ganada else ft.FontWeight.NORMAL),
                    ft.Text("✓" if ganada else "🔒",
                            size=9, color=ACCENT3 if ganada else MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                bgcolor=ACCENT3 + "12" if ganada else CARD,
                border=ft.border.all(1, ACCENT3 if ganada else BORDER),
                border_radius=14, padding=10,
                expand=True,
            )
        )

    # Filas de 3 en 3
    badges_rows = []
    for i in range(0, len(badge_items), 3):
        badges_rows.append(ft.Row(badge_items[i:i+3], spacing=8))
    badges_grid = ft.Column(badges_rows, spacing=8)

    # ── Metodología y Fuentes ─────────────────────────────────
    fases = [
        ("Fase 1", "Integración de datos (INEGI, CONAPO, DENUE)"),
        ("Fase 2", "Modelado matemático IARRI-MX"),
        ("Fase 3", "Validación estadística (Moran I, Regresión)"),
        ("Fase 4", "Desarrollo tecnológico (app móvil)"),
        ("Fase 5", "Implementación piloto — Puebla"),
    ]
    fase_rows = [
        ft.Row([
            ft.Container(
                width=8, height=8, border_radius=4, bgcolor=ACCENT,
                margin=ft.margin.only(top=2),
            ),
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
            bgcolor=_hex_alpha(ACCENT3, "11"),
            border=ft.border.all(1, _hex_alpha(ACCENT3, "33")),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        ),
        ft.Container(
            content=ft.Text("🌆 ODS 11 — Ciudades Sostenibles", size=11, color=ACCENT3),
            bgcolor=_hex_alpha(ACCENT3, "11"),
            border=ft.border.all(1, _hex_alpha(ACCENT3, "33")),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        ),
    ], wrap=True, spacing=8)

    meto_card = ft.Container(
        content=ft.Column([
            ft.Text("Metodología y Fuentes", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Container(height=4),
            *fase_rows,
            ft.Divider(height=1, color=BORDER),
            ods_row,
        ], spacing=8),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=16,
        padding=14,
    )

    # Cargar datos de Supabase en hilo separado (no bloquea UI)
    threading.Thread(target=_cargar_perfil_supabase, daemon=True).start()

    return ft.Column([
        perfil_header,
        ft.Container(height=4),
        titulo_seccion("RESUMEN"),
        ft.Container(height=8),
        kpis,
        ft.Container(height=14),
        titulo_seccion("CUENTA"),
        ft.Container(height=8),
        logout_card,
        ft.Container(height=14),
        titulo_seccion("INSIGNIAS OBTENIDAS"),
        ft.Container(height=8),
        badges_grid,
        ft.Container(height=14),
        titulo_seccion("METODOLOGÍA Y FUENTES"),
        ft.Container(height=8),
        meto_card,
        ft.Container(height=32),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)
