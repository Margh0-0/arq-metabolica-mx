"""
ui/screens/educacion_screen.py
Pantalla EDUCACIÓN — Módulo educativo con lecciones + quiz interactivo
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23

LECCIONES importado desde core.datos (movido en F2 del refactor — 2026-04-23)
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from ui.screens.inicio_screen import _dialogo_registro, _pantalla_bloqueada
from core.datos import LECCIONES


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
