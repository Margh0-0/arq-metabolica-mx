"""
ui/screens/calculadora_screen.py
Pantalla 3 — CALCULADORA (tabs IARRI + IARM + resultado combinado)

Estructura:
  - Tab 0 — IARRI: calculadora individual (AV, IC, ED, EAR, IMP)
  - Tab 1 — IARM:  índice territorial (ST, BAV, DEN, BEA)
  - Resultado combinado: narrativa cruzada IARRI × IARM al final de la pantalla
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
from core.iarm import calc_iarm, nivel_riesgo_iarm, narrativa_combinada
from core.datos import MUNICIPIOS, VARIABLES, VARIABLES_IARM, RECOMENDACIONES_IARM


# ─── Helper ──────────────────────────────────────────────────────────────────

def _hex_alpha(color: str, alpha_hex: str) -> str:
    base = color.lstrip("#")
    if len(base) == 8:
        return f"#{base[:6]}{alpha_hex}"
    return f"#{base}{alpha_hex}"


# ─── Builder principal ────────────────────────────────────────────────────────

def build_calculadora(page, state):
    # Bloqueo invitado
    if state.get("es_invitado"):
        def _ir_reg():
            state.get("logout", lambda: None)()
        _dialogo_registro(page, _ir_reg)
        return _pantalla_bloqueada(
            "🧮 Calculadora",
            "Calcula el índice de riesgo de tu municipio.",
            lambda: state.get("logout", lambda: None)(),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN A — IARRI (individual)
    # ══════════════════════════════════════════════════════════════════════════

    slider_vals = {v["key"]: state.get(f"slider_{v['key']}", 0.5) for v in VARIABLES}

    result_txt      = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    nivel_txt       = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)
    prob_txt        = ft.Text("Prob. RI: —", size=12, color=MUTED)
    guardar_btn_txt = ft.Text("💾  Guardar Resultado", size=13,
                               weight=ft.FontWeight.BOLD, color=WHITE)
    mc_btn_txt      = ft.Text("⚡  Simulación Monte Carlo (1000 iter.)", size=11,
                               weight=ft.FontWeight.BOLD, color=WHITE,
                               overflow=ft.TextOverflow.ELLIPSIS)

    # Barras de desglose IARRI
    MAX_CONTRIB = 0.25

    desglose_bars = {}
    desglose_rows = []
    for v in VARIABLES:
        bar_inner = ft.ProgressBar(value=0, expand=True, color=v["color"], bgcolor=BORDER)
        bar_track = ft.Container(
            content=bar_inner, height=8,
            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=42,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace",
                           weight=ft.FontWeight.BOLD)
        pct_lbl = ft.Text("0.0%", size=9, color=MUTED, width=28,
                           text_align=ft.TextAlign.RIGHT)
        desglose_bars[v["key"]] = (bar_inner, val_lbl, pct_lbl)
        desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=36,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_track,
                val_lbl,
                pct_lbl,
            ], spacing=6)
        )

    # Referencia al resultado combinado (se actualiza al cambiar cualquier tab)
    combinado_ref = {"widget": None}

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
        total_contrib = max(sum(contribs.values()), 0.001)
        for k, (bar, lbl, pct) in desglose_bars.items():
            c = contribs[k]
            bar.value = min(1.0, c / MAX_CONTRIB)
            lbl.value = f"{c:.3f}"
            pct.value = f"{c / total_contrib * 100:.1f}%"
        _actualizar_combinado()
        page.update()

    # Sliders IARRI
    slider_val_lbls = {}
    slider_widgets  = []

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

    origen_txt  = ft.Text("", size=11, color=MUTED, italic=True)
    encuesta_w  = build_encuesta(page, lambda r: None)
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

    presets_row = ft.Row(preset_buttons, spacing=8, scroll=ft.ScrollMode.AUTO)

    toggle_btn_txt = ft.Text("Llenar desde encuesta", size=13,
                              weight=ft.FontWeight.BOLD, color=WHITE)

    def togg_encuesta(e):
        encuesta_card.visible = not encuesta_card.visible
        toggle_btn_txt.value = (
            "Ocultar encuesta" if encuesta_card.visible else "Llenar desde encuesta"
        )
        page.update()

    # Tarjetas slider IARRI
    slider_cards = []
    for v, (key, val_lbl, s) in zip(VARIABLES, slider_widgets):
        card = tarjeta(ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text(v["icon"], size=15),
                        bgcolor=v["color"] + "22", border_radius=8,
                        width=30, height=30, alignment=ft.alignment.Alignment(0, 0),
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
        ], spacing=2), padding=14)
        slider_cards.append(card)

    def guardar_resultado(e):
        guardar_btn_txt.value = "⏳  Guardando..."
        page.update()

        def _task():
            try:
                iarri = calc_iarri(**slider_vals)
                nivel, col = nivel_riesgo(iarri)
                pr = prob_ri(iarri)

                muni_idx = state.get("muni_idx", 0)
                if "resultados_municipios" not in state:
                    state["resultados_municipios"] = {}
                state["resultados_municipios"][muni_idx] = {
                    "municipio_id": muni_idx + 1,
                    "AV":   slider_vals["AV"],
                    "IC":   slider_vals["IC"],
                    "ED":   slider_vals["ED"],
                    "EAR":  slider_vals["EAR"],
                    "IMP":  slider_vals["IMP"],
                    "iarri": iarri,
                    "nivel": nivel,
                    "prob":  pr,
                }
                state["iarri_guardado"] = True

                # Incluir IARM en el guardado si ya fue calculado
                iarm_vals = {v["key"]: state.get(f"iarm_{v['key']}", 0.5)
                             for v in VARIABLES_IARM}
                iarm = calc_iarm(**iarm_vals)
                niv_iarm, col_iarm_dlg = nivel_riesgo_iarm(iarm)
                state["iarm_guardado"] = True
                state["iarm_ultimo"] = {
                    **iarm_vals,
                    "iarm":  iarm,
                    "nivel": niv_iarm,
                }

                def cerrar_dialogo(e=None):
                    dlg.open = False
                    page.update()
                    state.get("_switch_tab", lambda x: None)(3)

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("✅ Resultado Guardado", weight=ft.FontWeight.BOLD, color=LOW),
                    content=ft.Column([
                        ft.Text("Tu cálculo se ha guardado correctamente.", size=13),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("IARRI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{iarri:.4f}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Nivel IARRI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"● {nivel}", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Prob. RI:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{pr*100:.1f}%", color=col, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Divider(height=1, color=BORDER),
                                ft.Row([
                                    ft.Text("IARM:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{iarm:.4f}", color=col_iarm_dlg, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                                ft.Row([
                                    ft.Text("Nivel IARM:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"● {niv_iarm}", color=col_iarm_dlg, weight=ft.FontWeight.BOLD),
                                ], spacing=10),
                            ], spacing=6),
                            bgcolor=CARD,
                            border=ft.border.all(1, col + "44"),
                            border_radius=12,
                            padding=12,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Se procederá a Intervención para ver recomendaciones.",
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
                        ft.TextButton("OK", on_click=lambda e: (
                            setattr(dlg_err, "open", False), page.update()
                        )),
                    ],
                )
                page.overlay.append(dlg_err)
                dlg_err.open = True
                page.update()
            finally:
                guardar_btn_txt.value = "💾  Guardar Resultado"
                page.update()

        threading.Thread(target=_task, daemon=True).start()

    # Resultado card IARRI
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
                    height=46, expand=True,
                    on_click=lambda e: run_mc(e),
                ),
                ft.ElevatedButton(
                    content=guardar_btn_txt,
                    bgcolor=ACCENT3,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46, expand=True,
                    on_click=guardar_resultado,
                ),
            ], spacing=8),
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
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
            ft.Row([
                ft.Text("0.0", size=9, color=MUTED), ft.Container(expand=True),
                ft.Text("0.5", size=9, color=MUTED), ft.Container(expand=True),
                ft.Text("1.0", size=9, color=MUTED),
            ]),
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

    # ── Tab IARRI completo ────────────────────────────────────────────────────
    tab_iarri_content = ft.Column([
        ft.Container(height=6),
        presets_row,
        ft.Container(height=8),
        tarjeta(ft.Text(
            "Modifique las barras deslizantes para ajustar su índice y obtener la mayor precisión posible.",
            size=12, color=ACCENT, font_family="monospace",
        )),
        ft.Container(height=10),
        *slider_cards,
        ft.Container(height=10),
        resultado_card,
        ft.Container(height=10),
        mc_card,
        ft.Container(height=8),
    ], spacing=8)

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN B — IARM (territorial)
    # ══════════════════════════════════════════════════════════════════════════

    iarm_vals = {v["key"]: state.get(f"iarm_{v['key']}", 0.5) for v in VARIABLES_IARM}

    iarm_result_txt = ft.Text("—", size=52, weight=ft.FontWeight.W_900, color=ACCENT)
    iarm_nivel_txt  = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=MUTED)

    # Barras de desglose IARM
    iarm_desglose_bars = {}
    iarm_desglose_rows = []
    for v in VARIABLES_IARM:
        bar_inner = ft.ProgressBar(value=0, expand=True, color=v["color"], bgcolor=BORDER)
        bar_track = ft.Container(
            content=bar_inner, height=8,
            expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        val_lbl = ft.Text("0.000", size=10, color=v["color"], width=42,
                           text_align=ft.TextAlign.RIGHT, font_family="monospace",
                           weight=ft.FontWeight.BOLD)
        pct_lbl = ft.Text("0.0%", size=9, color=MUTED, width=28,
                           text_align=ft.TextAlign.RIGHT)
        iarm_desglose_bars[v["key"]] = (bar_inner, val_lbl, pct_lbl)
        iarm_desglose_rows.append(
            ft.Row([
                ft.Text(v["key"], size=11, color=MUTED, width=36,
                        weight=ft.FontWeight.BOLD, font_family="monospace"),
                bar_track,
                val_lbl,
                pct_lbl,
            ], spacing=6)
        )

    # Panel de recomendaciones IARM (reactivo al nivel)
    iarm_rec_panel = ft.Container(visible=False)

    def _build_rec_panel(nivel_label: str) -> ft.Container:
        rec = RECOMENDACIONES_IARM.get(nivel_label)
        if not rec:
            return ft.Container(visible=False)
        col = rec["color"]
        items = [
            ft.Row([
                ft.Text("•", size=13, color=col),
                ft.Text(item, size=12, color=TEXT, expand=True),
            ], spacing=6)
            for item in rec["items"]
        ]
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(rec["icono"], size=20),
                    ft.Text(rec["titulo"], size=13, weight=ft.FontWeight.BOLD, color=col),
                ], spacing=8),
                ft.Container(height=4),
                *items,
            ], spacing=6),
            bgcolor=_hex_alpha(col, "11"),
            border=ft.border.all(1, _hex_alpha(col, "44")),
            border_radius=14,
            padding=14,
            visible=True,
        )

    def actualizar_iarm():
        iarm = calc_iarm(**iarm_vals)
        niv, col = nivel_riesgo_iarm(iarm)
        iarm_result_txt.value = f"{iarm:.4f}"
        iarm_result_txt.color = col
        iarm_nivel_txt.value  = f"● {niv}"
        iarm_nivel_txt.color  = col
        # Barras de desglose
        total = max(sum(iarm_vals.values()), 0.001)
        for k, (bar, lbl, pct) in iarm_desglose_bars.items():
            c = iarm_vals[k] * 0.25   # peso igual para todos
            bar.value = min(1.0, c / 0.25)
            lbl.value = f"{c:.3f}"
            pct.value = f"{iarm_vals[k] / total * 100:.1f}%"
        # Panel de recomendaciones
        nuevo_panel = _build_rec_panel(niv)
        iarm_rec_panel.content = nuevo_panel.content
        iarm_rec_panel.bgcolor = nuevo_panel.bgcolor
        iarm_rec_panel.border  = nuevo_panel.border
        iarm_rec_panel.border_radius = nuevo_panel.border_radius
        iarm_rec_panel.padding = nuevo_panel.padding
        iarm_rec_panel.visible = True
        # Guardar en state para el combinado
        state[f"iarm_calculado"] = iarm
        state[f"iarm_nivel"]     = niv
        _actualizar_combinado()
        page.update()

    # Sliders IARM
    iarm_slider_lbls    = {}
    iarm_slider_widgets = []

    for v in VARIABLES_IARM:
        lbl = ft.Text(f"{iarm_vals[v['key']]:.2f}", size=15,
                      weight=ft.FontWeight.W_900, color=v["color"], width=44)
        s = ft.Slider(
            min=0, max=1, divisions=100,
            value=iarm_vals[v["key"]],
            active_color=v["color"],
            inactive_color=BORDER,
            thumb_color=v["color"],
            on_change=None,
            expand=True,
        )
        iarm_slider_widgets.append((v["key"], lbl, s))
        iarm_slider_lbls[v["key"]] = lbl

    for key, lbl, s in iarm_slider_widgets:
        def make_iarm_change(k):
            def on_change(e):
                iarm_vals[k] = e.control.value
                state[f"iarm_{k}"] = e.control.value
                iarm_slider_lbls[k].value = f"{e.control.value:.2f}"
                actualizar_iarm()
            return on_change
        s.on_change = make_iarm_change(key)

    # Tarjetas slider IARM
    iarm_slider_cards = []
    for v, (key, val_lbl, s) in zip(VARIABLES_IARM, iarm_slider_widgets):
        etiqueta_min = "Sin riesgo"
        etiqueta_max = "Máx. riesgo"
        card = tarjeta(ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text(v["icon"], size=15),
                        bgcolor=v["color"] + "22", border_radius=8,
                        width=30, height=30, alignment=ft.alignment.Alignment(0, 0),
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
                ft.Text(etiqueta_min, size=9, color=MUTED),
                ft.Container(expand=True),
                ft.Text("0.5", size=9, color=MUTED),
                ft.Container(expand=True),
                ft.Text(etiqueta_max, size=9, color=v["color"]),
            ]),
        ], spacing=2), padding=14)
        iarm_slider_cards.append(card)

    # Resultado card IARM
    iarm_resultado_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("IARM Calculado", size=11, color=MUTED),
                    iarm_result_txt,
                ]),
                ft.Column([
                    ft.Text("Clasificación", size=11, color=MUTED),
                    iarm_nivel_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.END),
            ft.Divider(height=1, color=BORDER),
            ft.Text("Desglose de Factores", size=11, color=MUTED),
            *iarm_desglose_rows,
        ], spacing=10),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=["#fef3c7", "#fce7f3"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    # ── Tab IARM completo ─────────────────────────────────────────────────────
    tab_iarm_content = ft.Column([
        ft.Container(height=6),
        tarjeta(ft.Column([
            ft.Text(
                "IARM = (ST + BAV + DEN + BEA) / 4",
                size=13, color=ACCENT, font_family="monospace",
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                "Todos los factores son de riesgo directo: 0 = entorno protector · 1 = máximo riesgo ambiental.",
                size=11, color=MUTED,
            ),
        ], spacing=4)),
        ft.Container(height=10),
        *iarm_slider_cards,
        ft.Container(height=10),
        iarm_resultado_card,
        ft.Container(height=10),
        iarm_rec_panel,
        ft.Container(height=8),
    ], spacing=8)

    # ══════════════════════════════════════════════════════════════════════════
    # SECCIÓN C — Resultado combinado (IARRI × IARM)
    # ══════════════════════════════════════════════════════════════════════════

    combinado_container = ft.Container(
        content=ft.Column([
            ft.Text("Calculá ambos índices para ver el análisis combinado.",
                    size=12, color=MUTED, italic=True,
                    text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=18,
        padding=18,
    )

    def _actualizar_combinado():
        """Recalcula y actualiza la card combinada IARRI × IARM."""
        iarri_val = calc_iarri(**slider_vals)
        iarm_val  = state.get("iarm_calculado", calc_iarm(**iarm_vals))

        niv_iarri, col_iarri = nivel_riesgo(iarri_val)
        niv_iarm,  col_iarm  = nivel_riesgo_iarm(iarm_val)
        narr = narrativa_combinada(niv_iarri, niv_iarm)

        combinado_container.content = ft.Column([
            # Encabezado
            ft.Row([
                ft.Text(narr["icono"], size=24),
                ft.Text(narr["titulo"], size=13, weight=ft.FontWeight.BOLD,
                        color=narr["color"], expand=True),
            ], spacing=10),
            ft.Container(height=4),
            # Scores en paralelo
            ft.Row([
                ft.Column([
                    ft.Text("IARRI", size=10, color=MUTED,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{iarri_val:.3f}", size=26,
                            weight=ft.FontWeight.W_900, color=col_iarri,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        content=ft.Text(f"● {niv_iarri}", size=10,
                                        color=col_iarri, weight=ft.FontWeight.BOLD),
                        bgcolor=_hex_alpha(col_iarri, "18"),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Container(
                    content=ft.Text("✕", size=18, color=MUTED),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text("IARM", size=10, color=MUTED,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{iarm_val:.3f}", size=26,
                            weight=ft.FontWeight.W_900, color=col_iarm,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        content=ft.Text(f"● {niv_iarm}", size=10,
                                        color=col_iarm, weight=ft.FontWeight.BOLD),
                        bgcolor=_hex_alpha(col_iarm, "18"),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ft.Container(height=8),
            ft.Divider(height=1, color=BORDER),
            ft.Container(height=6),
            # Mensaje narrativo
            ft.Container(
                content=ft.Text(narr["mensaje"], size=12, color=TEXT),
                bgcolor=_hex_alpha(narr["color"], "0d"),
                border=ft.border.all(1, _hex_alpha(narr["color"], "33")),
                border_radius=10,
                padding=12,
            ),
            ft.Container(height=6),
            # Acción recomendada
            ft.Container(
                content=ft.Row([
                    ft.Text("💡", size=14),
                    ft.Text(narr["accion"], size=12, color=TEXT, expand=True),
                ], spacing=8),
                bgcolor=_hex_alpha(ACCENT, "0d"),
                border=ft.border.all(1, _hex_alpha(ACCENT, "33")),
                border_radius=10,
                padding=12,
            ),
        ], spacing=6)

        combinado_container.border = ft.border.all(2, _hex_alpha(narr["color"], "66"))

    # ══════════════════════════════════════════════════════════════════════════
    # TABS — sistema de navegación IARRI | IARM
    # ══════════════════════════════════════════════════════════════════════════

    active_tab = {"idx": 0}

    tab_iarri_btn = ft.Container(visible=True)
    tab_iarm_btn  = ft.Container(visible=True)

    content_switcher = ft.Container(content=tab_iarri_content, expand=True)

    def _make_tab_btn(label: str, idx: int, active: bool) -> ft.GestureDetector:
        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(
                    label, size=13, weight=ft.FontWeight.BOLD,
                    color=WHITE if active else MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if active else CARD,
                border=ft.border.all(1, ACCENT if active else BORDER),
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                expand=True,
                alignment=ft.alignment.Alignment(0, 0),
            ),
            on_tap=lambda e, i=idx: switch_calc_tab(i),
            expand=True,
        )

    tabs_row = ft.Row([], spacing=8)

    def _rebuild_tabs(active_idx: int):
        tabs_row.controls = [
            _make_tab_btn("🧮 IARRI — Individual", 0, active_idx == 0),
            _make_tab_btn("🏙️ IARM — Territorial",  1, active_idx == 1),
        ]

    def switch_calc_tab(idx: int):
        active_tab["idx"] = idx
        _rebuild_tabs(idx)
        if idx == 0:
            content_switcher.content = tab_iarri_content
        else:
            content_switcher.content = tab_iarm_content
        page.update()

    _rebuild_tabs(0)

    # Calcular el estado inicial del combinado
    actualizar_resultado()
    actualizar_iarm()

    # ── Layout final ──────────────────────────────────────────────────────────
    return ft.Column([
        titulo_seccion("Calculadora — IARRI & IARM"),
        ft.Container(height=8),
        tabs_row,
        ft.Container(height=4),
        content_switcher,
        ft.Container(height=4),
        titulo_seccion("Análisis Combinado IARRI × IARM"),
        ft.Container(height=8),
        combinado_container,
        ft.Container(height=24),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)
