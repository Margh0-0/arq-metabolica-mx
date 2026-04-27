"""
ui/screens/gamificacion_screen.py
Módulo: Gamificación — Retos Semanales e Insignias

Flujo de navegación:
  HOME  →  DETALLE_RETO  →  HOME
  HOME  →  DETALLE_BADGE →  HOME

Mecánica:
  - Los retos tienen pasos que el usuario marca manualmente
  - El progreso se persiste en state (reto_{id}_progreso, reto_{id}_completado)
  - Las insignias se desbloquean automáticamente al completar condiciones
  - El XP se acumula en state["gamificacion_xp"]
"""

import flet as ft
import threading

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.encuesta_widget import titulo_seccion
from core.datos import RETOS_SEMANALES, GAMIFICACION_BADGES, MICROCURSOS


# ─── MOTOR DE CONDICIONES ────────────────────────────────────────────────────

def _badge_desbloqueada(badge: dict, state: dict) -> bool:
    """Evalúa si la condición de una insignia se cumple en el state actual."""
    t = badge["condition_type"]
    k = badge["condition_key"]
    v = badge["condition_value"]

    if t == "bool":
        return bool(state.get(k, False))

    if t == "gte":
        # contar microcursos completados dinámicamente
        if k == "microcursos_completados":
            count = sum(
                1 for mc in MICROCURSOS
                if state.get(f"mc_{mc['id']}_evaluacion_completada", False)
            )
            return count >= (v or 1)
        return state.get(k, 0) >= (v or 1)

    if t == "reto":
        return bool(state.get(f"reto_{k}_completado", False))

    if t == "any_mc":
        return any(
            state.get(f"mc_{mc_id}_evaluacion_completada", False)
            for mc_id in (v or [])
        )

    return False


def _xp_gamificacion(state: dict) -> int:
    """XP acumulado de retos completados."""
    total = 0
    for r in RETOS_SEMANALES:
        if state.get(f"reto_{r['id']}_completado", False):
            total += r["xp"]
    for b in GAMIFICACION_BADGES:
        if _badge_desbloqueada(b, state) and state.get(f"badge_{b['id']}_xp_otorgado", False):
            total += b["xp_bonus"]
    return total


def _otorgar_xp_badges(state: dict, page):
    """Otorga XP de badges recién desbloqueadas (solo una vez por badge)."""
    for b in GAMIFICACION_BADGES:
        key = f"badge_{b['id']}_xp_otorgado"
        if _badge_desbloqueada(b, state) and not state.get(key, False):
            state[key] = True


# ─── PANTALLA PRINCIPAL ───────────────────────────────────────────────────────

def build_gamificacion(page: ft.Page, state: dict) -> ft.Column:

    contenido = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)

    # ─────────────────────────────────────────────────────────
    # HOME
    # ─────────────────────────────────────────────────────────
    def render_home(update: bool = True):
        _otorgar_xp_badges(state, page)

        xp = _xp_gamificacion(state)
        retos_completados = sum(
            1 for r in RETOS_SEMANALES
            if state.get(f"reto_{r['id']}_completado", False)
        )
        badges_ganadas = sum(
            1 for b in GAMIFICACION_BADGES
            if _badge_desbloqueada(b, state)
        )

        # ── Banner de progreso general ────────────────────────
        banner = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🏆", size=32),
                    ft.Column([
                        ft.Text("Gamificación", size=16,
                                weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text("Retos semanales e insignias", size=11,
                                color=WHITE + "CC"),
                    ], spacing=1, expand=True),
                    ft.Column([
                        ft.Text(f"{xp}", size=28, weight=ft.FontWeight.W_900,
                                color=WHITE),
                        ft.Text("XP", size=10, color=WHITE + "AA",
                                weight=ft.FontWeight.BOLD),
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=12),
                ft.Row([
                    _stat_chip(f"{retos_completados}/{len(RETOS_SEMANALES)}",
                               "Retos", "🎯"),
                    _stat_chip(f"{badges_ganadas}/{len(GAMIFICACION_BADGES)}",
                               "Insignias", "🏅"),
                    _stat_chip(
                        str(sum(1 for mc in MICROCURSOS
                                if state.get(f"mc_{mc['id']}_evaluacion_completada", False))),
                        "Microcursos", "🎓"),
                ], spacing=8),
            ], spacing=0),
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(-1, -1),
                end=ft.alignment.Alignment(1, 1),
                colors=["#7c3aed", "#0ea5e9"],
            ),
            border_radius=18,
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
        )

        # ── Retos por semana ──────────────────────────────────
        semanas = sorted(set(r["semana"] for r in RETOS_SEMANALES))
        semana_labels = {1: "Semana 1 — Movimiento", 2: "Semana 2 — Diseño",
                         3: "Semana 3 — Educación", 4: "Semana 4 — Reto Integral"}

        reto_widgets = []
        for semana in semanas:
            retos_sem = [r for r in RETOS_SEMANALES if r["semana"] == semana]
            reto_widgets.append(
                ft.Text(semana_labels.get(semana, f"Semana {semana}"),
                        size=12, weight=ft.FontWeight.BOLD, color=ACCENT3)
            )
            reto_widgets.append(ft.Container(height=4))
            for r in retos_sem:
                reto_widgets.append(_tarjeta_reto(r, state))
            reto_widgets.append(ft.Container(height=8))

        # ── Insignias ─────────────────────────────────────────
        badge_widgets = []
        # Primero desbloqueadas, luego bloqueadas
        desbloqueadas = [b for b in GAMIFICACION_BADGES if _badge_desbloqueada(b, state)]
        bloqueadas    = [b for b in GAMIFICACION_BADGES if not _badge_desbloqueada(b, state)]

        for grupo, label in [(desbloqueadas, "✅ Desbloqueadas"),
                              (bloqueadas,    "🔒 Por desbloquear")]:
            if not grupo:
                continue
            badge_widgets.append(
                ft.Text(label, size=11, color=MUTED, weight=ft.FontWeight.W_600)
            )
            badge_widgets.append(ft.Container(height=6))
            # Grilla de 3 columnas
            for i in range(0, len(grupo), 3):
                fila = grupo[i:i + 3]
                badge_widgets.append(
                    ft.Row(
                        [_tarjeta_badge(b, state) for b in fila],
                        spacing=8,
                    )
                )
            badge_widgets.append(ft.Container(height=8))

        controles = [
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("🏆", size=26),
                    ft.Column([
                        ft.Text("Gamificación", size=16,
                                weight=ft.FontWeight.BOLD, color=ACCENT),
                        ft.Text("Retos semanales · Insignias · Progreso",
                                size=11, color=MUTED),
                    ], spacing=1),
                ], spacing=10),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=10),
                    banner,
                    ft.Container(height=16),
                    titulo_seccion("RETOS SEMANALES DE DISEÑO SALUDABLE"),
                    ft.Container(height=8),
                    *reto_widgets,
                    titulo_seccion("INSIGNIAS"),
                    ft.Container(height=8),
                    *badge_widgets,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido.controls = controles
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────
    # DETALLE DE RETO
    # ─────────────────────────────────────────────────────────
    def render_reto(reto: dict, update: bool = True):
        completado = state.get(f"reto_{reto['id']}_completado", False)
        progreso   = state.get(f"reto_{reto['id']}_progreso",   [False] * len(reto["pasos"]))

        # Asegurar longitud correcta
        while len(progreso) < len(reto["pasos"]):
            progreso.append(False)
        state[f"reto_{reto['id']}_progreso"] = progreso

        pasos_hechos = sum(progreso)
        pct = pasos_hechos / len(reto["pasos"]) if reto["pasos"] else 0

        def toggle_paso(idx: int):
            if completado:
                return
            progreso[idx] = not progreso[idx]
            state[f"reto_{reto['id']}_progreso"] = progreso
            # Completar reto si se alcanzó la meta
            if sum(progreso) >= reto["meta"]:
                state[f"reto_{reto['id']}_completado"] = True
                # Otorgar XP
                state["gamificacion_xp"] = state.get("gamificacion_xp", 0) + reto["xp"]
                # Persistir progreso en Supabase (en hilo separado para no bloquear UI)
                def _sync_reto():
                    from data.auth_repository import obtener_usuario_actual
                    from data.resultados_repository import guardar_progreso_reto
                    import datetime
                    usuario = obtener_usuario_actual()
                    if usuario:
                        hoy = datetime.date.today()
                        guardar_progreso_reto(
                            usuario_id=usuario.id,
                            reto_id=reto["id"],
                            semana=reto["semana"],
                            anio=hoy.year,
                            completado=True,
                        )
                threading.Thread(target=_sync_reto, daemon=True).start()
                # Otorgar badge si aplica
                if reto.get("badge_id"):
                    _otorgar_xp_badges(state, page)
            render_reto(reto)

        # Pasos como checkboxes
        paso_widgets = []
        for idx, (paso, hecho) in enumerate(zip(reto["pasos"], progreso)):
            paso_widgets.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                "✓" if hecho else str(idx + 1),
                                size=11, color=WHITE if hecho else TEXT,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=LOW if hecho else BORDER,
                            border_radius=20,
                            width=26, height=26,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(
                            paso, size=12,
                            color=MUTED if hecho else TEXT,
                            expand=True,
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=LOW + "08" if hecho else CARD,
                    border=ft.border.all(1, LOW + "44" if hecho else BORDER),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    ink=not completado,
                    on_click=(lambda e, i=idx: toggle_paso(i)) if not completado else None,
                )
            )

        # Barra de progreso
        barra = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Progreso", size=11, color=MUTED),
                    ft.Container(expand=True),
                    ft.Text(f"{pasos_hechos}/{len(reto['pasos'])} pasos",
                            size=11, color=reto["color"], weight=ft.FontWeight.BOLD),
                ]),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            bgcolor=reto["color"] if not completado else LOW,
                            height=8,
                            expand=max(1, int(pct * 100)),
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.TRANSPARENT,
                            height=8,
                            expand=max(1, 100 - int(pct * 100)),
                        ),
                    ], spacing=0, expand=True),
                    bgcolor=BORDER, border_radius=4, height=8,
                    expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ], spacing=2),
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

        # Badge que desbloquea
        badge_preview = ft.Container()
        if reto.get("badge_id"):
            badge = next(
                (b for b in GAMIFICACION_BADGES if b["id"] == reto["badge_id"]), None
            )
            if badge:
                ya_ganada = _badge_desbloqueada(badge, state)
                badge_preview = ft.Container(
                    content=ft.Row([
                        ft.Text(badge["emoji"], size=28),
                        ft.Column([
                            ft.Text(
                                "¡Insignia desbloqueada!" if ya_ganada
                                else "Completa este reto para ganar:",
                                size=11,
                                color=LOW if ya_ganada else MUTED,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(badge["nombre"], size=13,
                                    weight=ft.FontWeight.BOLD, color=TEXT),
                        ], spacing=2),
                    ], spacing=12),
                    bgcolor=LOW + "15" if ya_ganada else reto["color"] + "10",
                    border=ft.border.all(1, LOW + "55" if ya_ganada else reto["color"] + "33"),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                )

        # Resultado si completado
        resultado = ft.Container()
        if completado:
            resultado = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("🎉", size=28),
                        ft.Column([
                            ft.Text("¡Reto completado!", size=15,
                                    weight=ft.FontWeight.BOLD, color=LOW),
                            ft.Text(f"+{reto['xp']} XP ganados",
                                    size=12, color=TEXT),
                        ], spacing=2),
                    ], spacing=12),
                ], spacing=4),
                bgcolor=LOW + "15",
                border=ft.border.all(1, LOW + "55"),
                border_radius=14,
                padding=14,
            )

        # Header con back
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS,
                    icon_color=ACCENT,
                    on_click=lambda e: render_home(),
                    icon_size=20,
                ),
                ft.Column([
                    ft.Text("Reto", size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text(reto["titulo"], size=10, color=MUTED),
                ], spacing=1, expand=True),
                ft.Text(reto["emoji"], size=26),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        )

        # Portada del reto
        portada = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(reto["emoji"], size=36),
                        bgcolor=reto["color"] + "22",
                        border_radius=16, width=64, height=64,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(reto["titulo"], size=15,
                                weight=ft.FontWeight.W_900, color=TEXT),
                        ft.Container(
                            content=ft.Text(
                                reto["categoria"].upper(),
                                size=9, color=reto["color"],
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=reto["color"] + "18",
                            border_radius=20,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        ),
                    ], spacing=4, expand=True),
                    ft.Container(
                        content=ft.Text(f"+{reto['xp']} XP", size=12,
                                        color=WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=reto["color"],
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    ),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Text(reto["descripcion"], size=12, color=MUTED),
            ], spacing=0),
            bgcolor=CARD,
            border=ft.border.all(
                2 if completado else 1,
                LOW if completado else reto["color"] + "44",
            ),
            border_radius=16, padding=16,
        )

        contenido.controls = [
            header,
            ft.Container(
                content=ft.Column([
                    ft.Container(height=8),
                    portada,
                    ft.Container(height=12),
                    barra,
                    ft.Container(height=12),
                    titulo_seccion("PASOS DEL RETO"),
                    ft.Container(height=6),
                    ft.Text(reto["instruccion"], size=11, color=MUTED, italic=True),
                    ft.Container(height=6),
                    *paso_widgets,
                    ft.Container(height=8),
                    badge_preview,
                    ft.Container(height=4),
                    resultado,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────
    # DETALLE DE BADGE
    # ─────────────────────────────────────────────────────────
    def render_badge(badge: dict, update: bool = True):
        ganada = _badge_desbloqueada(badge, state)

        # Reto asociado (si aplica)
        reto_asociado = None
        if badge["condition_type"] == "reto":
            reto_asociado = next(
                (r for r in RETOS_SEMANALES if r["id"] == badge["condition_key"]), None
            )

        # Condición legible
        if badge["condition_type"] == "reto" and reto_asociado:
            condicion_txt = f"Completar el reto: «{reto_asociado['titulo']}»"
        elif badge["condition_type"] == "bool":
            condicion_txt = "Guardar un cálculo IARRI en la Calculadora"
        elif badge["condition_type"] == "gte" and badge["condition_key"] == "microcursos_completados":
            condicion_txt = f"Completar {badge['condition_value']} microcursos en el módulo Aprender"
        else:
            condicion_txt = "Condición especial"

        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS,
                    icon_color=ACCENT,
                    on_click=lambda e: render_home(),
                    icon_size=20,
                ),
                ft.Column([
                    ft.Text("Insignia", size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text(badge["nombre"], size=10, color=MUTED),
                ], spacing=1, expand=True),
                ft.Text(badge["emoji"], size=26),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        )

        portada = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        badge["emoji"],
                        size=72,
                        opacity=1.0 if ganada else 0.25,
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(height=8),
                ft.Text(
                    badge["nombre"], size=20,
                    weight=ft.FontWeight.W_900, color=TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.Text(
                        "✅ DESBLOQUEADA" if ganada else "🔒 BLOQUEADA",
                        size=10, weight=ft.FontWeight.BOLD,
                        color=LOW if ganada else MUTED,
                    ),
                    bgcolor=LOW + "15" if ganada else BORDER + "44",
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                ),
                ft.Container(height=8),
                ft.Text(badge["descripcion"], size=12, color=MUTED,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=badge["color"] + "10" if ganada else CARD,
            border=ft.border.all(2 if ganada else 1,
                                  badge["color"] if ganada else BORDER),
            border_radius=20,
            padding=20,
            shadow=ft.BoxShadow(
                blur_radius=16 if ganada else 2,
                color=badge["color"] + ("44" if ganada else "00"),
                offset=ft.Offset(0, 4),
            ),
        )

        cond_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_ROUNDED if ganada
                        else ft.Icons.LOCK_OUTLINE_ROUNDED,
                        size=16,
                        color=LOW if ganada else MUTED,
                    ),
                    ft.Text("Condición para desbloquear", size=11,
                            color=MUTED, weight=ft.FontWeight.W_600),
                ], spacing=8),
                ft.Container(height=6),
                ft.Text(condicion_txt, size=13, color=TEXT),
                *(
                    [
                        ft.Container(height=8),
                        ft.ElevatedButton(
                            "Ir al reto →",
                            on_click=lambda e, r=reto_asociado: render_reto(r),
                            style=ft.ButtonStyle(
                                bgcolor=badge["color"], color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                        ),
                    ]
                    if reto_asociado and not ganada else []
                ),
            ], spacing=0),
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            border_radius=14,
            padding=14,
        )

        xp_card = ft.Container(
            content=ft.Row([
                ft.Text("🏅", size=22),
                ft.Column([
                    ft.Text("XP bonus al desbloquear", size=11, color=MUTED),
                    ft.Text(f"+{badge['xp_bonus']} XP", size=18,
                            weight=ft.FontWeight.BOLD,
                            color=LOW if ganada else badge["color"]),
                ], spacing=1),
            ], spacing=12),
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

        contenido.controls = [
            header,
            ft.Container(
                content=ft.Column([
                    ft.Container(height=16),
                    portada,
                    ft.Container(height=16),
                    cond_card,
                    ft.Container(height=8),
                    xp_card,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────
    # WIDGETS AUXILIARES
    # ─────────────────────────────────────────────────────────

    def _tarjeta_reto(r: dict, s: dict) -> ft.Container:
        completado    = s.get(f"reto_{r['id']}_completado", False)
        progreso      = s.get(f"reto_{r['id']}_progreso", [])
        pasos_hechos  = sum(progreso)
        total_pasos   = len(r["pasos"])
        pct           = pasos_hechos / total_pasos if total_pasos else 0

        estado_txt = (
            "✅ Completado"
            if completado
            else (f"{pasos_hechos}/{total_pasos} pasos" if pasos_hechos > 0
                  else "Sin iniciar")
        )
        estado_color = LOW if completado else (ACCENT if pasos_hechos > 0 else MUTED)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(r["emoji"], size=24),
                        bgcolor=r["color"] + "22",
                        border_radius=12, width=48, height=48,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(r["titulo"], size=13,
                                weight=ft.FontWeight.BOLD, color=TEXT),
                        ft.Text(estado_txt, size=11, color=estado_color),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(f"+{r['xp']} XP", size=11,
                                color=LOW if completado else r["color"],
                                weight=ft.FontWeight.BOLD),
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if completado
                            else ft.Icons.ARROW_FORWARD_IOS,
                            color=LOW if completado else MUTED,
                            size=16,
                        ),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                # Mini barra de progreso
                ft.Container(height=6),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            bgcolor=LOW if completado else r["color"],
                            height=4,
                            expand=max(1, int(pct * 100)),
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.TRANSPARENT,
                            height=4,
                            expand=max(1, 100 - int(pct * 100)),
                        ),
                    ], spacing=0, expand=True),
                    bgcolor=BORDER, border_radius=2, height=4,
                    expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ], spacing=0),
            bgcolor=CARD,
            border=ft.border.all(
                2 if completado else 1,
                LOW + "88" if completado else BORDER,
            ),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            ink=True,
            on_click=lambda e, reto=r: render_reto(reto),
            margin=ft.margin.only(bottom=8),
            shadow=ft.BoxShadow(
                blur_radius=6 if completado else 2,
                color=LOW + ("22" if completado else "00"),
                offset=ft.Offset(0, 2),
            ),
        )

    def _tarjeta_badge(b: dict, s: dict) -> ft.Container:
        ganada = _badge_desbloqueada(b, s)
        return ft.Container(
            content=ft.Column([
                ft.Text(b["emoji"], size=30,
                        opacity=1.0 if ganada else 0.2,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=4),
                ft.Text(b["nombre"], size=10,
                        color=TEXT if ganada else MUTED,
                        weight=ft.FontWeight.W_600 if ganada else ft.FontWeight.NORMAL,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2),
                ft.Text("✓ Ganada" if ganada else "🔒",
                        size=9,
                        color=LOW if ganada else MUTED,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            bgcolor=b["color"] + "15" if ganada else CARD,
            border=ft.border.all(
                2 if ganada else 1,
                b["color"] if ganada else BORDER,
            ),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=8, vertical=12),
            ink=True,
            on_click=lambda e, badge=b: render_badge(badge),
            expand=True,
            shadow=ft.BoxShadow(
                blur_radius=8 if ganada else 1,
                color=b["color"] + ("33" if ganada else "00"),
                offset=ft.Offset(0, 2),
            ),
        )

    render_home(update=False)
    return ft.Column([contenido], expand=True, spacing=0)


# ─── WIDGET AUXILIAR (module-level) ──────────────────────────────────────────

def _stat_chip(valor: str, label: str, emoji: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(emoji, size=18, text_align=ft.TextAlign.CENTER),
            ft.Text(valor, size=16, weight=ft.FontWeight.W_900,
                    color=WHITE, text_align=ft.TextAlign.CENTER),
            ft.Text(label, size=9, color=WHITE + "BB",
                    text_align=ft.TextAlign.CENTER),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=WHITE + "18",
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        expand=True,
    )
