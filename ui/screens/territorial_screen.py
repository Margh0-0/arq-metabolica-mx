"""
ui/screens/territorial_screen.py
Módulo: Análisis Territorial — Datos Abiertos INEGI

Cruza 5 variables territoriales:
  · Densidad poblacional
  · Acceso a áreas verdes
  · Índices de marginación
  · Acceso a equipamiento deportivo
  · Movilidad peatonal

Salida: "Perfil metabólico ambiental de tu colonia"
"""

import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import calc_iarri, nivel_riesgo, prob_ri
from core.datos import MUNICIPIOS, DATOS_TERRITORIALES


# ─── HELPERS SEMÁNTICOS ──────────────────────────────────────────────────────

def _color_var(valor: float, inversa: bool = True) -> str:
    """Inversa=True: valor alto es BUENO (áreas verdes, caminabilidad).
    Inversa=False: valor alto es MALO (marginación, ultraprocesados)."""
    riesgo = (1 - valor) if inversa else valor
    return LOW if riesgo < 0.33 else MID if riesgo < 0.66 else HIGH


def _diagnostico_colonia(col: dict) -> dict:
    """
    Genera el diagnóstico narrativo completo de una colonia
    cruzando las 5 variables. Retorna un dict con:
    - nivel_general: "bajo" | "medio" | "alto" | "critico"
    - color_general: hex
    - titulo: frase de diagnóstico
    - subtitulo: contexto breve
    - alertas: lista de alertas específicas por variable
    - fortalezas: lista de puntos positivos
    - recomendaciones: lista de acciones concretas
    """
    av   = col.get("av", 0.5)
    ic   = col.get("ic", 0.5)
    ed   = col.get("ed", 0.5)
    ear  = col.get("ear", 0.5)
    imp  = col.get("imp", 0.5)
    iarri = col.get("iarri", calc_iarri(av, ic, ed, ear, imp))

    alertas = []
    fortalezas = []
    recomendaciones = []

    # ── Áreas verdes ──────────────────────────────────────────
    av_m2 = col.get("areas_verdes_m2", av * 9)
    if av_m2 < 3.0:
        alertas.append({
            "emoji": "🌳", "color": HIGH,
            "texto": f"Áreas verdes críticas: {av_m2:.1f} m²/hab (OMS: 9 m²)",
            "impacto": "Reduce actividad física espontánea hasta 40%",
        })
        recomendaciones.append("🌱 Exigir microparques o corredores verdes en la colonia")
    elif av_m2 < 6.0:
        alertas.append({
            "emoji": "🌳", "color": MID,
            "texto": f"Áreas verdes insuficientes: {av_m2:.1f} m²/hab",
            "impacto": "Por debajo del estándar OMS",
        })
        recomendaciones.append("🌳 Aprovechar áreas verdes existentes para actividad diaria")
    else:
        fortalezas.append(f"🌳 Buen acceso a áreas verdes: {av_m2:.1f} m²/hab")

    # ── Movilidad peatonal ────────────────────────────────────
    movil = col.get("movilidad_peat", ic * 0.8)
    if movil < 0.30:
        alertas.append({
            "emoji": "🚶", "color": HIGH,
            "texto": f"Movilidad peatonal muy deficiente: {movil*100:.0f}% banquetas accesibles",
            "impacto": "El entorno disuade caminar como hábito diario",
        })
        recomendaciones.append("🚶 Reportar banquetas en mal estado al municipio")
    elif movil < 0.55:
        alertas.append({
            "emoji": "🚶", "color": MID,
            "texto": f"Movilidad peatonal limitada: {movil*100:.0f}% de banquetas en buen estado",
            "impacto": "Reduce el ejercicio involuntario cotidiano",
        })
    else:
        fortalezas.append(f"🚶 Buena infraestructura peatonal: {movil*100:.0f}% accesible")

    # ── Equipamiento deportivo ────────────────────────────────
    equip = col.get("equipamiento_dep", ed * 6)
    if equip < 1.0:
        alertas.append({
            "emoji": "⚽", "color": HIGH,
            "texto": f"Equipamiento deportivo casi nulo: {equip:.1f}/10k hab",
            "impacto": "Sin infraestructura para actividad física estructurada",
        })
        recomendaciones.append("⚽ Gestionar acceso a instalaciones deportivas públicas cercanas")
    elif equip < 3.0:
        alertas.append({
            "emoji": "⚽", "color": MID,
            "texto": f"Equipamiento deportivo escaso: {equip:.1f}/10k hab (ideal: 6)",
            "impacto": "Oferta insuficiente para cubrir la demanda poblacional",
        })
    else:
        fortalezas.append(f"⚽ Equipamiento deportivo aceptable: {equip:.1f}/10k hab")

    # ── Entorno alimentario ───────────────────────────────────
    ultra = col.get("tiendas_ultra", ear)
    if ultra > 0.70:
        alertas.append({
            "emoji": "🍟", "color": HIGH,
            "texto": f"Entorno alimentario muy riesgoso: {ultra*100:.0f}% ultraprocesados",
            "impacto": "Alta exposición a alimentos que elevan glucosa e insulina",
        })
        recomendaciones.append("🥗 Buscar mercados tradicionales o OXXO de cereales/frutas como alternativa")
    elif ultra > 0.45:
        alertas.append({
            "emoji": "🍟", "color": MID,
            "texto": f"Entorno alimentario moderadamente riesgoso: {ultra*100:.0f}%",
            "impacto": "Acceso fácil a ultraprocesados en la colonia",
        })
    else:
        fortalezas.append(f"🍟 Entorno alimentario aceptable: {ultra*100:.0f}% ultraprocesados")

    # ── Marginación ───────────────────────────────────────────
    marg = col.get("marginacion", imp)
    grado = col.get("grado_marginacion", "—")
    if marg > 0.60:
        alertas.append({
            "emoji": "📉", "color": HIGH,
            "texto": f"Marginación {grado}: índice {marg:.2f}",
            "impacto": "La vulnerabilidad socioeconómica amplifica todos los riesgos metabólicos",
        })
        recomendaciones.append("📋 Explorar programas de salud pública municipales disponibles")
    elif marg > 0.30:
        alertas.append({
            "emoji": "📉", "color": MID,
            "texto": f"Marginación {grado}: índice {marg:.2f}",
            "impacto": "Acceso limitado a servicios de salud preventiva",
        })
    else:
        fortalezas.append(f"📉 Marginación {grado}: buen acceso a servicios")

    # ── Densidad ──────────────────────────────────────────────
    dens = col.get("densidad_pob", 5000)
    if dens > 10_000:
        alertas.append({
            "emoji": "🏘️", "color": MID,
            "texto": f"Alta densidad: {dens:,}/km² — comprime espacios verdes y deportivos".replace(",", " "),
            "impacto": "Menor disponibilidad de espacios abiertos per cápita",
        })
    else:
        fortalezas.append(f"🏘️ Densidad manejable: {dens:,}/km²".replace(",", " "))

    # ── Nivel general ─────────────────────────────────────────
    if iarri >= 0.70:
        nivel = "crítico"
        color = HIGH
        titulo = "Entorno de Riesgo Metabólico Crítico"
        subtitulo = "Tu colonia concentra múltiples factores que elevan el riesgo de resistencia a la insulina."
    elif iarri >= 0.50:
        nivel = "alto"
        color = HIGH
        titulo = "Entorno de Riesgo Metabólico Alto"
        subtitulo = "Varios factores del entorno construido dificultan mantener un metabolismo saludable."
    elif iarri >= 0.35:
        nivel = "medio"
        color = MID
        titulo = "Entorno de Riesgo Metabólico Moderado"
        subtitulo = "Algunas variables del entorno representan oportunidades de mejora."
    else:
        nivel = "bajo"
        color = LOW
        titulo = "Entorno Metabólico Favorable"
        subtitulo = "Tu colonia cuenta con condiciones que facilitan un estilo de vida saludable."

    # Recomendación universal
    recomendaciones.append("📊 Usa la Calculadora IARRI para simular el impacto de mejoras en tu entorno")

    return {
        "nivel": nivel,
        "color": color,
        "titulo": titulo,
        "subtitulo": subtitulo,
        "alertas": alertas,
        "fortalezas": fortalezas,
        "recomendaciones": recomendaciones,
        "iarri": iarri,
        "prob_ri": prob_ri(iarri),
    }


# ─── PANTALLA PRINCIPAL ───────────────────────────────────────────────────────

def build_territorial(page: ft.Page, state: dict) -> ft.Column:
    # Estado de navegación interna
    nav = {"colonia": None, "municipio_idx": state.get("muni_idx", 0)}

    contenido = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)

    # ─────────────────────────────────────────────────────────
    # VISTA: SELECTOR DE MUNICIPIO + COLONIA
    # ─────────────────────────────────────────────────────────
    def render_selector(update: bool = True):
        nav["colonia"] = None
        muni_idx = nav["municipio_idx"]

        # Chips municipio
        chips = ft.Row([
            ft.GestureDetector(
                content=ft.Container(
                    content=ft.Text(
                        m["nombre"].replace("San ", "").split()[0],
                        size=11, weight=ft.FontWeight.W_600,
                        color=WHITE if i == muni_idx else MUTED,
                    ),
                    bgcolor=ACCENT if i == muni_idx else CARD,
                    border=ft.border.all(1, ACCENT if i == muni_idx else BORDER),
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=14, vertical=7),
                ),
                on_tap=lambda e, i=i: _cambiar_muni(i),
            )
            for i, m in enumerate(MUNICIPIOS)
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

        muni = MUNICIPIOS[muni_idx]
        datos_muni = DATOS_TERRITORIALES.get(muni["nombre"], {})
        colonias = datos_muni.get("colonias", [])
        iarri_muni = calc_iarri(muni["AV"], muni["IC"], muni["ED"], muni["EAR"], muni["IMP"])
        _, col_muni = nivel_riesgo(iarri_muni)

        # Resumen del municipio
        resumen_muni = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(muni["nombre"], size=16,
                                weight=ft.FontWeight.W_900, color=TEXT),
                        ft.Text(
                            f"👥 {datos_muni.get('poblacion', 0):,} hab".replace(",", " ")
                            + f"  ·  {len(colonias)} colonias",
                            size=11, color=MUTED,
                        ),
                    ], spacing=2, expand=True),
                    ft.Column([
                        ft.Text(f"{iarri_muni:.2f}", size=36,
                                weight=ft.FontWeight.W_900, color=col_muni),
                        ft.Container(
                            content=ft.Text("IARRI municipal", size=9,
                                            color=col_muni, weight=ft.FontWeight.BOLD),
                            bgcolor=col_muni + "18",
                            border_radius=10,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        ),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   vertical_alignment=ft.CrossAxisAlignment.END),
                ft.Container(height=10),
                # Barra de las 5 variables municipales
                ft.Column([
                    _mini_barra("🌳", "Áreas Verdes", muni["AV"], True),
                    _mini_barra("🚶", "Caminabilidad", muni["IC"], True),
                    _mini_barra("⚽", "Equip. Deportivo", muni["ED"], True),
                    _mini_barra("🍟", "Entorno Alim.", muni["EAR"], False),
                    _mini_barra("📉", "Marginación", muni["IMP"], False),
                ], spacing=5),
            ], spacing=0),
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(-1, -1),
                end=ft.alignment.Alignment(1, 1),
                colors=["#e0f2fe", "#ede9fe"],
            ),
            border=ft.border.all(1, BORDER),
            border_radius=18,
            padding=16,
        )

        # Tarjetas de colonias
        col_cards = []
        for col in colonias:
            diag = _diagnostico_colonia(col)
            col_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    "🔴" if diag["nivel"] in ("crítico", "alto")
                                    else "🟡" if diag["nivel"] == "medio"
                                    else "🟢",
                                    size=20,
                                ),
                                width=36, height=36,
                                bgcolor=diag["color"] + "15",
                                border_radius=10,
                                alignment=ft.alignment.Alignment(0, 0),
                            ),
                            ft.Column([
                                ft.Text(col["nombre"], size=13,
                                        weight=ft.FontWeight.BOLD, color=TEXT),
                                ft.Text(
                                    f"👥 {col.get('poblacion', 0):,} hab".replace(",", " "),
                                    size=10, color=MUTED,
                                ),
                            ], spacing=1, expand=True),
                            ft.Column([
                                ft.Text(f"{diag['iarri']:.2f}", size=20,
                                        weight=ft.FontWeight.W_900, color=diag["color"]),
                                ft.Text(f"RI {diag['prob_ri']*100:.0f}%",
                                        size=10, color=MUTED),
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(height=6),
                        # Mini barras de las 3 variables más críticas
                        ft.Row([
                            _chip_var("🌳", col.get("av", 0.5), True),
                            _chip_var("🚶", col.get("ic", 0.5), True),
                            _chip_var("⚽", col.get("ed", 0.5), True),
                            _chip_var("🍟", col.get("ear", 0.5), False),
                            _chip_var("📉", col.get("imp", 0.5), False),
                        ], spacing=4),
                    ], spacing=0),
                    bgcolor=CARD,
                    border=ft.border.all(2 if nav["colonia"] == col["nombre"] else 1,
                                         diag["color"] + "88" if nav["colonia"] == col["nombre"]
                                         else BORDER),
                    border_radius=14,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    ink=True,
                    on_click=lambda e, c=col: render_perfil(c),
                )
            )

        controles = [
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("🏙️", size=26),
                    ft.Column([
                        ft.Text("Análisis Territorial", size=16,
                                weight=ft.FontWeight.BOLD, color=ACCENT),
                        ft.Text("Perfil metabólico ambiental · Datos INEGI / CONAPO / DENUE",
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
                    ft.Text("Selecciona un municipio", size=11,
                            color=MUTED, weight=ft.FontWeight.W_600),
                    ft.Container(height=4),
                    chips,
                    ft.Container(height=10),
                    resumen_muni,
                    ft.Container(height=14),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=8),
                    ft.Text("Selecciona tu colonia", size=13,
                            weight=ft.FontWeight.BOLD, color=TEXT),
                    ft.Text("Toca una colonia para ver su perfil metabólico ambiental",
                            size=11, color=MUTED),
                    ft.Container(height=8),
                    *col_cards,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido.controls = controles
        if update:
            page.update()

    def _cambiar_muni(idx: int):
        nav["municipio_idx"] = idx
        state["muni_idx"] = idx
        render_selector()

    # ─────────────────────────────────────────────────────────
    # VISTA: PERFIL METABÓLICO AMBIENTAL DE LA COLONIA
    # ─────────────────────────────────────────────────────────
    def render_perfil(col: dict, update: bool = True):
        nav["colonia"] = col["nombre"]
        diag = _diagnostico_colonia(col)
        muni_idx = nav["municipio_idx"]
        muni = MUNICIPIOS[muni_idx]

        # ── PORTADA del perfil ────────────────────────────────
        portada = ft.Container(
            content=ft.Column([
                # Encabezado institucional
                ft.Text(
                    "PERFIL METABÓLICO AMBIENTAL",
                    size=9, color=WHITE + "AA",
                    weight=ft.FontWeight.BOLD,
                    font_family="monospace",
                ),
                ft.Container(height=4),
                ft.Text(col["nombre"], size=20,
                        weight=ft.FontWeight.W_900, color=WHITE),
                ft.Text(muni["nombre"] + " · Puebla, México",
                        size=11, color=WHITE + "CC"),
                ft.Container(height=12),
                ft.Row([
                    ft.Column([
                        ft.Text(f"{diag['iarri']:.2f}", size=52,
                                weight=ft.FontWeight.W_900, color=WHITE, height=60),
                        ft.Text("IARRI", size=10, color=WHITE + "AA",
                                weight=ft.FontWeight.BOLD),
                    ], spacing=0),
                    ft.Container(width=1, height=60, bgcolor=WHITE + "33"),
                    ft.Column([
                        ft.Text(f"{diag['prob_ri']*100:.0f}%", size=36,
                                weight=ft.FontWeight.W_900, color=WHITE),
                        ft.Text("Prob. RI", size=10, color=WHITE + "AA",
                                weight=ft.FontWeight.BOLD),
                    ], spacing=0),
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Container(
                            content=ft.Text(
                                diag["nivel"].upper(),
                                size=11, color=WHITE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=WHITE + "22",
                            border=ft.border.all(1, WHITE + "44"),
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            f"👥 {col.get('poblacion', 0):,} hab".replace(",", " "),
                            size=10, color=WHITE + "AA",
                        ),
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Text(diag["titulo"], size=13,
                        weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Text(diag["subtitulo"], size=11, color=WHITE + "CC"),
            ], spacing=2),
            gradient=ft.LinearGradient(
                begin=ft.alignment.Alignment(-1, -1),
                end=ft.alignment.Alignment(1, 1),
                colors=[diag["color"] + "DD", diag["color"] + "99"],
            ),
            border_radius=18,
            padding=18,
            shadow=ft.BoxShadow(blur_radius=16, color=diag["color"] + "55",
                                offset=ft.Offset(0, 4)),
        )

        # ── Las 5 variables en detalle ────────────────────────
        vars_detalle = [
            _var_detalle(
                "🌳", "Acceso a Áreas Verdes",
                col.get("areas_verdes_m2", col.get("av", 0.5) * 9),
                " m²/hab", col.get("av", 0.5), True,
                "OMS: mínimo 9 m²/hab", f"Municipio: {DATOS_TERRITORIALES[muni['nombre']].get('areas_verdes_m2', 0)} m²",
            ),
            _var_detalle(
                "🏘️", "Densidad Poblacional",
                col.get("densidad_pob", 5000),
                " hab/km²", col.get("densidad_pob", 5000) / 12000, False,
                "Umbral de estrés urbano: >10k/km²",
                f"Municipio: {DATOS_TERRITORIALES[muni['nombre']].get('densidad_pob', 0):,}/km²".replace(",", " "),
            ),
            _var_detalle(
                "📉", "Índice de Marginación",
                col.get("marginacion", col.get("imp", 0.5)),
                f" — {col.get('grado_marginacion', '—')}", col.get("marginacion", col.get("imp", 0.5)), False,
                "CONAPO · 0=Sin marginación / 1=Muy alto",
                f"Municipio: {DATOS_TERRITORIALES[muni['nombre']].get('marginacion', 0):.2f}",
            ),
            _var_detalle(
                "⚽", "Equipamiento Deportivo",
                col.get("equipamiento_dep", col.get("ed", 0.5) * 6),
                "/10k hab", col.get("ed", 0.5), True,
                "Ideal: 6 instalaciones/10k hab",
                f"Municipio: {DATOS_TERRITORIALES[muni['nombre']].get('equipamiento_dep', 0)}/10k",
            ),
            _var_detalle(
                "🚶", "Movilidad Peatonal",
                col.get("movilidad_peat", col.get("ic", 0.5) * 0.9) * 100,
                "% banquetas accesibles", col.get("ic", 0.5), True,
                "Meta: >60% de banquetas en buen estado",
                f"Municipio: {DATOS_TERRITORIALES[muni['nombre']].get('movilidad_peat', 0)*100:.0f}%",
            ),
        ]

        # ── Alertas ───────────────────────────────────────────
        alertas_widgets = []
        for a in diag["alertas"]:
            alertas_widgets.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(a["emoji"], size=18),
                        bgcolor=a["color"] + "20",
                        border_radius=8, width=36, height=36,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(a["texto"], size=12, color=TEXT,
                                weight=ft.FontWeight.W_600),
                        ft.Text(a["impacto"], size=10, color=MUTED, italic=True),
                    ], spacing=1, expand=True),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=a["color"] + "08",
                border=ft.border.all(1, a["color"] + "44"),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
            ))

        # ── Fortalezas ────────────────────────────────────────
        fortalezas_widgets = []
        for f in diag["fortalezas"]:
            fortalezas_widgets.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                            size=16, color=LOW),
                    ft.Text(f, size=12, color=TEXT, expand=True),
                ], spacing=8),
                bgcolor=LOW + "08",
                border=ft.border.all(1, LOW + "33"),
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        # ── Recomendaciones ───────────────────────────────────
        rec_widgets = []
        for idx_r, r in enumerate(diag["recomendaciones"]):
            rec_widgets.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(str(idx_r + 1), size=11,
                                        color=WHITE, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT,
                        border_radius=20, width=24, height=24,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Text(r, size=12, color=TEXT, expand=True),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
                bgcolor=ACCENT + "08",
                border=ft.border.all(1, ACCENT + "33"),
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        # ── Comparativa vs municipio ──────────────────────────
        comparativa = _build_comparativa(col, muni)

        # Fuente de datos
        fuente_widget = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=12, color=MUTED),
                ft.Text(
                    "Fuente: INEGI Censo 2020 · CONAPO · DENUE · Datos estimados por colonia",
                    size=9, color=MUTED, italic=True, expand=True,
                ),
            ], spacing=6),
            bgcolor=SURFACE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

        controles = [
            # Header con back
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        ft.Icons.ARROW_BACK_IOS,
                        icon_color=ACCENT,
                        on_click=lambda e: render_selector(),
                        icon_size=20,
                    ),
                    ft.Column([
                        ft.Text("Perfil Metabólico", size=13,
                                weight=ft.FontWeight.BOLD, color=TEXT),
                        ft.Text(col["nombre"], size=10, color=MUTED),
                    ], spacing=1, expand=True),
                    ft.Text("🏙️", size=26),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=SURFACE,
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=8),
                    portada,
                    ft.Container(height=14),
                    titulo_seccion("VARIABLES TERRITORIALES — ANÁLISIS DETALLADO"),
                    ft.Container(height=8),
                    *vars_detalle,
                    ft.Container(height=4),
                    # Alertas
                    *(
                        [
                            titulo_seccion("ALERTAS METABÓLICAS"),
                            ft.Container(height=6),
                            *alertas_widgets,
                            ft.Container(height=8),
                        ]
                        if alertas_widgets else []
                    ),
                    # Fortalezas
                    *(
                        [
                            titulo_seccion("FACTORES PROTECTORES"),
                            ft.Container(height=6),
                            *fortalezas_widgets,
                            ft.Container(height=8),
                        ]
                        if fortalezas_widgets else []
                    ),
                    titulo_seccion("COMPARATIVA: COLONIA VS MUNICIPIO"),
                    ft.Container(height=8),
                    comparativa,
                    ft.Container(height=12),
                    titulo_seccion("RECOMENDACIONES TERRITORIALES"),
                    ft.Container(height=6),
                    *rec_widgets,
                    ft.Container(height=10),
                    fuente_widget,
                    ft.Container(height=32),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=16, vertical=0),
            ),
        ]
        contenido.controls = controles
        if update:
            page.update()

    # ─────────────────────────────────────────────────────────
    # WIDGETS AUXILIARES
    # ─────────────────────────────────────────────────────────

    render_selector(update=False)
    return ft.Column([contenido], expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)


# ─── WIDGETS REUTILIZABLES (módulo-level) ────────────────────────────────────

def _mini_barra(emoji: str, label: str, valor: float, inversa: bool) -> ft.Row:
    """Fila de mini-barra para el resumen del municipio."""
    col = _color_var(valor, inversa)
    return ft.Row([
        ft.Text(emoji, size=12),
        ft.Text(label, size=10, color=MUTED, width=100),
        ft.Container(
            content=ft.Container(
                width=max(2, valor * 160),
                height=5, bgcolor=col, border_radius=2,
            ),
            width=160, height=5,
            bgcolor=BORDER, border_radius=2,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        ft.Text(f"{valor:.2f}", size=10, color=col,
                weight=ft.FontWeight.BOLD, width=30),
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _chip_var(emoji: str, valor: float, inversa: bool) -> ft.Container:
    """Chip compacto de variable para tarjeta de colonia."""
    col = _color_var(valor, inversa)
    return ft.Container(
        content=ft.Text(f"{emoji} {valor:.2f}", size=10,
                        color=col, weight=ft.FontWeight.BOLD),
        bgcolor=col + "15",
        border=ft.border.all(1, col + "44"),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=6, vertical=3),
    )


def _var_detalle(
    emoji: str, titulo: str,
    valor_num: float, unidad: str,
    pct: float, inversa: bool,
    nota_izq: str, nota_der: str,
) -> ft.Container:
    """Tarjeta expandida de variable con barra, valor y notas."""
    col = _color_var(pct, inversa)
    pct_clip = max(0.0, min(1.0, pct))

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Text(emoji, size=20),
                    bgcolor=col + "20", border_radius=10,
                    width=38, height=38,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(titulo, size=11,
                            weight=ft.FontWeight.W_600, color=TEXT),
                    ft.Text(nota_izq, size=10, color=MUTED),
                ], spacing=1, expand=True),
                ft.Text(
                    f"{valor_num:.1f}{unidad}" if isinstance(valor_num, float)
                    else f"{valor_num:,}{unidad}".replace(",", " "),
                    size=16, weight=ft.FontWeight.W_900, color=col,
                ),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=8),
            ft.Container(
                content=ft.Container(
                    bgcolor=col, border_radius=4, height=7,
                    width=max(4, pct_clip * 300),
                ),
                bgcolor=BORDER, border_radius=4, height=7,
                expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Row([
                ft.Text(nota_der, size=9, color=MUTED),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(
                        "✓ OK" if (col == LOW) else ("⚠ Atención" if col == MID else "✗ Crítico"),
                        size=9, color=WHITE, weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=col,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                ),
            ]),
        ], spacing=2),
        bgcolor=CARD,
        border=ft.border.all(1, col + "44"),
        border_radius=14,
        padding=14,
        margin=ft.margin.only(bottom=8),
        shadow=ft.BoxShadow(blur_radius=4, color="#0000000a", offset=ft.Offset(0, 1)),
    )


def _build_comparativa(col: dict, muni: dict) -> ft.Container:
    """Tabla de comparativa colonia vs municipio para las 5 variables."""
    datos_muni = DATOS_TERRITORIALES.get(muni["nombre"], {})

    filas = [
        ("🌳", "Áreas Verdes",
         col.get("av", 0.5), muni["AV"], True),
        ("🚶", "Caminabilidad",
         col.get("ic", 0.5), muni["IC"], True),
        ("⚽", "Equip. Dep.",
         col.get("ed", 0.5), muni["ED"], True),
        ("🍟", "Entorno Alim.",
         col.get("ear", 0.5), muni["EAR"], False),
        ("📉", "Marginación",
         col.get("imp", 0.5), muni["IMP"], False),
    ]

    header = ft.Row([
        ft.Text("Variable", size=10, color=MUTED, weight=ft.FontWeight.BOLD, expand=True),
        ft.Text("Colonia", size=10, color=ACCENT, weight=ft.FontWeight.BOLD, width=60,
                text_align=ft.TextAlign.CENTER),
        ft.Text("Municipio", size=10, color=MUTED, weight=ft.FontWeight.BOLD, width=60,
                text_align=ft.TextAlign.CENTER),
        ft.Text("Δ", size=10, color=MUTED, weight=ft.FontWeight.BOLD, width=40,
                text_align=ft.TextAlign.CENTER),
    ], spacing=4)

    rows = [header, ft.Divider(color=BORDER, height=1)]
    for emoji, label, val_col, val_muni, inversa in filas:
        delta = val_col - val_muni
        col_col = _color_var(val_col, inversa)
        col_mun = _color_var(val_muni, inversa)
        # Para inversas: delta positivo es MEJOR. Para directas: delta positivo es PEOR.
        delta_col = (LOW if delta > 0.02 else HIGH if delta < -0.02 else MID) if inversa \
                    else (HIGH if delta > 0.02 else LOW if delta < -0.02 else MID)
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

        rows.append(ft.Row([
            ft.Text(f"{emoji} {label}", size=11, color=TEXT, expand=True),
            ft.Container(
                content=ft.Text(f"{val_col:.2f}", size=12,
                                weight=ft.FontWeight.BOLD, color=col_col,
                                text_align=ft.TextAlign.CENTER),
                width=60, alignment=ft.alignment.Alignment(0, 0),
            ),
            ft.Container(
                content=ft.Text(f"{val_muni:.2f}", size=11, color=col_mun,
                                text_align=ft.TextAlign.CENTER),
                width=60, alignment=ft.alignment.Alignment(0, 0),
            ),
            ft.Container(
                content=ft.Text(delta_str, size=10, color=delta_col,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                width=40, alignment=ft.alignment.Alignment(0, 0),
            ),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER))

    return ft.Container(
        content=ft.Column(rows, spacing=8),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=14,
        padding=14,
    )
