"""
ui/screens/educacion_screen.py
Módulo de Educación Interactiva — Resistencia a la Insulina
Versión 2.0 — Gamificada con microcursos, XP y evaluaciones

Estructura de navegación:
  HOME  →  MICROCURSO  →  LECCION  →  EVALUACION  →  RESULTADO
  (o desde HOME directamente a LECCIONES libres)
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from ui.screens.inicio_screen import _dialogo_registro, _pantalla_bloqueada
from core.datos import LECCIONES, MICROCURSOS, NIVELES_XP


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _xp_total(state: dict) -> int:
    """Suma el XP acumulado de todas las evaluaciones completadas."""
    total = 0
    for mc in MICROCURSOS:
        xp = state.get(f"mc_{mc['id']}_xp", 0)
        total += xp
    return total


def _nivel_actual(xp: int) -> dict:
    nivel = NIVELES_XP[0]
    for n in NIVELES_XP:
        if xp >= n["xp_min"]:
            nivel = n
    return nivel


def _nivel_siguiente(xp: int) -> dict | None:
    for n in NIVELES_XP:
        if xp < n["xp_min"]:
            return n
    return None


def _microcurso_completado(mc: dict, state: dict) -> bool:
    return state.get(f"mc_{mc['id']}_evaluacion_completada", False)


def _microcurso_progreso(mc: dict, state: dict) -> int:
    """Retorna cuántas lecciones del microcurso han sido completadas."""
    completadas = sum(
        1 for lid in mc["lecciones_ids"]
        if state.get(f"leccion_{lid}_completada", False)
    )
    return completadas


# ─── PANTALLA PRINCIPAL ───────────────────────────────────────────────────────

def build_educacion(page: ft.Page, state: dict) -> ft.Column:
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

    # ── ESTADO DE NAVEGACIÓN INTERNA ──────────────────────────────────────────
    nav_state = {
        "vista": "home",          # "home" | "microcurso" | "leccion" | "evaluacion"
        "mc_activo": None,        # dict microcurso activo
        "lec_activa": None,       # dict lección activa
        "origen_leccion": None,   # "microcurso" | "libre"
    }

    contenido_area = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)

    # ── NAVEGACIÓN HACIA ATRÁS ────────────────────────────────────────────────
    def volver():
        v = nav_state["vista"]
        if v == "evaluacion":
            nav_state["vista"] = "microcurso"
            render_microcurso(nav_state["mc_activo"])
        elif v == "leccion":
            origen = nav_state["origen_leccion"]
            if origen == "microcurso":
                nav_state["vista"] = "microcurso"
                render_microcurso(nav_state["mc_activo"])
            else:
                render_home()
        elif v == "microcurso":
            render_home()
        else:
            render_home()

    # ─────────────────────────────────────────────────────────────────────────
    # VISTA HOME
    # ─────────────────────────────────────────────────────────────────────────
    def render_home(update: bool = True):
        nav_state["vista"] = "home"
        xp = _xp_total(state)
        nivel = _nivel_actual(xp)
        nivel_sig = _nivel_siguiente(xp)
        progreso_nivel = (
            (xp - nivel["xp_min"]) / (nivel_sig["xp_min"] - nivel["xp_min"])
            if nivel_sig else 1.0
        )

        # ── Banner XP / Nivel ──────────────────────────────────────────────
        banner_xp = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(nivel["emoji"], size=32),
                    ft.Column([
                        ft.Text(
                            nivel["titulo"],
                            size=15, weight=ft.FontWeight.BOLD, color=WHITE,
                        ),
                        ft.Text(
                            f"{xp} XP acumulados",
                            size=11, color=WHITE + "CC",
                        ),
                    ], spacing=1, expand=True),
                    ft.Container(
                        content=ft.Text(
                            f"Nivel {nivel['nivel']}",
                            size=12, weight=ft.FontWeight.BOLD, color=ACCENT,
                        ),
                        bgcolor=WHITE + "22",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    ),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Column([
                    ft.Row([
                        ft.Text(
                            f"→ {nivel_sig['emoji']} {nivel_sig['titulo']}"
                            if nivel_sig else "✨ ¡Nivel máximo alcanzado!",
                            size=10, color=WHITE + "BB",
                        ),
                        ft.Text(
                            f"{nivel_sig['xp_min'] - xp} XP restantes" if nivel_sig else "",
                            size=10, color=WHITE + "BB",
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Container(
                            width=max(4, progreso_nivel * 260),
                            height=6,
                            bgcolor=WHITE,
                            border_radius=3,
                        ),
                        width=260,
                        height=6,
                        bgcolor=WHITE + "33",
                        border_radius=3,
                    ),
                ], spacing=0),
            ], spacing=0),
            bgcolor=ACCENT,
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            margin=ft.margin.only(bottom=8),
        )

        # ── Tarjetas de Microcursos ────────────────────────────────────────
        mc_cards = []
        for mc in MICROCURSOS:
            completado = _microcurso_completado(mc, state)
            lecs_hechas = _microcurso_progreso(mc, state)
            total_lecs = len(mc["lecciones_ids"])
            mc_xp = state.get(f"mc_{mc['id']}_xp", 0)
            bloqueado = False  # sin prerequisitos por ahora

            progreso_frac = lecs_hechas / total_lecs if total_lecs > 0 else 0

            estado_texto = (
                f"✅ Completado — {mc_xp} XP ganados"
                if completado
                else f"{lecs_hechas}/{total_lecs} lecciones • {mc['xp_total']} XP"
            )
            estado_color = LOW if completado else MUTED

            mc_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(mc["emoji"], size=28),
                                bgcolor=mc["color"] + "22",
                                border_radius=12,
                                width=52, height=52,
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(
                                    mc["titulo"], size=13,
                                    weight=ft.FontWeight.BOLD, color=TEXT,
                                ),
                                ft.Text(
                                    mc["nivel_nombre"],
                                    size=10, color=mc["color"],
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(estado_texto, size=11, color=estado_color),
                            ], spacing=2, expand=True),
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if completado
                                else ft.Icons.ARROW_FORWARD_IOS,
                                color=LOW if completado else MUTED,
                                size=18,
                            ),
                        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        # barra de progreso de lecciones
                        ft.Container(height=6),
                        ft.Container(
                            content=ft.Container(
                                width=max(4, progreso_frac * 280),
                                height=4,
                                bgcolor=mc["color"],
                                border_radius=2,
                            ),
                            width=280,
                            height=4,
                            bgcolor=BORDER,
                            border_radius=2,
                        ),
                        # descripcion breve
                        ft.Container(height=4),
                        ft.Text(mc["descripcion"], size=11, color=MUTED),
                    ], spacing=0),
                    bgcolor=CARD,
                    border=ft.border.all(
                        2 if completado else 1,
                        mc["color"] + "88" if completado else BORDER,
                    ),
                    border_radius=14,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ink=not bloqueado,
                    on_click=(lambda e, m=mc: render_microcurso(m)) if not bloqueado else None,
                    opacity=1.0 if not bloqueado else 0.5,
                )
            )

        # ── Sección lecciones libres ───────────────────────────────────────
        lec_cards = []
        for lec in LECCIONES:
            completado = state.get(f"leccion_{lec['id']}_completada", False)
            puntaje    = state.get(f"leccion_{lec['id']}_puntaje", 0)
            lec_cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(lec["emoji"], size=22),
                            bgcolor=lec["color"] + "22",
                            border_radius=10,
                            width=42, height=42,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(lec["titulo"], size=12,
                                    weight=ft.FontWeight.BOLD, color=TEXT),
                            ft.Text(
                                f"✅ {puntaje}/{len(lec['quiz'])} correctas"
                                if completado else f"{len(lec['quiz'])} preguntas",
                                size=11,
                                color=LOW if completado else MUTED,
                            ),
                        ], spacing=2, expand=True),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if completado
                            else ft.Icons.ARROW_FORWARD_IOS,
                            color=LOW if completado else MUTED,
                            size=16,
                        ),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CARD,
                    border=ft.border.all(1, lec["color"] + "55" if completado else BORDER),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    ink=True,
                    on_click=lambda e, l=lec: _abrir_leccion_libre(l),
                )
            )

        controles = [
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("📚", size=26),
                    ft.Column([
                        ft.Text("Educación Interactiva", size=16,
                                weight=ft.FontWeight.BOLD, color=ACCENT),
                        ft.Text("Microcursos gamificados sobre resistencia a la insulina",
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
                    banner_xp,
                    ft.Container(height=12),
                    ft.Text("🎯 Microcursos", size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Container(height=6),
                    *mc_cards,
                    ft.Container(height=16),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=10),
                    ft.Text("📖 Lecciones individuales", size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text("Explora temas sueltos a tu ritmo",
                            size=11, color=MUTED),
                    ft.Container(height=6),
                    *lec_cards,
                    ft.Container(height=32),
                ], spacing=10),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido_area.controls = controles
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────────────────────
    # VISTA MICROCURSO
    # ─────────────────────────────────────────────────────────────────────────
    def render_microcurso(mc: dict, update: bool = True):
        nav_state["vista"] = "microcurso"
        nav_state["mc_activo"] = mc

        completado = _microcurso_completado(mc, state)
        lecs_hechas = _microcurso_progreso(mc, state)
        total_lecs = len(mc["lecciones_ids"])
        mc_xp = state.get(f"mc_{mc['id']}_xp", 0)

        # Lecciones del microcurso
        lec_cards = []
        for idx, lid in enumerate(mc["lecciones_ids"]):
            lec = next((l for l in LECCIONES if l["id"] == lid), None)
            if not lec:
                continue
            lec_completada = state.get(f"leccion_{lid}_completada", False)
            puntaje = state.get(f"leccion_{lid}_puntaje", 0)
            # La primera siempre accesible; las siguientes solo si la anterior está hecha
            bloqueada = idx > 0 and not state.get(
                f"leccion_{mc['lecciones_ids'][idx - 1]}_completada", False
            )
            lec_cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                "🔒" if bloqueada else lec["emoji"], size=22,
                            ),
                            bgcolor=(BORDER if bloqueada else lec["color"] + "22"),
                            border_radius=10,
                            width=42, height=42,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Column([
                            ft.Text(
                                lec["titulo"], size=12,
                                weight=ft.FontWeight.BOLD,
                                color=MUTED if bloqueada else TEXT,
                            ),
                            ft.Text(
                                "Completa la lección anterior primero"
                                if bloqueada
                                else (
                                    f"✅ {puntaje}/{len(lec['quiz'])} correctas"
                                    if lec_completada
                                    else f"{len(lec['quiz'])} preguntas de quiz"
                                ),
                                size=11,
                                color=MUTED if bloqueada else (LOW if lec_completada else MUTED),
                            ),
                        ], spacing=2, expand=True),
                        ft.Icon(
                            ft.Icons.LOCK if bloqueada
                            else (ft.Icons.CHECK_CIRCLE if lec_completada
                                  else ft.Icons.ARROW_FORWARD_IOS),
                            color=MUTED if bloqueada else (LOW if lec_completada else MUTED),
                            size=16,
                        ),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CARD,
                    border=ft.border.all(
                        1,
                        BORDER if bloqueada
                        else (lec["color"] + "55" if lec_completada else BORDER),
                    ),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    ink=not bloqueada,
                    opacity=0.55 if bloqueada else 1.0,
                    on_click=(
                        lambda e, l=lec: _abrir_leccion_mc(l)
                    ) if not bloqueada else None,
                )
            )

        # Botón evaluación
        ev_disponible = lecs_hechas == total_lecs
        ev_completada = _microcurso_completado(mc, state)
        btn_evaluacion = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("📝", size=22),
                    bgcolor=(LOW + "22" if ev_completada
                             else (ACCENT + "22" if ev_disponible else BORDER + "22")),
                    border_radius=10,
                    width=42, height=42,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(
                        mc["evaluacion"]["titulo"],
                        size=12, weight=ft.FontWeight.BOLD,
                        color=TEXT if ev_disponible or ev_completada else MUTED,
                    ),
                    ft.Text(
                        f"✅ Aprobada — {mc_xp} XP ganados" if ev_completada
                        else (
                            "¡Listo! Pon a prueba lo aprendido"
                            if ev_disponible
                            else f"Completa las {total_lecs} lecciones primero"
                        ),
                        size=11,
                        color=LOW if ev_completada else (ACCENT if ev_disponible else MUTED),
                    ),
                ], spacing=2, expand=True),
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if ev_completada
                    else (ft.Icons.PLAY_ARROW if ev_disponible else ft.Icons.LOCK),
                    color=LOW if ev_completada else (ACCENT if ev_disponible else MUTED),
                    size=18,
                ),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD,
            border=ft.border.all(
                2 if ev_completada else 1,
                LOW if ev_completada else (ACCENT if ev_disponible else BORDER),
            ),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            ink=ev_disponible and not ev_completada,
            opacity=0.55 if (not ev_disponible and not ev_completada) else 1.0,
            on_click=(
                lambda e: render_evaluacion(mc)
            ) if ev_disponible and not ev_completada else None,
        )

        # Badge de completado
        badge_widget = ft.Container()
        if ev_completada:
            badge_widget = ft.Container(
                content=ft.Row([
                    ft.Text(mc["badge_emoji"], size=28),
                    ft.Column([
                        ft.Text("¡Badge desbloqueado!", size=12,
                                weight=ft.FontWeight.BOLD, color=LOW),
                        ft.Text(mc["badge_nombre"], size=11, color=TEXT),
                    ], spacing=2),
                ], spacing=12),
                bgcolor=LOW + "15",
                border=ft.border.all(1, LOW + "55"),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
            )

        controles = [
            # Header con back
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        ft.Icons.ARROW_BACK_IOS,
                        icon_color=ACCENT,
                        on_click=lambda e: volver(),
                        icon_size=20,
                    ),
                    ft.Column([
                        ft.Text(mc["titulo"], size=13,
                                weight=ft.FontWeight.BOLD, color=TEXT, expand=True),
                        ft.Text(mc["nivel_nombre"], size=10, color=mc["color"],
                                weight=ft.FontWeight.W_600),
                    ], spacing=1, expand=True),
                    ft.Text(mc["emoji"], size=28),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=6),
                    # info del microcurso
                    ft.Container(
                        content=ft.Column([
                            ft.Text(mc["descripcion"], size=12, color=MUTED),
                            ft.Container(height=4),
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(
                                        f"{lecs_hechas}/{total_lecs} lecciones",
                                        size=11, color=mc["color"], weight=ft.FontWeight.W_600,
                                    ),
                                    bgcolor=mc["color"] + "15",
                                    border_radius=20,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        f"🏅 {mc['xp_total']} XP",
                                        size=11, color=ACCENT, weight=ft.FontWeight.W_600,
                                    ),
                                    bgcolor=ACCENT + "15",
                                    border_radius=20,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                            ], spacing=8),
                        ], spacing=4),
                        bgcolor=mc["color"] + "08",
                        border=ft.border.all(1, mc["color"] + "33"),
                        border_radius=12,
                        padding=12,
                    ),
                    ft.Container(height=12),
                    ft.Text("📚 Lecciones del módulo", size=12,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Container(height=6),
                    *lec_cards,
                    ft.Container(height=14),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=10),
                    ft.Text("🎯 Evaluación final", size=12,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Container(height=6),
                    btn_evaluacion,
                    ft.Container(height=8),
                    badge_widget,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido_area.controls = controles
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────────────────────
    # ABRIR LECCIÓN (desde microcurso o libre)
    # ─────────────────────────────────────────────────────────────────────────
    def _abrir_leccion_mc(lec: dict):
        nav_state["origen_leccion"] = "microcurso"
        render_leccion(lec)

    def _abrir_leccion_libre(lec: dict):
        nav_state["origen_leccion"] = "libre"
        render_leccion(lec)

    # ─────────────────────────────────────────────────────────────────────────
    # VISTA LECCIÓN
    # ─────────────────────────────────────────────────────────────────────────
    def render_leccion(lec: dict, update: bool = True):
        nav_state["vista"] = "leccion"
        nav_state["lec_activa"] = lec

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
                            # indicador de sección
                            ft.Row([
                                ft.Row([
                                    ft.Container(
                                        width=8, height=8,
                                        bgcolor=lec["color"] if i == idx else BORDER,
                                        border_radius=4,
                                    )
                                    for i in range(total_secciones)
                                ], spacing=4),
                                ft.ElevatedButton(
                                    "Siguiente →" if idx < total_secciones - 1
                                    else "Ir al Quiz →",
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

            for qi, q in enumerate(lec["quiz"]):
                q_tipo = q.get("tipo", "multiple")

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
                                side=ft.BorderSide(2 if sel is True else 1,
                                                   LOW if sel is True else BORDER),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        )
                        btn_n = ft.ElevatedButton(
                            "❌ No saludable",
                            on_click=make_clasif(al["nombre"], False),
                            style=ft.ButtonStyle(
                                bgcolor=HIGH if sel is False else CARD,
                                color=WHITE if sel is False else TEXT,
                                side=ft.BorderSide(2 if sel is False else 1,
                                                   HIGH if sel is False else BORDER),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        )
                        alimento_rows.append(ft.Container(
                            content=ft.Column([
                                ft.Text(al["nombre"], size=13,
                                        weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Row([btn_s, btn_n], spacing=8),
                            ], spacing=6),
                            bgcolor=CARD, border=ft.border.all(1, BORDER),
                            border_radius=10, padding=10,
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text("🥗 " + q["pregunta"], size=13, color=TEXT,
                                weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(alimento_rows, spacing=8),
                    ], spacing=4)))

                elif q_tipo == "verdadero_falso":
                    sel = resp_quiz[qi]
                    def make_vf(qi=qi, valor=True):
                        def h(e):
                            if quiz_enviado[0]: return
                            resp_quiz[qi] = valor
                            render_quiz()
                        return h
                    btn_v = ft.ElevatedButton(
                        "✅  Verdadero", on_click=make_vf(qi, True),
                        height=46, expand=True,
                        style=ft.ButtonStyle(
                            bgcolor=LOW if sel is True else CARD,
                            color=WHITE if sel is True else TEXT,
                            side=ft.BorderSide(2 if sel is True else 1,
                                               LOW if sel is True else BORDER),
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    )
                    btn_f = ft.ElevatedButton(
                        "❌  Falso", on_click=make_vf(qi, False),
                        height=46, expand=True,
                        style=ft.ButtonStyle(
                            bgcolor=HIGH if sel is False else CARD,
                            color=WHITE if sel is False else TEXT,
                            side=ft.BorderSide(2 if sel is False else 1,
                                               HIGH if sel is False else BORDER),
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    )
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text(f"{qi+1}. {q['pregunta']}", size=13, color=TEXT,
                                weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Row([btn_v, btn_f], spacing=10),
                    ], spacing=4)))

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
                        ft.Text("💬 " + q["instruccion"], size=13, color=TEXT,
                                weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(campos, spacing=8),
                    ], spacing=4)))

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
                                    side=ft.BorderSide(2 if is_sel else 1,
                                                       par["col"] if is_sel else BORDER),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                            ))
                        par_rows.append(ft.Container(
                            content=ft.Column([
                                ft.Text(par["municipio"], size=12,
                                        weight=ft.FontWeight.W_600, color=TEXT),
                                ft.Row(opt_btns, spacing=6, wrap=True),
                            ], spacing=6),
                            bgcolor=CARD, border=ft.border.all(1, BORDER),
                            border_radius=10, padding=10,
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text("🔗 " + q["pregunta"], size=13, color=TEXT,
                                weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Column(par_rows, spacing=8),
                    ], spacing=4)))

                else:  # multiple choice
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
                            border=ft.border.all(2 if sel else 1,
                                                  lec["color"] if sel else BORDER),
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=10),
                            ink=True,
                            on_click=make_op(),
                        ))
                    preg_cards.append(tarjeta(ft.Column([
                        ft.Text(f"{qi+1}. {q['pregunta']}", size=13, color=TEXT,
                                weight=ft.FontWeight.W_500),
                        ft.Container(height=6),
                        ft.Column(opciones_btns, spacing=6),
                    ], spacing=4)))

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
                on_click=lambda e: enviar_quiz_leccion(),
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

        def enviar_quiz_leccion():
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
            state[f"leccion_{lec['id']}_puntaje"] = correctas
            total = total_items
            color_res = LOW if correctas == total else MID if correctas >= total // 2 else HIGH
            quiz_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("¡Lección completada!", size=15,
                                weight=ft.FontWeight.BOLD, color=color_res),
                        ft.Text(f"Obtuviste {correctas} de {total} respuestas correctas",
                                size=13, color=TEXT),
                        ft.Container(height=8),
                        ft.ElevatedButton(
                            "← Volver",
                            on_click=lambda e: volver(),
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
                        on_click=lambda e: volver(),
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
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────────────────────
    # VISTA EVALUACIÓN (quiz avanzado del microcurso)
    # ─────────────────────────────────────────────────────────────────────────
    def render_evaluacion(mc: dict, update: bool = True):
        nav_state["vista"] = "evaluacion"
        preguntas = mc["evaluacion"]["preguntas"]
        respuestas = [None] * len(preguntas)
        enviado = [False]
        quiz_col = ft.Column([], spacing=12)

        def _rebuild_quiz():
            cards = []
            for qi, q in enumerate(preguntas):
                sel = respuestas[qi]
                opc_widgets = []
                for oi, op in enumerate(q["opciones"]):
                    is_sel = sel == oi
                    is_correcta = oi == q["correcta"]
                    # después de enviar, mostrar colores de resultado
                    if enviado[0]:
                        if is_correcta:
                            bg = LOW; col = WHITE; borde = LOW
                        elif is_sel and not is_correcta:
                            bg = HIGH; col = WHITE; borde = HIGH
                        else:
                            bg = CARD; col = TEXT; borde = BORDER
                    else:
                        bg = ACCENT if is_sel else CARD
                        col = WHITE if is_sel else TEXT
                        borde = ACCENT if is_sel else BORDER

                    def make_click(qi=qi, oi=oi):
                        def h(e):
                            if enviado[0]: return
                            respuestas[qi] = oi
                            _rebuild_quiz()
                        return h

                    opc_widgets.append(ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    "✓" if (enviado[0] and is_correcta)
                                    else ("✗" if (enviado[0] and is_sel and not is_correcta)
                                          else ("●" if is_sel else "○")),
                                    size=14, color=col, weight=ft.FontWeight.BOLD,
                                ),
                                width=22,
                            ),
                            ft.Text(op, size=12, color=col, expand=True),
                        ], spacing=8),
                        bgcolor=bg,
                        border=ft.border.all(2 if is_sel else 1, borde),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        ink=not enviado[0],
                        on_click=make_click() if not enviado[0] else None,
                    ))

                # explicación post-envío
                explicacion_widget = ft.Container()
                if enviado[0]:
                    correcta_sel = respuestas[qi] == q["correcta"]
                    explicacion_widget = ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.LIGHTBULB_OUTLINE,
                                size=16, color=MID,
                            ),
                            ft.Text(q["explicacion"], size=11, color=TEXT,
                                    expand=True, italic=True),
                        ], spacing=8),
                        bgcolor=MID + "15",
                        border=ft.border.all(1, MID + "44"),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    )

                # XP badge
                xp_badge = ft.Container()
                if enviado[0] and respuestas[qi] == q["correcta"]:
                    xp_badge = ft.Container(
                        content=ft.Text(f"+{q['xp']} XP", size=10,
                                        color=WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=LOW,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    )

                cards.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(str(qi + 1), size=12,
                                                    color=WHITE, weight=ft.FontWeight.BOLD),
                                    bgcolor=mc["color"],
                                    border_radius=20,
                                    width=28, height=28,
                                    alignment=ft.alignment.Alignment(0, 0),
                                ),
                                ft.Text(q["pregunta"], size=13, color=TEXT,
                                        expand=True, weight=ft.FontWeight.W_500),
                                xp_badge,
                            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
                            ft.Container(height=8),
                            ft.Column(opc_widgets, spacing=6),
                            ft.Container(height=4),
                            explicacion_widget,
                        ], spacing=0),
                        bgcolor=CARD,
                        border=ft.border.all(1, BORDER),
                        border_radius=14,
                        padding=14,
                    )
                )

            # botón enviar o resultado
            all_ans = all(r is not None for r in respuestas)
            if enviado[0]:
                xp_ganado = sum(
                    q["xp"]
                    for qi, q in enumerate(preguntas)
                    if respuestas[qi] == q["correcta"]
                )
                total_xp = sum(q["xp"] for q in preguntas)
                correctas_total = sum(
                    1 for qi, q in enumerate(preguntas)
                    if respuestas[qi] == q["correcta"]
                )
                pct = correctas_total / len(preguntas)
                color_res = LOW if pct >= 0.8 else MID if pct >= 0.5 else HIGH

                # Guardar en state
                state[f"mc_{mc['id']}_evaluacion_completada"] = True
                state[f"mc_{mc['id']}_xp"] = xp_ganado

                bottom = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(
                                "🏆" if pct >= 0.8 else "📊" if pct >= 0.5 else "📖",
                                size=32,
                            ),
                            ft.Column([
                                ft.Text(
                                    "¡Excelente dominio!" if pct >= 0.8
                                    else "¡Buen intento!" if pct >= 0.5
                                    else "Sigue practicando",
                                    size=15, weight=ft.FontWeight.BOLD, color=color_res,
                                ),
                                ft.Text(
                                    f"{correctas_total}/{len(preguntas)} correctas  •  {xp_ganado}/{total_xp} XP",
                                    size=12, color=TEXT,
                                ),
                            ], spacing=2, expand=True),
                        ], spacing=12),
                        ft.Container(height=6),
                        # badge si pasó
                        ft.Container(
                            content=ft.Row([
                                ft.Text(mc["badge_emoji"], size=24),
                                ft.Column([
                                    ft.Text("Badge desbloqueado", size=11,
                                            color=LOW, weight=ft.FontWeight.W_600),
                                    ft.Text(mc["badge_nombre"], size=12,
                                            color=TEXT, weight=ft.FontWeight.BOLD),
                                ], spacing=1),
                            ], spacing=10),
                            bgcolor=LOW + "15",
                            border=ft.border.all(1, LOW + "55"),
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            visible=pct >= 0.5,
                        ),
                        ft.Container(height=8),
                        ft.ElevatedButton(
                            f"← Volver al módulo",
                            on_click=lambda e: volver(),
                            style=ft.ButtonStyle(
                                bgcolor=ACCENT, color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        ),
                    ], spacing=4),
                    bgcolor=color_res + "15",
                    border=ft.border.all(1, color_res + "55"),
                    border_radius=14,
                    padding=14,
                )
            else:
                bottom = ft.ElevatedButton(
                    "Enviar evaluación",
                    on_click=lambda e: _enviar(),
                    disabled=not all_ans,
                    style=ft.ButtonStyle(
                        bgcolor=mc["color"], color=WHITE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )

            quiz_col.controls = [
                # Descripción de la evaluación
                ft.Container(
                    content=ft.Column([
                        ft.Text(mc["evaluacion"]["descripcion"],
                                size=12, color=MUTED),
                        ft.Container(height=4),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    f"📝 {len(preguntas)} preguntas",
                                    size=11, color=mc["color"], weight=ft.FontWeight.W_600,
                                ),
                                bgcolor=mc["color"] + "15",
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"🏅 {sum(q['xp'] for q in preguntas)} XP máx.",
                                    size=11, color=ACCENT, weight=ft.FontWeight.W_600,
                                ),
                                bgcolor=ACCENT + "15",
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            ),
                        ], spacing=8),
                    ], spacing=4),
                    bgcolor=mc["color"] + "08",
                    border=ft.border.all(1, mc["color"] + "33"),
                    border_radius=12,
                    padding=12,
                ),
                ft.Container(height=4),
                *cards,
                ft.Container(height=8),
                bottom,
                ft.Container(height=32),
            ]
            page.update()

        def _enviar():
            enviado[0] = True
            _rebuild_quiz()

        _rebuild_quiz()

        controles = [
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        ft.Icons.ARROW_BACK_IOS,
                        icon_color=ACCENT,
                        on_click=lambda e: volver(),
                        icon_size=20,
                    ),
                    ft.Column([
                        ft.Text(mc["evaluacion"]["titulo"], size=13,
                                weight=ft.FontWeight.BOLD, color=TEXT, expand=True),
                        ft.Text("Evaluación final", size=10,
                                color=mc["color"], weight=ft.FontWeight.W_600),
                    ], spacing=1, expand=True),
                    ft.Text("📝", size=26),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=quiz_col,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ),
        ]
        contenido_area.controls = controles
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────────────────────
    # INICIO
    # ─────────────────────────────────────────────────────────────────────────
    render_home(update=False)
    return ft.Column([contenido_area], expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
