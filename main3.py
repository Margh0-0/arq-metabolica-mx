"""
ARQ-Metabólica MX — App Móvil con Flet (Python + Flutter)
Índice Arquitectónico de Riesgo de Resistencia a la Insulina (IARRI-MX)
CON INTEGRACIÓN MySQL Workbench

Instalar:  pip install flet numpy scipy mysql-connector-python
Correr:    python main.py
APK:       flet build apk
iOS:       flet build ipa
"""

import flet as ft
import numpy as np
import threading

# ── Importar módulo de base de datos ──────────────────────
from database import (
    init_db, #base
    get_municipios,
    get_estadisticas_municipio,
    guardar_calculo,
    guardar_encuesta,
)

# ═══════════════════════════════════════════════════════════
#  PALETA DE COLORES
# ═══════════════════════════════════════════════════════════
BG       = "#0a0e1a"
SURFACE  = "#111827"
CARD     = "#161f35"
BORDER   = "#1e2d4a"
ACCENT   = "#00e5c8"
ACCENT2  = "#ff6b35"
ACCENT3  = "#7c3aed"
LOW      = "#10b981"
MID      = "#f59e0b"
HIGH     = "#ef4444"
TEXT     = "#e8edf5"
MUTED    = "#6b7fa3"
WHITE    = "#ffffff"

# ═══════════════════════════════════════════════════════════
#  MODELO MATEMÁTICO IARRI-MX
# ═══════════════════════════════════════════════════════════
WEIGHTS = {"AV": 0.20, "IC": 0.25, "ED": 0.15, "EAR": 0.25, "IM": 0.15}
#indice de IARRI (indice arquitectonico de insulina)
# MUNICIPIOS se carga desde la BD en tiempo de ejecución
MUNICIPIOS = []

VARIABLES = [
    {"key": "AV",  "label": "Áreas Verdes",                     "icon": "🌳", "color": LOW,    "inv": True,  "desc": "Estándar OMS 9 m²/hab"},
    {"key": "IC",  "label": "Índice Caminabilidad",              "icon": "🚶", "color": ACCENT, "inv": True,  "desc": "Intersecciones + banquetas"},
    {"key": "ED",  "label": "Entrenamientos con Actividad Fisica","icon": "⚽", "color": ACCENT3,"inv": True,  "desc": "Equipamientos / población"},
    {"key": "EAR", "label": "Habitos Alimentarios",              "icon": "🍟", "color": ACCENT2,"inv": False, "desc": "Tiendas ultraprocesados / total"},
    {"key": "IM",  "label": "Índice de Marginación",             "icon": "📉", "color": MID,    "inv": False, "desc": "CONAPO normalizado"},
]

RECOMENDACIONES = [
    {"icon": "🌳", "color": LOW,    "titulo": "Incrementar Áreas Verdes",    "desc": "Corredores verdes y microparques. AV: 0.30 → 0.55", "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🚶", "color": ACCENT, "titulo": "Ruta Diaria de 15 min",       "desc": "Banquetas accesibles e iluminación. IC: 0.20 → 0.45", "impacto": "↓ IARRI −0.0625 (−8%)"},
    {"icon": "⚽", "color": ACCENT3,"titulo": "Espacios Deportivos",          "desc": "2 unidades barriales abiertas. ED: 0.10 → 0.30", "impacto": "↓ IARRI −0.03 (−3.8%)"},
    {"icon": "🏗️", "color": ACCENT2,"titulo": "Regulación Alimentaria",      "desc": "Reducir ultraprocesados. EAR: 0.80 → 0.60", "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🪟", "color": MID,    "titulo": "Diseño Arquitectónico",        "desc": "Ventilación cruzada y acceso escaleras", "impacto": "Compensación: +18%"},
]

BADGES = [
    {"emoji": "🏛️", "nombre": "Arquitecto Preventivo", "earned": True},
    {"emoji": "🌱", "nombre": "Diseñador Bioactivo",    "earned": True},
    {"emoji": "⚡", "nombre": "Agente Metabólico",      "earned": False},
    {"emoji": "📊", "nombre": "Analista Territorial",   "earned": False},
    {"emoji": "🗺️", "nombre": "Mapeador Urbano",        "earned": True},
    {"emoji": "🔬", "nombre": "Investigador IARRI",     "earned": False},
]


# ═══════════════════════════════════════════════════════════
#  FUNCIONES MATEMÁTICAS
# ═══════════════════════════════════════════════════════════
def calc_iarri(AV, IC, ED, EAR, IM):
    return (WEIGHTS["AV"]*(1-AV) + WEIGHTS["IC"]*(1-IC) +
            WEIGHTS["ED"]*(1-ED) + WEIGHTS["EAR"]*EAR + WEIGHTS["IM"]*(1-IM))
#AV = Areas verdes 
#IC = Indice de caminos-trayectos
#ED = Entrenamiento deportivo 
#EAR= Entorno alimentario
#IM = Indice de marginacion 
def nivel_riesgo(v):
    if v <= 0.33 -1: return "Bajo",  LOW
    if v <= 0.66: return "Medio", MID
    return               "Alto",  HIGH

def prob_ri(v):
    return min(1.0, 0.10 + 0.50 * v)

def monte_carlo(base, n=1000, sigma=0.12):
    res = []
    for _ in range(n):
        v = {k: max(0, min(1, base[k] + np.random.uniform(-sigma, sigma)))
             for k in ["AV","IC","ED","EAR","IM"]}
        res.append(calc_iarri(**v))
    arr = np.array(res)
    return arr, arr.mean(), arr.std(), np.percentile(arr,2.5), np.percentile(arr,97.5)

# ═══════════════════════════════════════════════════════════
#  CARGA DE MUNICIPIOS DESDE BD
# ═══════════════════════════════════════════════════════════
def cargar_municipios_bd():
    """Carga municipios desde MySQL y actualiza la lista global."""
    global MUNICIPIOS
    datos = get_municipios()
    if datos:
        MUNICIPIOS = datos
        print(f"[DB] {len(MUNICIPIOS)} municipios cargados desde MySQL ✓")
    else:
        # Fallback a datos hardcoded si no hay conexión
        MUNICIPIOS = [#cambios
            {"id": None, "nombre": "San Andrés Cholula",      "AV": 0.80, "IC": 0.60, "ED": 0.40, "EAR": 0.45, "IM": 0.10},
            {"id": None, "nombre": "Tehuacan", "AV": 0.50, "IC": 0.35, "ED": 0.20, "EAR": 0.60, "IM": 0.55},
            {"id": None, "nombre": "Cuautlancingo",           "AV": 0.30, "IC": 0.20, "ED": 0.10, "EAR": 0.80, "IM": 0.70},
            {"id": None, "nombre": "San Andres Cholula",      "AV": 0.30, "IC": 0.20, "ED": 0.10, "EAR": 0.80, "IM": 0.70},
        ]
        print("[DB] ⚠ Sin conexión MySQL, usando datos locales")


# ═══════════════════════════════════════════════════════════
#  COMPONENTES UI REUTILIZABLES
# ═══════════════════════════════════════════════════════════
def tarjeta(content, padding=14, color=CARD, border=True):
    return ft.Container(
        content=content,
        bgcolor=color,
        border_radius=16,
        padding=padding,
        border=ft.border.all(1, BORDER) if border else None,
    )

def titulo_seccion(texto):
    return ft.Text(texto, size=11, weight=ft.FontWeight.BOLD,
                   color=MUTED, font_family="monospace")

def badge_riesgo(nivel, color):
    return ft.Container(
        content=ft.Row([
            ft.Container(width=8, height=8, border_radius=4, bgcolor=color),
            ft.Text(f"Riesgo {nivel}", size=12, weight=ft.FontWeight.BOLD, color=color),
        ], spacing=6, tight=True),
        bgcolor=color + "22",
        border=ft.border.all(1, color + "55"),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=12, vertical=5),
    )


# ═══════════════════════════════════════════════════════════
#  PANTALLA 1 — INICIO  (con estadísticas BD)
# ═══════════════════════════════════════════════════════════
def build_inicio(page, state):
    muni_idx = state["muni_idx"]
    muni     = MUNICIPIOS[muni_idx]
    iarri    = calc_iarri(muni["AV"], muni["IC"], muni["ED"], muni["EAR"], muni["IM"])
    nivel, col = nivel_riesgo(iarri)

    def cambiar_muni(idx):
        state["muni_idx"] = idx
        state["refresh"]()

    chips = ft.Row([
        ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(
                    m["nombre"],
                    size=11, weight=ft.FontWeight.W_600,
                    color="#000000" if i == muni_idx else MUTED),
                bgcolor=ACCENT if i == muni_idx else CARD,
                border=ft.border.all(1, ACCENT if i == muni_idx else BORDER),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
            ),
            on_tap=lambda e, i=i: cambiar_muni(i),
        )
        for i, m in enumerate(MUNICIPIOS)
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

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

    # ── Estadísticas BD ────────────────────────────────────
    stats_txt = ft.Text("Cargando estadísticas...", size=10, color=MUTED)
    stats_card = tarjeta(ft.Column([
        ft.Text("📊 Datos históricos (MySQL)", size=12, weight=ft.FontWeight.BOLD, color=TEXT),
        stats_txt,
    ], spacing=6))

    def cargar_stats():
        muni_id = muni.get("id")
        if muni_id:
            s = get_estadisticas_municipio(muni_id)
            if s and s.get("total_calculos"):
                stats_txt.value = (
                    f"Total cálculos: {s['total_calculos']}  |  "
                    f"IARRI prom: {(s['iarri_promedio'] or 0):.3f}  |  "
                    f"Prob.RI prom: {(s['prob_ri_promedio'] or 0)*100:.1f}%\n"
                    f"Riesgo Bajo: {s['casos_bajo']}  Medio: {s['casos_medio']}  Alto: {s['casos_alto']}"
                )
            else:
                stats_txt.value = "Sin datos históricos aún. Usa la calculadora para generar registros."
        else:
            stats_txt.value = "Sin conexión a BD. Revisa database.py"
        page.update()

    threading.Thread(target=cargar_stats, daemon=True).start()

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
                ft.Text("Probabilidad de Resistencia a la Insulina:", size=12, color=MUTED),
                ft.Text(f"{prob_ri(iarri)*100:.1f}%", size=14,
                        weight=ft.FontWeight.BOLD, color=col),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1,-1),
            end=ft.alignment.Alignment(1,1),
            colors=["#0f2441", "#1a0a2e"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=22,
        padding=20,
        margin=ft.margin.only(bottom=12),
    )

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
                    ft.Text(f"{val:.2f}", size=20, weight=ft.FontWeight.W_900, color=v["color"]),
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
    
    def calcula_derivadas(muni):
        AV = muni["AV"]
        IC = muni["IC"]
        ED = muni["ED"]
        EAR = muni["EAR"]
        IM  = muni["IM"]    
        
        total = AV + IC + ED + EAR + IM
        
        return {
            "IC": IC / total,
            "EAR": EAR / total,
            "AV": AV / total,
            "ED": ED / total,
            "IM": IM / total, 
        }
        
    derivadas = calcula_derivadas(muni) #recuerda que muni es el arreglo para municipios
    sens_items = [
            
        ("IC",  derivadas["IC"], ACCENT,  "Mayor impacto de movilidad continua"),
        ("EAR", derivadas["EAR"], ACCENT2,"Mayor impacto (riesgo)"),
        ("AV",  derivadas["AV"], LOW,     "Impacto medio"),
        ("ED",  derivadas["ED"], ACCENT3, "Impacto moderado"),  
        ("IM",  derivadas["IM"], MID,     "Impacto moderado"),
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

    sens_card = tarjeta(ft.Column([
        ft.Text("∂IARRI — Totales Estadisticos", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        ft.Text("Mayor impacto: Caminabilidad (movimientos) y Entorno Alimentario ", size=10, color=MUTED),
        *sens_rows,
    ], spacing=8))

    formula_card = tarjeta(ft.Column([
        ft.Text("Fórmula del Modelo", size=3, color=MUTED), 
        ft.Text("IARRI = Areas Verdes + Indice de camino\n+ Entrenamiento(fisico) + Entorno alimentario + Indice de Marginacion",
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

    return ft.Column([
        hero,
        titulo_seccion("VARIABLES TERRITORIALES"),
        ft.Container(height=8),
        grid_row1, ft.Container(height=8), grid_row2,
        ft.Container(height=8), grid_row3,
        ft.Container(height=14),
        titulo_seccion("DATOS HISTÓRICOS — MySQL"),
        ft.Container(height=6),
        stats_card,
        ft.Container(height=14),
        titulo_seccion("ANÁLISIS DE SENSIBILIDAD"),
        ft.Container(height=6),
        sens_card,
        ft.Container(height=10),
        formula_card,
        ft.Container(height=20),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 2 — MAPA / COMPARACIÓN
# ═══════════════════════════════════════════════════════════
def build_mapa(page, state):
    # Calcular IARRI real de cada municipio
    iarri_munis = {m["nombre"]: calc_iarri(m["AV"],m["IC"],m["ED"],m["EAR"],m["IM"]) for m in MUNICIPIOS}
    nombres_cortos = {m["nombre"]: m["nombre"].split()[1] if len(m["nombre"].split()) > 1 else m["nombre"].split()[0] for m in MUNICIPIOS}

    def label_mapa(nombre, color, left, top):
        iv = iarri_munis.get(nombre, 0)
        return ft.Container(content=ft.Column([
            ft.Text(nombres_cortos.get(nombre, nombre), size=10, weight=ft.FontWeight.BOLD, color=color),
            ft.Text(f"IARRI: {iv:.2f}", size=8, color=MUTED),
        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER), left=left, top=top)

    n0 = MUNICIPIOS[0]["nombre"] if len(MUNICIPIOS) > 0 else ""
    n1 = MUNICIPIOS[1]["nombre"] if len(MUNICIPIOS) > 1 else ""
    n2 = MUNICIPIOS[2]["nombre"] if len(MUNICIPIOS) > 2 else ""
    c0 = LOW  if iarri_munis.get(n0,0) <= 0.33 else (MID if iarri_munis.get(n0,0) <= 0.66 else HIGH)
    c1 = LOW  if iarri_munis.get(n1,0) <= 0.33 else (MID if iarri_munis.get(n1,0) <= 0.66 else HIGH)
    c2 = LOW  if iarri_munis.get(n2,0) <= 0.33 else (MID if iarri_munis.get(n2,0) <= 0.66 else HIGH)

    mapa_svg = ft.Container(
        content=ft.Stack([
            ft.Container(bgcolor=CARD, expand=True, border_radius=16),
            ft.Container(width=140, height=110, border_radius=70, bgcolor=c0+"33", left=20, top=20),
            ft.Container(width=130, height=100, border_radius=65, bgcolor=c1+"33", left=130, top=60),
            ft.Container(width=150, height=110, border_radius=75, bgcolor=c2+"33", left=220, top=80),
            label_mapa(n0, c0, 20, 10),
            label_mapa(n1, c1, 145, 42),
            label_mapa(n2, c2, 228, 60),
            ft.Container(content=ft.Text("🌳", size=14), left=55, top=55),
            ft.Container(content=ft.Text("🌳", size=12), left=80, top=75),
            ft.Container(content=ft.Text("🍟", size=12), left=265, top=110),
            ft.Container(content=ft.Text("🍟", size=11), left=285, top=128),
            ft.Container(content=ft.Text("⚽", size=12), left=170, top=90),
        ]),
        height=175,
        border=ft.border.all(1, BORDER),
        border_radius=16,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        margin=ft.margin.only(bottom=8),
    )

    leyenda = ft.Row([
        ft.Row([ft.Container(width=10, height=10, border_radius=5, bgcolor=LOW),
                ft.Text("Áreas verdes", size=11, color=MUTED)], spacing=5),
        ft.Row([ft.Container(width=10, height=10, border_radius=5, bgcolor=HIGH),
                ft.Text("Ultraprocesados", size=11, color=MUTED)], spacing=5),
        ft.Row([ft.Container(width=10, height=10, border_radius=5, bgcolor=ACCENT3),
                ft.Text("Deporte", size=11, color=MUTED)], spacing=5),
    ], spacing=14)

    munis_sorted = sorted(
        [{**m, "iarri": calc_iarri(m["AV"],m["IC"],m["ED"],m["EAR"],m["IM"])}
         for m in MUNICIPIOS],
        key=lambda x: x["iarri"]
    )
    muni_rows = []
    for i, m in enumerate(munis_sorted):
        niv, col = nivel_riesgo(m["iarri"])
        muni_rows.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(f"#{i+1}", size=18, weight=ft.FontWeight.W_900, color=MUTED, width=30),
                    ft.Column([
                        ft.Text(m["nombre"], size=13, weight=ft.FontWeight.W_600, color=TEXT),
                        ft.Container(
                            content=ft.Container(bgcolor=col, border_radius=3,
                                                  height=6, width=m["iarri"] * 200),
                            bgcolor=BORDER, border_radius=3, height=6,
                            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            margin=ft.margin.only(top=4),
                        ),
                    ], spacing=2, expand=True),
                    ft.Text(f"{m['iarri']:.2f}", size=18, weight=ft.FontWeight.W_900,
                            color=col, width=44),
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD, border=ft.border.all(1, BORDER),
                border_radius=14, padding=14, margin=ft.margin.only(bottom=8),
            )
        )

    def header_cell(txt, flex=1):
        return ft.Container(
            content=ft.Text(txt, size=10, color=MUTED, weight=ft.FontWeight.BOLD,
                            font_family="monospace"),
            expand=flex, padding=ft.padding.symmetric(vertical=8, horizontal=4),
            bgcolor=SURFACE,
        )

    def data_cell(txt, color=TEXT, flex=1, bold=False):
        return ft.Container(
            content=ft.Text(txt, size=11, color=color,
                            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL),
            expand=flex, padding=ft.padding.symmetric(vertical=8, horizontal=4),
            alignment=ft.alignment.Alignment(0,0),
        )

    tabla_header = ft.Row([
        header_cell("Municipio", 2),
        header_cell("IARRI"),
        header_cell("Prob.RI"),
        header_cell("Nivel", 1),
    ], spacing=1)

    tabla_rows = []
    for i, m in enumerate(MUNICIPIOS):
        iarri = calc_iarri(m["AV"],m["IC"],m["ED"],m["EAR"],m["IM"])
        niv, col = nivel_riesgo(iarri)
        pr = prob_ri(iarri)
        bg = CARD if i%2==0 else SURFACE
        parts = m["nombre"].split()
        name = parts[0] + (" " + parts[1] if len(parts) > 1 else "")
        tabla_rows.append(ft.Container(
            content=ft.Row([
                data_cell(name, flex=2),
                data_cell(f"{iarri:.2f}", color=col, bold=True),
                data_cell(f"{pr*100:.0f}%"),
                ft.Container(
                    content=ft.Container(
                        content=ft.Text(niv, size=10, color=col, weight=ft.FontWeight.BOLD),
                        bgcolor=col+"22", border=ft.border.all(1,col+"55"),
                        border_radius=8, padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                    expand=True, alignment=ft.alignment.Alignment(0,0),
                ),
            ], spacing=1),
            bgcolor=bg,
        ))

    tabla_card = tarjeta(ft.Column([
        ft.Text("Proyección Epidemiológica", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        tabla_header,
        ft.Divider(height=1, color=BORDER),
        *tabla_rows,
        ft.Divider(height=1, color=BORDER),
        ft.Text("Prob(RI) = 0.10 + 0.50 × IARRI  —  Modelo conceptual ENSANUT",
                size=9, color=MUTED, italic=True),
    ], spacing=2))

    return ft.Column([
        mapa_svg,
        leyenda,
        ft.Container(height=12),
        titulo_seccion("COMPARACIÓN MUNICIPAL"),
        ft.Container(height=8),
        *muni_rows,
        titulo_seccion("PROYECCIÓN EPIDEMIOLÓGICA"),
        ft.Container(height=8),
        tabla_card,
        ft.Container(height=20),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 3 — CALCULADORA + ENCUESTA + GUARDA EN BD
# ═══════════════════════════════════════════════════════════
def build_calculadora(page, state):
    slider_vals = {v["key"]: state.get(f"slider_{v['key']}", 0.0) for v in VARIABLES}
    result_txt  = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    nivel_txt   = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)
    prob_txt    = ft.Text("Prob. RI: —", size=12, color=MUTED)
    mc_btn_txt  = ft.Text("Simulación Monte Carlo (excepcion)", size=13,
                           weight=ft.FontWeight.BOLD, color="#000000")
    guardar_msg = ft.Text("", size=11, color=ACCENT)
    estilo_msg = ft.Text(
        "Pulsa 'Evaluar Estilo de Vida' para actualizar tus insignias según tu perfil.",
        size=10, color=MUTED, italic=True,
    )

    desglose_bars = {}
    desglose_rows = []
    for v in VARIABLES:
        bar_inner = ft.Container(bgcolor=v["color"], border_radius=3, height=7, width=0)
        bar_outer = ft.Container(
            content=bar_inner, bgcolor=BORDER, border_radius=3, height=7,
            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=38,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace")
        desglose_bars[v["key"]] = (bar_inner, val_lbl)
        desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=34,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_outer,
                val_lbl,
            ], spacing=6)
        )

    # Variables para Monte Carlo (accesible desde guardar)
    mc_resultados = {"media": None, "desv": None, "ci_lo": None, "ci_hi": None}

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
            "IM":  WEIGHTS["IM"]  * slider_vals["IM"],
        }
        for k, (bar, lbl) in desglose_bars.items():
            bar.width = contribs[k] * 600
            lbl.value = f"{contribs[k]:.3f}"
        page.update()

    def evaluar_estilo_vida(e=None):
        actividad = cb_activo.value
        camina = cb_camina.value
        ultra = cb_ultra.value
        verde = cb_verde.value
        min_ejer = int(min_field.value) if min_field.value else 0
        iarri = calc_iarri(**slider_vals)

        badges = []
        for b in BADGES:
            earned = False
            if b["nombre"] == "Arquitecto Preventivo":
                earned = (not ultra and slider_vals["EAR"] <= 0.5)
            elif b["nombre"] == "Diseñador Bioactivo":
                earned = verde and slider_vals["AV"] >= 0.5
            elif b["nombre"] == "Agente Metabólico":
                earned = actividad and (min_ejer >= 150 or camina)
            elif b["nombre"] == "Mapeador Urbano":
                earned = camina or slider_vals["IC"] >= 0.5
            elif b["nombre"] == "Analista Territorial":
                earned = camina and slider_vals["IM"] <= 0.5
            elif b["nombre"] == "Investigador IARRI":
                earned = mc_resultados["media"] is not None
            badges.append({**b, "earned": earned})

        state["badges"] = badges
        lifestyle = "Activo y Preventivo" if actividad and verde and not ultra else (
            "Moderado" if camina or actividad or verde else "Sedentario"
        )
        estilo_msg.value = f"Estilo de vida: {lifestyle}. Insignias actualizadas."
        estilo_msg.color = ACCENT if lifestyle == "Activo y Preventivo" else (MID if lifestyle == "Moderado" else HIGH)
        page.update()

    slider_widgets = []
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

    slider_val_lbls = {k: lbl for k, lbl, _ in slider_widgets}

    # ── IARRI del municipio seleccionado ──────────────────
    muni_iarri_val  = calc_iarri(**{k: MUNICIPIOS[state["muni_idx"]][k] for k in ["AV","IC","ED","EAR","IM"]})
    muni_niv, muni_col = nivel_riesgo(muni_iarri_val)
    muni_iarri_txt  = ft.Text(f"{muni_iarri_val:.4f}", size=38, weight=ft.FontWeight.W_900, color=muni_col)
    muni_nivel_txt  = ft.Text(f"● Riesgo {muni_niv}", size=13, weight=ft.FontWeight.BOLD, color=muni_col)
    muni_prob_txt   = ft.Text(f"Prob. RI: {prob_ri(muni_iarri_val)*100:.1f}%", size=12, color=muni_col)
    muni_nombre_txt = ft.Text(MUNICIPIOS[state["muni_idx"]]["nombre"], size=13, color=MUTED)

    muni_iarri_card = ft.Container(
        content=ft.Row([
            ft.Column([
                muni_nombre_txt,
                muni_iarri_txt,
            ], spacing=2),
            ft.Column([
                muni_nivel_txt,
                muni_prob_txt,
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=14,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    preset_buttons_refs = []
    preset_activo = [state.get("muni_idx", 0)]  # índice activo

    def set_preset(idx):
        m = MUNICIPIOS[idx]
        for v in VARIABLES:
            slider_vals[v["key"]] = m[v["key"]]
            state[f"slider_{v['key']}"] = m[v["key"]]
        for k, lbl, s in slider_widgets:
            lbl.value = f"{slider_vals[k]:.2f}"
            s.value   = slider_vals[k]
        # Actualizar card IARRI del municipio
        iv = calc_iarri(**{k: m[k] for k in ["AV","IC","ED","EAR","IM"]})
        nv, cv = nivel_riesgo(iv)
        muni_iarri_txt.value  = f"{iv:.4f}"
        muni_iarri_txt.color  = cv
        muni_nivel_txt.value  = f"● Riesgo {nv}"
        muni_nivel_txt.color  = cv
        muni_prob_txt.value   = f"Prob. RI: {prob_ri(iv)*100:.1f}%"
        muni_prob_txt.color   = cv
        muni_nombre_txt.value = m["nombre"]
        # Resaltar botón activo
        prev = preset_activo[0]
        preset_activo[0] = idx
        for j, btn in enumerate(preset_buttons_refs):
            iv_j = calc_iarri(MUNICIPIOS[j]["AV"], MUNICIPIOS[j]["IC"],
                               MUNICIPIOS[j]["ED"], MUNICIPIOS[j]["EAR"], MUNICIPIOS[j]["IM"])
            _, col_j = nivel_riesgo(iv_j)
            btn.style = ft.ButtonStyle(
                bgcolor=ACCENT+"33" if j == idx else CARD,
                color=TEXT,
                side=ft.BorderSide(2 if j == idx else 1,
                                   ACCENT if j == idx else col_j + "66"),
            )
        actualizar_resultado()

    preset_buttons = []
    for i, m in enumerate(MUNICIPIOS):
        def make_on_click(idx):
            return lambda e: set_preset(idx)
        partes  = m["nombre"].split()
        # Mostrar primeras 2 palabras (caben en el botón con scroll)
        etiqueta = " ".join(partes[:2]) if len(partes) >= 2 else partes[0]
        iarri_m  = calc_iarri(m["AV"], m["IC"], m["ED"], m["EAR"], m["IM"])
        _, col_m = nivel_riesgo(iarri_m)
        es_activo = (i == state.get("muni_idx", 0))
        btn = ft.FilledTonalButton(
            content=ft.Column([
                ft.Text(etiqueta, size=11, weight=ft.FontWeight.W_600,
                        color=TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text(f"IARRI {iarri_m:.2f}", size=10,
                        color=col_m, text_align=ft.TextAlign.CENTER),
            ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=make_on_click(i),
            style=ft.ButtonStyle(
                bgcolor=ACCENT+"33" if es_activo else CARD,
                color=TEXT,
                side=ft.BorderSide(2 if es_activo else 1,
                                   ACCENT if es_activo else col_m + "66"),
            ),
        )
        preset_buttons.append(btn)
        preset_buttons_refs.append(btn)

    presets_row = ft.Row(preset_buttons, spacing=8, scroll=ft.ScrollMode.AUTO)

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
            ft.Text("" if v["inv"] else "",
                    size=9, color=v["color"], italic=True),
        ], spacing=2), padding=14)
        slider_cards.append(card)

    # ── Botón guardar en BD ────────────────────────────────
    def guardar_en_bd(e):#automatizar
        iarri = calc_iarri(**slider_vals)
        niv, _ = nivel_riesgo(iarri)
        pr = prob_ri(iarri)
        muni = MUNICIPIOS[state["muni_idx"]]

        def _save():
            rid = guardar_calculo(
                municipio_id=muni.get("id"),
                AV=slider_vals["AV"], IC=slider_vals["IC"],
                ED=slider_vals["ED"], EAR=slider_vals["EAR"],
                IM=slider_vals["IM"],
                iarri=iarri, nivel=niv, prob=pr,
                mc_media=mc_resultados["media"],
                mc_desv=mc_resultados["desv"],
                mc_ci_lo=mc_resultados["ci_lo"],
                mc_ci_hi=mc_resultados["ci_hi"],
                origen="calculadora"
            )
            if rid:
                guardar_msg.value = f"✓ Guardado en MySQL (ID: {rid})"
                guardar_msg.color = ACCENT
            else:
                guardar_msg.value = "⚠ No se pudo guardar. Revisa la conexión."
                guardar_msg.color = HIGH
            page.update()

        threading.Thread(target=_save, daemon=True).start()
        guardar_msg.value = "Guardando..."
        page.update()

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
            # Botón guardar
            ft.ElevatedButton(
                content=ft.Text("💾  Guardar en MySQL", size=13,
                                 weight=ft.FontWeight.BOLD, color="#000000"),
                bgcolor=LOW,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                height=46,
                expand=True,
                on_click=guardar_en_bd,
            ),
            guardar_msg,
            ft.ElevatedButton(
                content=ft.Text("🧠  Evaluar Estilo de Vida", size=13,
                                 weight=ft.FontWeight.BOLD, color="#000000"),
                bgcolor=ACCENT3,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                height=46,
                expand=True,
                on_click=evaluar_estilo_vida,
            ),
            estilo_msg,
            ft.Divider(height=1, color=BORDER),
            ft.ElevatedButton(
                content=mc_btn_txt,
                bgcolor=ACCENT,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                height=46,
                expand=True,
                on_click=lambda e: run_mc(e),
            ),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1,-1),
            end=ft.alignment.Alignment(1,1),
            colors=["#0f2441","#1a0a2e"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    mc_mean_txt = ft.Text("", size=12, color=ACCENT, font_family="monospace")
    mc_std_txt  = ft.Text("", size=12, color=ACCENT3, font_family="monospace")
    mc_ci_txt   = ft.Text("", size=12, color=MID, font_family="monospace")
    mc_hist     = ft.Row([], spacing=2, height=80, vertical_alignment=ft.CrossAxisAlignment.END)

    mc_card = ft.Container(
        content=ft.Column([
            ft.Text("📊 Monte Carlo — 1000 simulaciones", size=13,
                    weight=ft.FontWeight.BOLD, color=TEXT),
            ft.Text("σ = ±0.12 perturbación aleatoria por variable", size=10, color=MUTED),
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

    def run_mc(e):
        mc_btn_txt.value = "⏳  Calculando..."
        page.update()

        def _task():
            res, media, desv, ci_lo, ci_hi = monte_carlo(slider_vals, 1000, 0.12)
            mc_resultados.update({"media": media, "desv": desv, "ci_lo": ci_lo, "ci_hi": ci_hi})
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

    # ── Sección encuesta ───────────────────────────────────
    nombre_field = ft.TextField(
        label="Tu nombre (opcional)", hint_text="Anónimo",
        bgcolor=CARD, border_color=BORDER, color=TEXT,
        label_style=ft.TextStyle(color=MUTED), height=50,
    )
    edad_field = ft.TextField(
        label="Edad", hint_text="Ej: 28",
        bgcolor=CARD, border_color=BORDER, color=TEXT,
        label_style=ft.TextStyle(color=MUTED), height=50,
        keyboard_type=ft.KeyboardType.NUMBER, width=100,
    )
    cb_activo   = ft.Checkbox(label="Hago ejercicio regularmente", value=False, active_color=ACCENT)
    cb_ultra    = ft.Checkbox(label="Consumo ultraprocesados frecuentemente", value=False, active_color=ACCENT2)
    cb_verde    = ft.Checkbox(label="Tengo acceso a áreas verdes cerca", value=False, active_color=LOW)
    cb_camina   = ft.Checkbox(label="Camino más de 20 min al día", value=False, active_color=ACCENT3)
    min_field   = ft.TextField(
        label="Min ejercicio/semana", hint_text="Ej: 150",
        bgcolor=CARD, border_color=BORDER, color=TEXT,
        label_style=ft.TextStyle(color=MUTED), height=50,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    enc_msg = ft.Text("", size=11, color=ACCENT)

    def guardar_encuesta_click(e):
        muni = MUNICIPIOS[state["muni_idx"]]
        iarri = calc_iarri(**slider_vals)
        niv, _ = nivel_riesgo(iarri)
        pr = prob_ri(iarri)

        datos = {
            "municipio_id":           muni.get("id"),
            "nombre_usuario":         nombre_field.value or "Anónimo",
            "edad":                   int(edad_field.value) if edad_field.value else None,
            "genero":                 None,
            "actividad_fisica":       int(cb_activo.value),
            "min_ejercicio_sem":      int(min_field.value) if min_field.value else 0,
            "consume_ultraprocesados":int(cb_ultra.value),
            "acceso_areas_verdes":    int(cb_verde.value),
            "camina_diario":          int(cb_camina.value),
            "AV_enc":                 slider_vals["AV"],
            "IC_enc":                 slider_vals["IC"],
            "ED_enc":                 slider_vals["ED"],
            "EAR_enc":                slider_vals["EAR"],
            "IM_enc":                 slider_vals["IM"],
            "iarri_resultado":        iarri,
            "nivel_riesgo":           niv,
            "prob_ri":                pr,
        }

        def _save():
            eid = guardar_encuesta(datos)
            if eid:
                enc_msg.value = f"✓ Encuesta guardada (ID: {eid})"
                enc_msg.color = ACCENT
            else:
                enc_msg.value = "⚠ Error al guardar. Revisa la conexión MySQL."
                enc_msg.color = HIGH
            page.update()

        threading.Thread(target=_save, daemon=True).start()
        enc_msg.value = "Guardando encuesta..."
        page.update()

    encuesta_card = tarjeta(ft.Column([
        ft.Text("📋 Encuesta de Hábitos", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        ft.Text("Tus respuestas se guardan en la BD y mejoran el modelo",
                size=10, color=MUTED),
        ft.Row([nombre_field, edad_field], spacing=8),
        cb_activo, min_field, cb_ultra, cb_verde, cb_camina,
        ft.ElevatedButton(
            content=ft.Text("📤  Enviar Encuesta", size=13,
                             weight=ft.FontWeight.BOLD, color="#000000"),
            bgcolor=ACCENT3,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            height=46, expand=True,
            on_click=guardar_encuesta_click,
        ),
        enc_msg,
    ], spacing=10))

    return ft.Column([
        titulo_seccion("SELECCION DE MUNICIPIO"),
        ft.Container(height=6),
        presets_row,
        ft.Container(height=8),
        titulo_seccion("IARRI DEL MUNICIPIO ESTIMADO"),
        ft.Container(height=6),
        muni_iarri_card,
        ft.Container(height=8),
        #tarjeta(ft.Text(
            #"IARRI = 0.20(1−AV) + 0.25(1−IC) + 0.15(1−ED) + 0.25(EAR) + 0.15(IM)",
            #size=10, color=ACCENT, font_family="monospace",
        #)),
        ft.Container(height=10),
        titulo_seccion("EVALUACION DE HABITOS DE RESISTENCIA"),
        ft.Container(height=6),
        *slider_cards,
        ft.Container(height=10),
        resultado_card,
        ft.Container(height=10),
        mc_card,
        ft.Container(height=12),
        titulo_seccion("ENCUESTA PERSONAL"),
        ft.Container(height=6),
        encuesta_card,
        ft.Container(height=20),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)


# ═══════════════════════════════════════════════════════════
#  PANTALLA 4 — RECOMENDACIONES + GAMIFICACIÓN
# ═══════════════════════════════════════════════════════════
def build_recomendaciones(page, state):
    # Calcular valores reales del municipio de mayor riesgo
    muni_actual = MUNICIPIOS[state["muni_idx"]] if MUNICIPIOS else {}
    iarri_antes  = calc_iarri(muni_actual.get("AV",0.3), muni_actual.get("IC",0.2),
                               muni_actual.get("ED",0.1), muni_actual.get("EAR",0.8),
                               muni_actual.get("IM",0.7))
    # Simulación post-intervención: mejora AV, IC, ED
    iarri_despues = calc_iarri(
        min(1, muni_actual.get("AV",0.3) + 0.25),
        min(1, muni_actual.get("IC",0.2) + 0.25),
        min(1, muni_actual.get("ED",0.1) + 0.20),
        muni_actual.get("EAR",0.8),
        muni_actual.get("IM",0.7),
    )
    reduccion_pct = ((iarri_antes - iarri_despues) / iarri_antes * 100) if iarri_antes > 0 else 0
    badges = state.get("badges", BADGES)
    badges_ganadas = sum(1 for b in badges if b["earned"])

    kpis = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text(f"{reduccion_pct:.1f}%", size=22, weight=ft.FontWeight.W_900, color=ACCENT),
                ft.Text("Reducción", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
            padding=12, expand=True,
        ),
        ft.Container(
            content=ft.Column([#ARRIBA
                ft.Text(f"{iarri_antes:.2f}→{iarri_despues:.2f}", size=16, weight=ft.FontWeight.W_900, color=MID),
                ft.Text("IARRI post-interv.", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
            padding=12, expand=True,
        ),
        ft.Container(
            content=ft.Column([
                ft.Text(str(badges_ganadas), size=22, weight=ft.FontWeight.W_900, color=ACCENT3),
                ft.Text("Insignias", size=10, color=MUTED, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=CARD, border=ft.border.all(1,BORDER), border_radius=14,
            padding=12, expand=True,
        ),
    ], spacing=8)

    rec_cards = []
    for r in RECOMENDACIONES:
        body = ft.Container(
            content=ft.Column([
                ft.Text(r["desc"], size=12, color=MUTED),
                ft.Container(
                    content=ft.Text(r["impacto"], size=11, color=r["color"],
                                    weight=ft.FontWeight.BOLD),
                    bgcolor=r["color"]+"11", border=ft.border.all(1, r["color"]+"33"),
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

    nombre_sim = muni_actual.get("nombre", "Municipio")
    av_a  = muni_actual.get("AV", 0.30)
    ic_a  = muni_actual.get("IC", 0.20)
    ed_a  = muni_actual.get("ED", 0.10)
    av_d  = min(1.0, av_a + 0.25)
    ic_d  = min(1.0, ic_a + 0.25)
    ed_d  = min(1.0, ed_a + 0.20)
    cambios = [
        ("AV", f"{av_a:.2f}→{av_d:.2f}", LOW),
        ("IC", f"{ic_a:.2f}→{ic_d:.2f}", ACCENT),
        ("ED", f"{ed_a:.2f}→{ed_d:.2f}", ACCENT3),
    ]
    niv_antes,  col_antes  = nivel_riesgo(iarri_antes)
    niv_despues, col_despues = nivel_riesgo(iarri_despues)

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
        ft.Text(f"Simulación: {nombre_sim}", size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        *sim_rows,
        ft.Divider(height=1, color=BORDER),
        ft.Row([
            ft.Column([
                ft.Text("Antes", size=10, color=MUTED),
                ft.Text(f"{iarri_antes:.2f}", size=28, weight=ft.FontWeight.W_900, color=col_antes),
                ft.Text(niv_antes, size=11, color=col_antes),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("→", size=24, color=ACCENT),
            ft.Column([
                ft.Text("Después", size=10, color=MUTED),
                ft.Text(f"{iarri_despues:.2f}", size=28, weight=ft.FontWeight.W_900, color=col_despues),
                ft.Text(niv_despues, size=11, color=col_despues),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Reducción", size=10, color=MUTED),
                ft.Text(f"−{reduccion_pct:.1f}%", size=28, weight=ft.FontWeight.W_900, color=ACCENT),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
        ft.Container(
            content=ft.Text("↓ Potencial preventivo del diseño urbano (ENSANUT)",
                             size=11, color=ACCENT, text_align=ft.TextAlign.CENTER),
            bgcolor=ACCENT+"11", border=ft.border.all(1,ACCENT+"33"),
            border_radius=10, padding=10,
        ),
    ], spacing=10))

    badge_items = []
    for b in badges:
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
                border_radius=14, padding=12, expand=True,
            )
        )

    badges_grid = ft.Column([
        ft.Row(badge_items[:3], spacing=8),
        ft.Row(badge_items[3:], spacing=8),
    ], spacing=8)

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
#  APP PRINCIPAL
# ═══════════════════════════════════════════════════════════
def main(page: ft.Page):
    page.title       = "ARQ-Metabólica MX"
    page.bgcolor     = BG
    page.padding     = 0
    page.theme_mode  = ft.ThemeMode.DARK
    page.fonts       = {}
    page.window.width  = 400
    page.window.height = 800

    # ── Inicializar BD y cargar datos ─────────────────────
    init_db()
    cargar_municipios_bd()

    state = {
        "muni_idx": 0,
        "tab": 0,
        "refresh": None,
        "badges": [dict(b) for b in BADGES],
    }

    content_area = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    nav_labels = ["Inicio","Mapa","Calcular","Intervención"]
    nav_icons  = ["🏠","🗺️","🧮","🛡️"]
    nav_items  = []

    def build_screen(idx):
        builders = [build_inicio, build_mapa, build_calculadora, build_recomendaciones]
        return builders[idx](page, state)

    def switch_tab(idx):
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

    for i in range(4):
        nav_items.append(make_nav(i))

    nav_bar = ft.Container(
        content=ft.Row(nav_items, expand=True,
                        alignment=ft.MainAxisAlignment.SPACE_AROUND),
        bgcolor=SURFACE,
        border=ft.border.only(top=ft.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(vertical=10),
        height=62,
    )

    top_bar = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text("ARQ-Metabólica MX", size=18, weight=ft.FontWeight.W_900, color=ACCENT),
                ft.Text("IARRI-MX  ·  Puebla, México", size=11, color=MUTED),
            ], spacing=0),
            ft.Container(
                content=ft.Text("v2.0 DB", size=11, color=ACCENT, weight=ft.FontWeight.BOLD),
                bgcolor=ACCENT+"22", border=ft.border.all(1,ACCENT+"44"),
                border_radius=8, padding=ft.padding.symmetric(horizontal=10, vertical=4),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
    )

    content_area.content = build_screen(0)

    page.add(
        ft.Column([
            top_bar,
            ft.Container(content=content_area, expand=True),
            nav_bar,
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
