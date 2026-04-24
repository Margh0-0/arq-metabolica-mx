"""
ui/screens/calculadora_screen.py
Pantalla 3 — CALCULADORA IARRI (sliders, encuesta, Monte Carlo, guardar)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23
"""

import threading
import numpy as np
import flet as ft

from ui.theme import (
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import build_encuesta, titulo_seccion
from ui.screens.inicio_screen import _dialogo_registro, _pantalla_bloqueada
from core.iarri import calc_iarri, nivel_riesgo, prob_ri, monte_carlo, WEIGHTS
from core.datos import MUNICIPIOS, VARIABLES


def build_calculadora(page, state):
    # Bloqueo invitado
    if state.get("es_invitado"):
        def _ir_reg():
            state.get("logout", lambda: None)()
        _dialogo_registro(page, _ir_reg)
        return _pantalla_bloqueada(
            "🧮 Calculadora IARRI",
            "Calcula el índice de riesgo de tu municipio.",
            lambda: state.get("logout", lambda: None)(),
        )

    slider_vals = {v["key"]: state.get(f"slider_{v['key']}", 0.5) for v in VARIABLES}

    result_txt   = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    nivel_txt    = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)
    prob_txt     = ft.Text("Prob. RI: —", size=12, color=MUTED)
    guardar_btn_txt = ft.Text("💾  Guardar Resultado", size=13,
                               weight=ft.FontWeight.BOLD, color=WHITE)
    #mc_resultado = ft.Column([], visible=False)
    mc_btn_txt   = ft.Text("⚡  Simulación Monte Carlo (1000 iter.)", size=13,
                            weight=ft.FontWeight.BOLD, color=WHITE)
    
    #Barras de desglose — reactivas a cada cambio de slider
    MAX_CONTRIB = 0.25   # peso máximo posible por variable (IC y EAR)
    BAR_MAX_PX  = 200    # píxeles que representa MAX_CONTRIB

    # Barras de desglose
    desglose_bars = {}
    desglose_rows = []
    for v in VARIABLES:
        bar_inner = ft.Container(bgcolor=v["color"], border_radius=3,height=8, width=4)
        bar_track = ft.Container(
            content=bar_inner,bgcolor=BORDER, border_radius=3, height=8,
            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=42,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace",weight=ft.FontWeight.BOLD)
        pct_lbl = ft.Text("0.0%", size=9, color=MUTED, width=28,
                           text_align=ft.TextAlign.RIGHT)
        desglose_bars[v["key"]] = (bar_inner, val_lbl,pct_lbl)
        desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=36,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_track,
                val_lbl,
                pct_lbl,

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
        # Desglose
        contribs = {
            "AV":  WEIGHTS["AV"]  * (1 - slider_vals["AV"]),
            "IC":  WEIGHTS["IC"]  * (1 - slider_vals["IC"]),
            "ED":  WEIGHTS["ED"]  * (1 - slider_vals["ED"]),
            "EAR": WEIGHTS["EAR"] * slider_vals["EAR"],
            "IMP": WEIGHTS["IMP"]  * slider_vals["IMP"], #impportante
        }
        total_contrib = max(sum(contribs.values()),0.001) #cambio en las barras con lo del
        for k, (bar, lbl, pct) in desglose_bars.items():
            c = contribs[k] 
            bar.width = max(4, (c / MAX_CONTRIB) * BAR_MAX_PX)
            lbl.value = f"{c:.3f}"
            pct.value = f"{c /total_contrib*100:.1f}%"
        page.update()

    # Sliders
    slider_val_lbls = {}
    slider_widgets = []

    for v in VARIABLES:
        slider_val_lbl = ft.Text(f"{slider_vals[v['key']]:.2f}", size=15,
                                  weight=ft.FontWeight.W_900, color=v["color"], width=44)
        s = ft.Slider(
            min=0, max=1, divisions=100,
            value=slider_vals[v["key"]],
            active_color=v["color"],
            inactive_color=BORDER,
            thumb_color=v["color"],
            on_change=None,
            expand=True,
        )
        slider_widgets.append((v["key"], slider_val_lbl, s))
        slider_val_lbls[v["key"]] = slider_val_lbl

    for key, lbl, s in slider_widgets:
        def make_change(k):
            def on_change(e):
                slider_vals[k] = e.control.value
                state[f"slider_{k}"] = e.control.value
                slider_val_lbls[k].value = f"{e.control.value:.2f}"
                actualizar_resultado()
            return on_change
        s.on_change = make_change(key)

    origen_txt = ft.Text("", size=11, color=MUTED, italic=True)

    encuesta_w = build_encuesta(page, lambda r: None)
    encuesta_card = ft.Container(content=encuesta_w, visible=False)

    def aplicar_valorslider(nuevos_valores: dict, origen: str = ""):
        for k, valor in nuevos_valores.items():
            slider_vals[k] = valor
            state[f"slider_{k}"] = valor
            slider_val_lbls[k].value = f"{valor:.2f}"
            for key2, lbl2, s2 in slider_widgets:
                if key2 == k:
                    s2.value = valor
                    lbl2.value = f"{valor:.2f}"
        if origen:
            origen_txt.value = f"Valores cargados desde {origen}"
            origen_txt.color = ACCENT
        actualizar_resultado()

    def encuesta_completa(respuestas: dict):
        encuesta_card.visible = False
        aplicar_valorslider(respuestas, "Encuesta")
            
    def set_preset(idx):
        m = MUNICIPIOS[idx]
        for v in VARIABLES:
            slider_vals[v["key"]] = m[v["key"]]
            state[f"slider_{v['key']}"] = m[v["key"]]
        for k, lbl, s in slider_widgets:
            lbl.value = f"{slider_vals[k]:.2f}"
            s.value   = slider_vals[k]
        actualizar_resultado()

    # Crear botones presets
    preset_names = ["San Andrés", "San Pablo Xochimehuacan", "Cuautlancingo"]
    preset_buttons = []
    for i, m in enumerate(MUNICIPIOS):
        def make_on_click(idx):
            return lambda e: set_preset(idx)
        preset_buttons.append(
            ft.FilledTonalButton(
                preset_names[i] if i < len(preset_names) else m["nombre"].split()[0],
                on_click=make_on_click(i),
                style=ft.ButtonStyle(bgcolor=CARD, color=TEXT),
            )
        )
    preset_buttons.append(
        ft.FilledTonalButton(
            "",
            on_click=lambda e: None,
            style=ft.ButtonStyle(bgcolor=CARD, color=TEXT),
        )
    )

    presets_row = ft.Row(preset_buttons, spacing=8, scroll=ft.ScrollMode.AUTO)
    
    toggle_btn_txt = ft.Text("Llenar desde encuesta", size=13, weight=ft.FontWeight.BOLD, color=WHITE)

    def togg_encuesta(e):
        encuesta_card.visible = not encuesta_card.visible
        toggle_btn_txt.value = (
            "Ocultar encuesta" if encuesta_card.visible
            else "Llenar desde encuesta"
        )
        page.update()
    # Tarjetas slider
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
            #ft.Text("protector ↓" if v["inv"] else "riesgo ↑",
                    #size=9, color=v["color"], italic=True),
        ], spacing=2), padding=14)
        slider_cards.append(card)

    def guardar_resultado(e):
        """Guarda el resultado en el state y cambia a pestaña de intervención."""
        guardar_btn_txt.value = "⏳  Guardando..."
        page.update()

        def _task():
            try:
                iarri = calc_iarri(**slider_vals)
                nivel, col = nivel_riesgo(iarri)
                pr = prob_ri(iarri)

                muni_idx = state.get("muni_idx", 0)
                # Guardar resultado del municipio actual en el estado compartido
                if "resultados_municipios" not in state:
                    state["resultados_municipios"] = {}
                state["resultados_municipios"][muni_idx] = {
                    "municipio_id": muni_idx + 1,
                    "AV":  slider_vals["AV"],
                    "IC":  slider_vals["IC"],
                    "ED":  slider_vals["ED"],
                    "EAR": slider_vals["EAR"],
                    "IMP": slider_vals["IMP"],
                    "iarri": iarri,
                    "nivel": nivel,
                    "prob":  pr,
                }
                # Flag para badge "Analista Territorial"
                state["iarri_guardado"] = True

                def cerrar_dialogo(e=None):
                    dlg.open = False
                    page.update()
                    # Cambiar a pestaña de Intervención (índice 3)
                    state.get("_switch_tab", lambda x: None)(3)

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("✅ Resultado Guardado", weight=ft.FontWeight.BOLD, color=LOW),
                    content=ft.Column([
                        ft.Text(
                            "Tu cálculo de IARRI se ha guardado correctamente.",
                            size=13,
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("Valor IARRI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{iarri:.4f}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Nivel de Riesgo:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"● {nivel}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Probabilidad RI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{pr*100:.1f}%", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                            ], spacing=6),
                            bgcolor=CARD,
                            border=ft.border.all(1, col + "44"),
                            border_radius=12,
                            padding=12,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Se procederá a la pestaña de Intervención para ver recomendaciones y su intervencion.",
                            size=12, color=MUTED, italic=True,
                        ),
                    ], spacing=8),
                    actions=[
                        ft.ElevatedButton(
                            "Ir a Intervención",
                            on_click=cerrar_dialogo,
                            style=ft.ButtonStyle(
                                bgcolor=ACCENT, color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.overlay.append(dlg)
                dlg.open = True
                page.update()

            except Exception as ex:
                print(f"[ERROR] guardar_resultado: {ex}")
                dlg_err = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("❌ Error", weight=ft.FontWeight.BOLD, color=HIGH),
                    content=ft.Text(f"Hubo un error al guardar: {str(ex)}", size=13),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: (setattr(dlg_err, 'open', False), page.update())),
                    ],
                )
                page.overlay.append(dlg_err)
                dlg_err.open = True
                page.update()
            finally:
                guardar_btn_txt.value = "💾  Guardar Resultado"
                page.update()

        threading.Thread(target=_task, daemon=True).start()

    # Resultado card
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
            ft.Row([
                ft.ElevatedButton(
                    content=mc_btn_txt,
                    bgcolor=ACCENT,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46,
                    expand=True,
                    on_click=lambda e: run_mc(e),
                ),
                ft.ElevatedButton(
                    content=guardar_btn_txt,
                    bgcolor=ACCENT3,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46,
                    expand=True,
                    on_click=guardar_resultado,
                ),
            ], spacing=8),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1,-1),
            end=ft.alignment.Alignment(1,1),
            colors=["#e0f2fe", "#ede9fe"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    # Monte Carlo
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
            # histograma 20 bins
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

    return ft.Column([
        titulo_seccion("Calculadora sobre Municipio"),
        ft.Container(height=6),
        presets_row,
        ft.Container(height=8),
        tarjeta(ft.Text(
            "Instrucciones: Modifique las barras deslizantes para ajustar su indice y obtener la precision posible.",
            size=12, color=ACCENT, font_family="monospace",
        )),
        ft.Container(height=10),
        titulo_seccion("Indice Arquitectonico de Riesgo"),
        ft.Container(height=10),
        *slider_cards,
        ft.Container(height=10),
        resultado_card,
        ft.Container(height=10),
        mc_card,
        ft.Container(height=20),
    ], spacing=8, scroll=ft.ScrollMode.AUTO)
