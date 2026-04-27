"""
ui/screens/test_screen.py
Pantalla TEST — Test de síntomas de Resistencia a la Insulina (14 preguntas)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23

Mejoras 2026-04-27:
  - Layout mobile: botones en Column vertical (sin overflow)
  - Barra de progreso reactiva (respondidas / 14)
  - Indicador visual de preguntas sin responder (highlight rojo)
  - Resultado persistido en state["test_resultado"] para sobrevivir navegación
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion


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

_TOTAL = len(PREGUNTAS_TEST)  # 14


def build_test(page, state):
    # ── Estado ────────────────────────────────────────────────
    respuestas  = [None] * _TOTAL          # True | False | None
    botones_refs = []                      # [[btn_si, btn_no], ...]
    tarjetas_refs = []                     # [ft.Container, ...]  — para highlight de pendientes

    # ── Widgets reactivos globales ────────────────────────────
    progreso_txt = ft.Text(
        f"0 de {_TOTAL} respondidas",
        size=11, color=MUTED,
    )
    progreso_bar = ft.ProgressBar(
        value=0, expand=True, color=ACCENT, bgcolor=BORDER, bar_height=6,
    )
    resultado_container = ft.Column([], visible=False, spacing=10)

    # ── Helpers ───────────────────────────────────────────────
    def _respondidas():
        return sum(1 for r in respuestas if r is not None)

    def _actualizar_progreso():
        n = _respondidas()
        progreso_txt.value = f"{n} de {_TOTAL} respondidas"
        progreso_bar.value = n / _TOTAL

    def _highlight_pendientes():
        """Marca en rojo las tarjetas sin respuesta para que el usuario las encuentre."""
        for i, card in enumerate(tarjetas_refs):
            if respuestas[i] is None:
                card.border = ft.border.all(2, HIGH + "99")
            else:
                card.border = ft.border.all(1, BORDER)

    def _limpiar_highlights():
        for card in tarjetas_refs:
            card.border = ft.border.all(1, BORDER)

    # ── Resultado ─────────────────────────────────────────────
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

        # Persistir en state para sobrevivir navegación entre tabs
        state["test_resultado"] = {
            "nivel": nivel,
            "color": color,
            "emoji": emoji,
            "desc":  desc,
            "total_si": total_si,
        }

        _limpiar_highlights()
        resultado_container.controls = [
            ft.Container(height=8),
            tarjeta(ft.Column([
                ft.Row([
                    ft.Text(emoji, size=32),
                    ft.Column([
                        ft.Text(nivel, size=18, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(f"{total_si} de {_TOTAL} síntomas presentes", size=12, color=MUTED),
                    ], spacing=2),
                ], spacing=12),
                ft.Container(height=6),
                ft.Text(desc, size=13, color=TEXT),
                ft.Container(height=8),
                ft.Divider(height=1, color=BORDER),
                ft.Container(height=8),
                ft.Text("Pruebas médicas recomendadas", size=12,
                        weight=ft.FontWeight.BOLD, color=ACCENT),
                ft.Text(
                    "• Glucosa en ayuno\n• Insulina en ayuno\n• Índice HOMA-IR\n• Hemoglobina glucosilada (HbA1c)",
                    size=12, color=TEXT,
                ),
                ft.Container(height=8),
                ft.Text("💡 Consejo clave", size=12, weight=ft.FontWeight.BOLD, color=MID),
                ft.Text(
                    "La resistencia a la insulina es reversible en muchos casos con cambios constantes (no extremos).",
                    size=12, color=TEXT,
                ),
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

    def intentar_ver_resultado():
        """Muestra resultado si todas respondidas, si no resalta las pendientes."""
        if _respondidas() == _TOTAL:
            calcular_resultado()
        else:
            _highlight_pendientes()
            page.update()

    # ── Reinicio ──────────────────────────────────────────────
    def reiniciar_test():
        for i in range(_TOTAL):
            respuestas[i] = None
        for row in botones_refs:
            for btn in row:
                btn.style = ft.ButtonStyle(
                    bgcolor=CARD, color=TEXT,
                    side=ft.BorderSide(1, BORDER),
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
        _limpiar_highlights()
        _actualizar_progreso()
        resultado_container.visible = False
        resultado_container.controls = []
        state.pop("test_resultado", None)
        page.update()

    # ── Handler de respuesta ──────────────────────────────────
    def on_respuesta(idx, valor, btn_si, btn_no):
        def handler(e):
            respuestas[idx] = valor
            # Feedback visual: resaltar botón seleccionado
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
            # Limpiar highlight rojo de esta tarjeta si la tenía
            tarjetas_refs[idx].border = ft.border.all(1, BORDER)
            # Actualizar barra de progreso
            _actualizar_progreso()
            page.update()
            # Auto-calcular si están todas respondidas
            if _respondidas() == _TOTAL:
                calcular_resultado()
        return handler

    # ── Construir tarjetas de preguntas ───────────────────────
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
            expand=True,
        )
        btn_no = ft.ElevatedButton(
            p["resp_no"],
            style=ft.ButtonStyle(
                bgcolor=CARD, color=TEXT,
                side=ft.BorderSide(1, BORDER),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            expand=True,
        )
        btn_si.on_click = on_respuesta(idx, True,  btn_si, btn_no)
        btn_no.on_click = on_respuesta(idx, False, btn_si, btn_no)
        botones_refs.append([btn_si, btn_no])

        # Tarjeta con Column vertical — sin overflow en mobile
        card_container = ft.Container(
            content=ft.Column([
                ft.Text(f"{idx+1}. {p['texto']}", size=13, color=TEXT),
                ft.Container(height=6),
                # Column vertical: cada botón ocupa el ancho completo
                ft.Column([btn_si, btn_no], spacing=8),
            ], spacing=4),
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )
        tarjetas_refs.append(card_container)
        preguntas_cards.append(card_container)

    # ── Botón ver resultado (cuando no todas respondidas) ─────
    btn_ver_resultado = ft.ElevatedButton(
        "Ver mi resultado",
        icon=ft.Icons.ASSIGNMENT_TURNED_IN_OUTLINED,
        on_click=lambda e: intentar_ver_resultado(),
        style=ft.ButtonStyle(
            bgcolor=ACCENT, color=WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )

    # ── Layout final ──────────────────────────────────────────
    return ft.Column([
        # Header con progreso
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
                ft.Container(height=6),
                ft.Text(
                    "Responde Sí o No a cada pregunta. Al terminar verás tu resultado automáticamente.",
                    size=12, color=MUTED,
                ),
                ft.Container(height=8),
                ft.Row([progreso_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                progreso_bar,
            ], spacing=2),
            bgcolor=SURFACE,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        ),
        # Preguntas + resultado
        ft.Column([
            *preguntas_cards,
            ft.Container(height=12),
            btn_ver_resultado,
            resultado_container,
            ft.Container(height=24),
        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
    ], spacing=0, expand=True)
