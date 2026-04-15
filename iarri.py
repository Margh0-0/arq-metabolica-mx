"""
Calculadora IARRI con Encuesta → Sliders → Monte Carlo
Framework: Flet (Python)
"""

import flet as ft
import numpy as np
import threading
import random

# ─── COLORES ────────────────────────────────────────────────────────────────
BG     = "#0a0f1e"
CARD   = "#111827"
BORDER = "#1f2d40"
TEXT   = "#e2e8f0"
MUTED  = "#64748b"
ACCENT = "#38bdf8"
ACCENT3= "#818cf8"
LOW    = "#22c55e"
MID    = "#f59e0b"
HIGH   = "#ef4444"

# ─── VARIABLES IARRI ────────────────────────────────────────────────────────
WEIGHTS = {"AV": 0.20, "IC": 0.25, "ED": 0.15, "EAR": 0.25, "IMP": 0.15}

VARIABLES = [
    {"key": "AV",  "label": "Acceso a Vivienda",      "desc": "Condiciones del hogar",      "icon": "🏠", "color": "#38bdf8", "inv": True},
    {"key": "IC",  "label": "Ingreso / Economía",     "desc": "Capacidad económica",        "icon": "💰", "color": "#818cf8", "inv": True},
    {"key": "ED",  "label": "Educación",               "desc": "Nivel educativo",            "icon": "📚", "color": "#34d399", "inv": True},
    {"key": "EAR", "label": "Exposición a Riesgo",    "desc": "Factores ambientales",       "icon": "⚠️", "color": "#f59e0b", "inv": False},
    {"key": "IMP", "label": "Impacto / Vulnerabilidad","desc": "Nivel de afectación",        "icon": "🎯", "color": "#ef4444", "inv": False},
]

# ─── MUNICIPIOS PRESET ──────────────────────────────────────────────────────
MUNICIPIOS = [
    {"nombre": "Puebla Centro",   "AV": 0.7, "IC": 0.65, "ED": 0.75, "EAR": 0.3,  "IMP": 0.25},
    {"nombre": "San Martín",      "AV": 0.4, "IC": 0.35, "ED": 0.45, "EAR": 0.65, "IMP": 0.60},
    {"nombre": "Tehuacán",        "AV": 0.5, "IC": 0.50, "ED": 0.55, "EAR": 0.50, "IMP": 0.45},
    {"nombre": "Chignahuapan",    "AV": 0.3, "IC": 0.25, "ED": 0.35, "EAR": 0.75, "IMP": 0.70},
]

# ─── ENCUESTA — preguntas por variable ──────────────────────────────────────
# Cada opción tiene un "valor" float 0-1 que representa el nivel de la variable
ENCUESTA = [
    {
        "variable": "AV",
        "pregunta": "¿Cómo describirías las condiciones de tu vivienda?",
        "opciones": [
            {"texto": "Casa propia con todos los servicios (agua, luz, drenaje)", "valor": 0.90},
            {"texto": "Renta con servicios básicos completos",                    "valor": 0.70},
            {"texto": "Servicios incompletos o vivienda compartida",              "valor": 0.45},
            {"texto": "Sin servicios básicos o vivienda precaria",                "valor": 0.15},
        ],
    },
    {
        "variable": "IC",
        "pregunta": "¿Cuál es el ingreso mensual aproximado de tu hogar?",
        "opciones": [
            {"texto": "Más de $15,000 pesos",              "valor": 0.90},
            {"texto": "Entre $8,000 y $15,000 pesos",      "valor": 0.65},
            {"texto": "Entre $3,000 y $8,000 pesos",       "valor": 0.40},
            {"texto": "Menos de $3,000 pesos",             "valor": 0.15},
        ],
    },
    {
        "variable": "ED",
        "pregunta": "¿Cuál es tu nivel de estudios más alto completado?",
        "opciones": [
            {"texto": "Universidad o posgrado",            "valor": 0.95},
            {"texto": "Preparatoria o técnico",            "valor": 0.70},
            {"texto": "Secundaria",                        "valor": 0.45},
            {"texto": "Primaria o sin estudios",           "valor": 0.20},
        ],
    },
    {
        "variable": "EAR",
        "pregunta": "¿Cuánto te afectan factores ambientales/climáticos en tu zona?",
        "opciones": [
            {"texto": "No me afectan, zona sin riesgos aparentes",     "valor": 0.10},
            {"texto": "Afectaciones leves ocasionales",                "valor": 0.35},
            {"texto": "Afectaciones moderadas (inundaciones, calor extremo)", "valor": 0.65},
            {"texto": "Zona de alto riesgo ambiental constante",       "valor": 0.90},
        ],
    },
    {
        "variable": "IMP",
        "pregunta": "¿Qué tan vulnerable te sientes ante una emergencia de salud?",
        "opciones": [
            {"texto": "Tengo seguro médico y acceso a especialistas",  "valor": 0.10},
            {"texto": "Acceso a IMSS o ISSSTE con algunas limitaciones","valor": 0.35},
            {"texto": "Solo atención en centros de salud públicos",    "valor": 0.65},
            {"texto": "Sin acceso a servicios de salud cercanos",      "valor": 0.90},
        ],
    },
]

# ─── LÓGICA IARRI ────────────────────────────────────────────────────────────
def calc_iarri(AV, IC, ED, EAR, IMP):
    return (WEIGHTS["AV"]  * (1 - AV) +
            WEIGHTS["IC"]  * (1 - IC) +
            WEIGHTS["ED"]  * (1 - ED) +
            WEIGHTS["EAR"] * EAR +
            WEIGHTS["IMP"] * IMP)

def nivel_riesgo(v):
    if v < 0.33:  return "Bajo",  LOW
    if v < 0.66:  return "Medio", MID
    return "Alto", HIGH

def prob_ri(v):
    return 1 / (1 + np.exp(-10 * (v - 0.5)))

def monte_carlo(vals, n=1000, sigma=0.12):
    res = []
    for _ in range(n):
        perturbed = {k: float(np.clip(v + random.gauss(0, sigma), 0, 1))
                     for k, v in vals.items()}
        res.append(calc_iarri(**perturbed))
    arr = np.array(res)
    ci  = np.percentile(arr, [2.5, 97.5])
    return arr, arr.mean(), arr.std(), ci[0], ci[1]

# ─── HELPERS UI ──────────────────────────────────────────────────────────────
def tarjeta(content, padding=16):
    return ft.Container(
        content=content,
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=16,
        padding=padding,
    )

def titulo_seccion(txt):
    return ft.Text(txt, size=10, color=MUTED, weight=ft.FontWeight.BOLD,
                   letter_spacing=1.5)

# ─── ENCUESTA UI ─────────────────────────────────────────────────────────────
def build_encuesta(page, on_complete):
    """
    Muestra una encuesta paso a paso.
    on_complete(respuestas: dict) se llama al terminar con los valores 0-1.
    """
    respuestas = {}
    paso_actual = [0]  # mutable para closures

    # Contenedor principal que se va actualizando
    contenido = ft.Column([], spacing=12, scroll=ft.ScrollMode.AUTO)

    progreso_txt = ft.Text("", size=11, color=MUTED)
    progreso_bar_inner = ft.Container(bgcolor=ACCENT, border_radius=4, height=4, width=0)
    progreso_bar = ft.Container(
        content=progreso_bar_inner,
        bgcolor=BORDER, border_radius=4, height=4,
        expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    def render_paso():
        idx = paso_actual[0]
        total = len(ENCUESTA)
        progreso_txt.value = f"Pregunta {idx + 1} de {total}"
        progreso_bar_inner.width = (idx / total) * 600  # se ajusta al container

        q = ENCUESTA[idx]
        v = next(var for var in VARIABLES if var["key"] == q["variable"])

        botones = []
        for op in q["opciones"]:
            def make_click(valor, variable):
                def on_click(e):
                    respuestas[variable] = valor
                    if paso_actual[0] < len(ENCUESTA) - 1:
                        paso_actual[0] += 1
                        render_paso()
                    else:
                        # Encuesta completa → llamar callback
                        on_complete(respuestas)
                return on_click

            botones.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(v["icon"], size=16),
                            bgcolor=v["color"] + "22",
                            border_radius=8,
                            width=34, height=34,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(op["texto"], size=13, color=TEXT, expand=True),
                    ], spacing=10),
                    bgcolor=CARD,
                    border=ft.border.all(1, v["color"] + "55"),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ink=True,
                    on_click=make_click(op["valor"], q["variable"]),
                )
            )

        contenido.controls = [
            ft.Container(height=4),
            ft.Row([
                ft.Container(
                    content=ft.Text(v["icon"], size=22),
                    bgcolor=v["color"] + "22",
                    border_radius=12,
                    width=48, height=48,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(v["label"], size=12, color=v["color"],
                            weight=ft.FontWeight.BOLD),
                    ft.Text(q["pregunta"], size=15, color=TEXT,
                            weight=ft.FontWeight.W_600),
                ], spacing=2, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=8),
            *botones,
        ]
        page.update()

    render_paso()

    return ft.Column([
        titulo_seccion("ENCUESTA DE RIESGO"),
        ft.Container(height=6),
        tarjeta(ft.Column([
            ft.Row([progreso_txt, progreso_bar], spacing=10,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ]), padding=12),
        ft.Container(height=4),
        tarjeta(contenido, padding=16),
        ft.Container(height=20),
    ], spacing=6)


# ─── CALCULADORA PRINCIPAL ───────────────────────────────────────────────────
def build_calculadora(page, state):
    slider_vals = {v["key"]: state.get(f"slider_{v['key']}", 0.5) for v in VARIABLES}

    result_txt   = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    nivel_txt    = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)
    prob_txt     = ft.Text("Prob. RI: —", size=12, color=MUTED)
    mc_btn_txt   = ft.Text("⚡  Simulación Monte Carlo (1000 iter.)", size=13,
                            weight=ft.FontWeight.BOLD, color="#000000")

    # Barras desglose
    desglose_bars = {}
    desglose_rows = []
    for v in VARIABLES:
        bar_inner = ft.Container(bgcolor=v["color"], border_radius=3, height=7, width=0)
        bar_outer = ft.Container(
            content=bar_inner, bgcolor=BORDER, border_radius=3,
            height=7, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=38,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace")
        desglose_bars[v["key"]] = (bar_inner, val_lbl)
        desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=34,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_outer, val_lbl,
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
        contribs = {
            "AV":  WEIGHTS["AV"]  * (1 - slider_vals["AV"]),
            "IC":  WEIGHTS["IC"]  * (1 - slider_vals["IC"]),
            "ED":  WEIGHTS["ED"]  * (1 - slider_vals["ED"]),
            "EAR": WEIGHTS["EAR"] * slider_vals["EAR"],
            "IMP": WEIGHTS["IMP"] * slider_vals["IMP"],
        }
        for k, (bar, lbl) in desglose_bars.items():
            bar.width = contribs[k] * 600
            lbl.value = f"{contribs[k]:.3f}"
        page.update()

    # Sliders
    slider_widgets = []
    slider_val_lbls = {}

    for v in VARIABLES:
        def make_change(key):
            def on_change(e):
                slider_vals[key] = e.control.value
                state[f"slider_{key}"] = e.control.value
                slider_val_lbls[key].value = f"{e.control.value:.2f}"
                actualizar_resultado()
            return on_change

        slider_val_lbl = ft.Text(f"{slider_vals[v['key']]:.2f}", size=15,
                                  weight=ft.FontWeight.W_900, color=v["color"], width=44)
        s = ft.Slider(
            min=0, max=1, divisions=100,
            value=slider_vals[v["key"]],
            active_color=v["color"],
            inactive_color=BORDER,
            thumb_color=v["color"],
            on_change=make_change(v["key"]),
            expand=True,
        )
        slider_widgets.append((v["key"], slider_val_lbl, s))
        slider_val_lbls[v["key"]] = slider_val_lbl

    # ── FUNCIÓN CLAVE: pre-llenar sliders desde encuesta o preset ──
    def aplicar_valores(nuevos_vals: dict, origen: str = ""):
        """Recibe dict {AV: float, IC: float, ...} y actualiza todo."""
        for key, val in nuevos_vals.items():
            slider_vals[key] = val
            state[f"slider_{key}"] = val
            slider_val_lbls[key].value = f"{val:.2f}"
            for k, lbl, s in slider_widgets:
                if k == key:
                    s.value = val
        if origen:
            origen_txt.value = f"✅ Valores cargados desde: {origen}"
            origen_txt.color = ACCENT
        actualizar_resultado()

    origen_txt = ft.Text("", size=11, color=MUTED, italic=True)

    # Encuesta: cuando termina llama aplicar_valores
    def on_encuesta_complete(respuestas: dict):
        encuesta_card.visible = False
        aplicar_valores(respuestas, "Encuesta")

    encuesta_widget = build_encuesta(page, on_encuesta_complete)
    encuesta_card = ft.Container(
        content=encuesta_widget,
        visible=True,
    )

    # Presets municipios
    def set_preset(idx):
        m = MUNICIPIOS[idx]
        vals = {v["key"]: m[v["key"]] for v in VARIABLES}
        aplicar_valores(vals, f"Municipio: {m['nombre']}")

    preset_buttons = []
    for i, m in enumerate(MUNICIPIOS):
        def make_on_click(idx):
            return lambda e: set_preset(idx)
        preset_buttons.append(
            ft.FilledTonalButton(
                m["nombre"].split()[0],
                on_click=make_on_click(i),
                style=ft.ButtonStyle(bgcolor=CARD, color=TEXT),
            )
        )

    # Botón para mostrar/ocultar encuesta
    def toggle_encuesta(e):
        encuesta_card.visible = not encuesta_card.visible
        toggle_btn_txt.value = (
            "🙈  Ocultar Encuesta" if encuesta_card.visible
            else "📋  Llenar desde Encuesta"
        )
        page.update()

    toggle_btn_txt = ft.Text("🙈  Ocultar Encuesta", size=13,
                              weight=ft.FontWeight.BOLD, color="#000000")

    # Tarjetas slider
    slider_cards = []
    for v, (key, val_lbl, s) in zip(VARIABLES, slider_widgets):
        card = tarjeta(ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text(v["icon"], size=15),
                        bgcolor=v["color"] + "22", border_radius=8,
                        width=30, height=30,
                        alignment=ft.alignment.Alignment(0, 0),
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
            ft.Text("protector ↓" if v["inv"] else "riesgo ↑",
                    size=9, color=v["color"], italic=True),
        ], spacing=2), padding=14)
        slider_cards.append(card)

    # Resultado card
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
            ft.Row([ft.Text("0.0", size=9, color=MUTED), ft.Container(expand=True),
                    ft.Text("0.5", size=9, color=MUTED), ft.Container(expand=True),
                    ft.Text("1.0", size=9, color=MUTED)]),
            mc_mean_txt, mc_std_txt, mc_ci_txt,
        ], spacing=8),
        bgcolor=CARD, border=ft.border.all(1, BORDER),
        border_radius=16, padding=16,
        visible=False,
    )

    def run_mc(e):
        mc_btn_txt.value = "⏳  Calculando..."
        page.update()

        def _task():
            res, media, desv, ci_lo, ci_hi = monte_carlo(slider_vals, 1000, 0.12)
            counts, _ = np.histogram(res, bins=20, range=(0, 1))
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
            origen_txt,
            ft.Divider(height=1, color=BORDER),
            ft.Text("Desglose de Contribuciones", size=11, color=MUTED),
            *desglose_rows,
            ft.Divider(height=1, color=BORDER),
            ft.ElevatedButton(
                content=mc_btn_txt,
                bgcolor=ACCENT,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                height=46,
                expand=True,
                on_click=run_mc,
            ),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=["#0f2441", "#1a0a2e"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    actualizar_resultado()

    return ft.Column([
        # ── Botón encuesta ──
        ft.ElevatedButton(
            content=toggle_btn_txt,
            bgcolor=ACCENT3,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            height=46,
            on_click=toggle_encuesta,
        ),
        ft.Container(height=4),

        # ── Encuesta (visible por default) ──
        encuesta_card,

        # ── Presets municipio ──
        titulo_seccion("O CARGA UN MUNICIPIO PRESET"),
        ft.Container(height=4),
        ft.Row(preset_buttons, spacing=8, scroll=ft.ScrollMode.AUTO),
        ft.Container(height=8),

        tarjeta(ft.Text(
            "IARRI = 0.20(1−AV) + 0.25(1−IC) + 0.15(1−ED) + 0.25(EAR) + 0.15(IMP)",
            size=10, color=ACCENT, font_family="monospace",
        )),
        ft.Container(height=10),

        titulo_seccion("AJUSTE MANUAL DE VARIABLES"),
        ft.Container(height=6),
        *slider_cards,
        ft.Container(height=10),
        resultado_card,
        ft.Container(height=10),
        mc_card,
        ft.Container(height=20),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title = "IARRI — Calculadora de Riesgo"
    page.bgcolor = BG
    page.padding = 16
    page.theme_mode = ft.ThemeMode.DARK

    state = {}
    page.add(build_calculadora(page, state))

ft.app(target=main)