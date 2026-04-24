"""
ui/screens/perfil_screen.py
Pantalla 5 — PERFIL DE USUARIO (datos Supabase, tema, logout, progreso lecciones, badges)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import threading
import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
    PALETAS, get_paleta,
)
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import calc_iarri, nivel_riesgo
from core.datos import MUNICIPIOS, LECCIONES, BADGES


def _aplicar_paleta(nombre_paleta):
    """Cambia SOLO las variables globales de color en ui.theme. No toca la UI."""
    import ui.theme as _theme
    import ui.screens.inicio_screen as _inicio
    p = _theme.get_paleta(nombre_paleta)
    # Actualizar ui.theme
    _theme.BG      = p["BG"]
    _theme.SURFACE = p["SURFACE"]
    _theme.CARD    = p["CARD"]
    _theme.BORDER  = p["BORDER"]
    _theme.TEXT    = p["TEXT"]
    _theme.MUTED   = p["MUTED"]
    _theme.ACCENT  = p["ACCENT"]
    # Actualizar módulos que importaron las variables (reexport)
    _inicio.BG      = p["BG"]
    _inicio.SURFACE = p["SURFACE"]
    _inicio.CARD    = p["CARD"]
    _inicio.BORDER  = p["BORDER"]
    _inicio.TEXT    = p["TEXT"]
    _inicio.MUTED   = p["MUTED"]
    _inicio.ACCENT  = p["ACCENT"]


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
