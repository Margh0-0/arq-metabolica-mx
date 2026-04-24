"""
ui/screens/mapa_screen.py
Pantalla 2 — MAPA (análisis territorial INEGI + mapa interactivo)
Extraído de main.py en F5 del refactor arquitectural — 2026-04-23

CRÍTICO: preserva el try/except ImportError para flet_map.
"""

import flet as ft

from ui.theme import (
    COLORES, PALETAS, get_paleta,
    BG, SURFACE, CARD, BORDER, ACCENT, ACCENT2, ACCENT3,
    LOW, MID, HIGH, TEXT, MUTED, WHITE,
)
from ui.components.tarjeta import tarjeta
from ui.components.encuesta_widget import titulo_seccion
from core.iarri import calc_iarri, nivel_riesgo, prob_ri
from core.datos import MUNICIPIOS, DATOS_TERRITORIALES, _csv_datos


def build_mapa(page, state):
    """
    Mapa interactivo con flet_map (OpenStreetMap).
    - Desktop/Web: muestra mapa embebido + botón para abrir HTML en navegador
    - Android/iOS: mapa embebido con marcadores y zonas de riesgo
    Tiles: OpenStreetMap (gratis, sin API key).
    """
    import json as _json
    import os as _os2

    muni_idx  = state.get("muni_idx", 0)
    muni_data = MUNICIPIOS[muni_idx]
    muni_nom  = muni_data["nombre"]

    if _csv_datos and muni_nom in _csv_datos:
        _base = DATOS_TERRITORIALES.get(muni_nom, {})
        _csv  = _csv_datos[muni_nom]
        datos_ter = {**_base, **_csv,
                     "densidad_max": _base.get("densidad_max", 12000),
                     "oms_standard": 9.0,
                     "equip_ideal":  _base.get("equip_ideal", 6.0),
                     "colonias":     _base.get("colonias", [])}
    else:
        datos_ter = DATOS_TERRITORIALES.get(muni_nom, {})

    iarri_val = calc_iarri(muni_data["AV"], muni_data["IC"],
                           muni_data["ED"], muni_data["EAR"], muni_data["IMP"])
    nivel_txt, col_niv = nivel_riesgo(iarri_val)

    # ── Selector de municipio ─────────────────────────────────
    def cambiar_muni(idx):
        state["muni_idx"] = idx
        state["refresh"]()

    chips = ft.Row([
        ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(
                    m["nombre"].split()[0] + (" " + m["nombre"].split()[1]
                     if len(m["nombre"].split()) > 1 else ""),
                    size=11, weight=ft.FontWeight.W_600,
                    color=WHITE if i == muni_idx else MUTED,
                ),
                bgcolor=ACCENT if i == muni_idx else CARD,
                border=ft.border.all(1, ACCENT if i == muni_idx else BORDER),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=14, vertical=7),
            ),
            on_tap=lambda e, i=i: cambiar_muni(i),
        )
        for i, m in enumerate(MUNICIPIOS)
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

    # ── Header ────────────────────────────────────────────────
    pop_fmt = f"{datos_ter.get('poblacion', 0):,}".replace(",", " ")
    perfil_header = ft.Container(
        content=ft.Column([
            ft.Text("PERFIL METABÓLICO AMBIENTAL", size=10,
                    color=MUTED, weight=ft.FontWeight.BOLD, font_family="monospace"),
            chips,
            ft.Container(height=4),
            ft.Row([
                ft.Column([
                    ft.Text(muni_nom, size=18, weight=ft.FontWeight.W_900, color=TEXT),
                    ft.Text(f"👥 {pop_fmt} hab · Puebla, México", size=11, color=MUTED),
                ], spacing=2, expand=True),
                ft.Column([
                    ft.Text(f"{iarri_val:.2f}", size=42,
                            weight=ft.FontWeight.W_900, color=col_niv, height=52),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=6, height=6, border_radius=3, bgcolor=col_niv),
                            ft.Text(f"Riesgo {nivel_txt}", size=10,
                                    color=col_niv, weight=ft.FontWeight.BOLD),
                        ], spacing=4, tight=True),
                        bgcolor=col_niv + "18",
                        border=ft.border.all(1, col_niv + "55"),
                        border_radius=16,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    ),
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=8),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
            colors=["#e0f2fe", "#ede9fe"],
        ),
        border=ft.border.all(1, BORDER),
        border_radius=20,
        padding=18,
        margin=ft.margin.only(bottom=4),
    )

    # ── Coordenadas y POIs ────────────────────────────────────
    _coords = {
        "San Andrés Cholula":      (19.0514, -98.3020),
        "San Pablo Xochimehuacan": (19.0310, -98.2360),
        "Cuautlancingo":           (19.0897, -98.2730),
    }
    _pois = {
        "San Andrés Cholula": [
            {"lat":19.0540,"lon":-98.3060,"tipo":"verde",   "titulo":"Parque Paseo Cholula",    "desc":"Área verde · AV +0.12"},
            {"lat":19.0490,"lon":-98.2980,"tipo":"verde",   "titulo":"Jardines de Zavaleta",     "desc":"Corredor verde · AV +0.08"},
            {"lat":19.0514,"lon":-98.3020,"tipo":"deporte", "titulo":"Unidad Deportiva SAC",    "desc":"Canchas y gimnasio · ED +0.10"},
            {"lat":19.0475,"lon":-98.3040,"tipo":"peatonal","titulo":"Zona Peatonal Centro",    "desc":"Caminabilidad alta · IC +0.15"},
            {"lat":19.0530,"lon":-98.2990,"tipo":"ultra",   "titulo":"Zona Comercial Galerías", "desc":"Ultraprocesados densos"},
        ],
        "San Pablo Xochimehuacan": [
            {"lat":19.0320,"lon":-98.2350,"tipo":"ultra",   "titulo":"Corredor Comercial",      "desc":"Tiendas · EAR +0.18"},
            {"lat":19.0290,"lon":-98.2380,"tipo":"verde",   "titulo":"Área verde escasa",       "desc":"Solo 2.8 m²/hab"},
            {"lat":19.0310,"lon":-98.2340,"tipo":"deporte", "titulo":"Campo Municipal",         "desc":"ED básico"},
        ],
        "Cuautlancingo": [
            {"lat":19.0920,"lon":-98.2750,"tipo":"ultra",   "titulo":"Corredor OXXO/7Eleven",   "desc":"EAR +0.22"},
            {"lat":19.0880,"lon":-98.2710,"tipo":"ultra",   "titulo":"Zona Industrial",         "desc":"Ultraprocesados"},
            {"lat":19.0897,"lon":-98.2730,"tipo":"deporte", "titulo":"Campo Municipal",         "desc":"ED 0.08"},
            {"lat":19.0870,"lon":-98.2760,"tipo":"verde",   "titulo":"Área verde crítica",      "desc":"Solo 1.1 m²/hab"},
        ],
    }
    _tipos_poi = {
        "verde":    {"color": "#22c55e", "emoji": "🌳"},
        "deporte":  {"color": "#8b5cf6", "emoji": "⚽"},
        "peatonal": {"color": "#0ea5e9", "emoji": "🚶"},
        "ultra":    {"color": "#ef4444", "emoji": "🍟"},
    }

    lat_c, lon_c = _coords.get(muni_nom, (19.05, -98.26))

    # ════════════════════════════════════════════════════════
    # INTENTO 1: flet_map embebido (funciona en todos lados)
    # ════════════════════════════════════════════════════════
    mapa_widget = None
    _ftm = None

    try:
        import flet_map as _ftm
    except ImportError:
        try:
            import flet.map as _ftm
        except ImportError:
            _ftm = None

    if _ftm is not None:
        try:
            # Construir marcadores para todos los municipios
            _markers = []
            _circles = []

            for _m in MUNICIPIOS:
                _iv = calc_iarri(_m["AV"], _m["IC"], _m["ED"], _m["EAR"], _m["IMP"])
                _nv, _cv = nivel_riesgo(_iv)
                _mlat, _mlon = _coords.get(_m["nombre"], (lat_c, lon_c))
                _activo = _m["nombre"] == muni_nom

                # Etiqueta del municipio
                _markers.append(_ftm.Marker(
                    coordinates=_ftm.MapLatitudeLongitude(_mlat, _mlon),
                    content=ft.Tooltip(
                        message=f"{_m['nombre']}\nIARRI: {_iv:.2f} — Riesgo {_nv}",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(_m["nombre"].split()[0], size=9,
                                        color=WHITE, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{_iv:.2f}", size=13,
                                        color=WHITE, weight=ft.FontWeight.W_900),
                            ], spacing=0,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=_cv,
                            padding=ft.padding.symmetric(horizontal=8, vertical=5),
                            border_radius=10,
                            border=ft.border.all(2 if _activo else 0, WHITE),
                            shadow=ft.BoxShadow(blur_radius=8, color="#00000066"),
                        ),
                    ),
                ))

                # Zona de riesgo como CircleMarker
                _circles.append(_ftm.CircleMarker(
                    coordinates=_ftm.MapLatitudeLongitude(_mlat, _mlon),
                    radius=700 + _iv * 1800,
                    use_radius_in_meter=True,
                    color=_cv,
                    fill_color=_cv,
                    fill_opacity=0.15,
                    border_stroke_width=2,
                    border_color=_cv,
                ))

            # POIs del municipio activo
            for _poi in _pois.get(muni_nom, []):
                _t = _tipos_poi.get(_poi["tipo"], {"color":"#888","emoji":"📍"})
                _markers.append(_ftm.Marker(
                    coordinates=_ftm.MapLatitudeLongitude(_poi["lat"], _poi["lon"]),
                    content=ft.Tooltip(
                        message=f"{_poi['titulo']}\n{_poi['desc']}",
                        content=ft.Container(
                            content=ft.Text(_t["emoji"], size=16),
                            bgcolor=_t["color"] + "DD",
                            width=30, height=30,
                            border_radius=15,
                            alignment=ft.alignment.Alignment(0, 0),
                            border=ft.border.all(1, WHITE),
                        ),
                    ),
                ))

            mapa_widget = ft.Column([
                _ftm.Map(
                    height=300,
                    initial_center=_ftm.MapLatitudeLongitude(lat_c, lon_c),
                    initial_zoom=12.5,
                    layers=[
                        _ftm.TileLayer(
                            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                            user_agent_package_name="arq_metabolica_mx",
                        ),
                        _ftm.CircleLayer(circles=_circles),
                        _ftm.MarkerLayer(markers=_markers),
                    ],
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MAP_ROUNDED, size=13, color=MUTED),
                        ft.Text("OpenStreetMap · toca un marcador para ver datos",
                                size=10, color=MUTED, italic=True),
                        ft.Container(expand=True),
                        ft.Text("OSM Contributors", size=9, color=MUTED, italic=True),
                    ], spacing=6),
                    padding=ft.padding.symmetric(horizontal=8, vertical=5),
                ),
            ], spacing=0)

        except Exception as _ex:
            print(f"[mapa] flet_map error: {_ex}")
            mapa_widget = None

    # ════════════════════════════════════════════════════════
    # INTENTO 2: Mapa HTML en navegador (fallback Desktop)
    # ════════════════════════════════════════════════════════
    if mapa_widget is None:
        _munis_js = []
        for _m in MUNICIPIOS:
            _iv = calc_iarri(_m["AV"], _m["IC"], _m["ED"], _m["EAR"], _m["IMP"])
            _nv, _cv = nivel_riesgo(_iv)
            _mlat, _mlon = _coords.get(_m["nombre"], (lat_c, lon_c))
            _munis_js.append({
                "nombre": _m["nombre"], "lat": _mlat, "lon": _mlon,
                "iarri": round(_iv,3), "nivel": _nv, "color": _cv,
                "AV":_m["AV"],"IC":_m["IC"],"ED":_m["ED"],
                "EAR":_m["EAR"],"IMP":_m["IMP"],
                "pois": _pois.get(_m["nombre"],[]),
            })
        _mj = _json.dumps(_munis_js, ensure_ascii=False)
        _tj = _json.dumps(_tipos_poi, ensure_ascii=False)

        _html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{height:100%;font-family:sans-serif}}
#map{{height:100vh;width:100vw}}
#panel{{position:absolute;top:10px;right:10px;z-index:1000;background:rgba(15,23,42,.93);
border-radius:14px;padding:12px 14px;width:185px;border:1px solid #334155;
color:#e2e8f0;max-height:80vh;overflow-y:auto}}
#panel h3{{font-size:11px;color:#38bdf8;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase}}
.mi{{padding:6px 0;border-bottom:1px solid #1e293b;cursor:pointer}}
.mi:last-child{{border-bottom:none}}.mn{{font-size:11px;font-weight:600}}
.mv{{font-size:14px;font-weight:900}}.ml{{font-size:10px;color:#64748b}}
.leaflet-popup-content-wrapper{{background:#0f172a;border:1px solid #334155;
border-radius:12px;color:#e2e8f0}}
.leaflet-popup-tip{{background:#0f172a}}
.pt{{font-size:13px;font-weight:700;color:#38bdf8;margin-bottom:4px}}
.pi{{font-size:24px;font-weight:900;margin:2px 0}}
.ps{{font-size:11px;color:#64748b}}
.pv{{display:flex;justify-content:space-between;font-size:11px;margin:2px 0}}
.pb{{background:#1e293b;border-radius:3px;height:5px;width:100%;margin-top:2px}}
.pf{{height:5px;border-radius:3px}}
</style></head><body>
<div id="map"></div>
<div id="panel"><h3>IARRI Municipal</h3><div id="lm"></div></div>
<script>
const MU={_mj};const TI={_tj};
const map=L.map('map',{{center:[{lat_c},{lon_c}],zoom:13}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'OpenStreetMap',maxZoom:19}}).addTo(map);
function popM(m){{
  const vs=[{{k:'AV',l:'Areas Verdes',i:'🌳',inv:true}},
    {{k:'IC',l:'Caminabilidad',i:'🚶',inv:true}},
    {{k:'ED',l:'Equip Dep',i:'⚽',inv:true}},
    {{k:'EAR',l:'Entorno Alim',i:'🍟',inv:false}},
    {{k:'IMP',l:'Marginacion',i:'📉',inv:false}}];
  const f=vs.map(v=>{{const val=m[v.k],r=v.inv?(1-val):val,
    c=r<.33?'#22c55e':r<.66?'#f59e0b':'#ef4444';
    return `<div class="pv"><span>${{v.i}} ${{v.l}}</span>
    <span style="color:${{c}};font-weight:700">${{val.toFixed(2)}}</span></div>
    <div class="pb"><div class="pf" style="width:${{val*100}}%;background:${{c}}"></div></div>`;}}).join('');
  return `<div style="min-width:185px"><div class="pt">${{m.nombre}}</div>
    <div class="pi" style="color:${{m.color}}">${{m.iarri.toFixed(2)}}</div>
    <div class="ps">Riesgo ${{m.nivel}} · Prob RI ${{(10+50*m.iarri).toFixed(0)}}%</div>
    <div style="margin-top:8px;border-top:1px solid #1e293b;padding-top:6px">${{f}}</div></div>`;}}
function icoP(tipo){{const c=TI[tipo]||{{color:'#888',emoji:'📍'}};
  return L.divIcon({{html:`<div style="background:${{c.color}};width:28px;height:28px;
    border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.5)">${{c.emoji}}</div>`,
    className:'',iconSize:[28,28],iconAnchor:[14,14]}});}}
const lm=document.getElementById('lm');
MU.forEach(m=>{{
  L.circle([m.lat,m.lon],{{radius:700+m.iarri*1800,color:m.color,fillColor:m.color,fillOpacity:.15,weight:2}})
    .bindPopup(popM(m),{{maxWidth:260}}).addTo(map);
  const ico=L.divIcon({{html:`<div style="background:${{m.color}};padding:3px 8px;
    border-radius:8px;font-size:11px;font-weight:700;color:#000;
    box-shadow:0 2px 10px rgba(0,0,0,.4);white-space:nowrap">
    ${{m.nombre.split(' ')[0]}} ${{m.iarri.toFixed(2)}}</div>`,className:'',iconAnchor:[45,12]}});
  L.marker([m.lat,m.lon],{{icon:ico}}).bindPopup(popM(m),{{maxWidth:260}}).addTo(map);
  (m.pois||[]).forEach(p=>{{
    L.marker([p.lat,p.lon],{{icon:icoP(p.tipo)}})
      .bindPopup(`<div style="min-width:145px"><b style="color:#38bdf8">${{p.titulo}}</b><br>
        <span style="font-size:11px;color:#64748b">${{p.desc}}</span></div>`,{{maxWidth:220}}).addTo(map);}});
  const d=document.createElement('div');d.className='mi';
  d.innerHTML=`<div class="mn">${{m.nombre}}</div>
    <div class="mv" style="color:${{m.color}}">${{m.iarri.toFixed(2)}}</div>
    <div class="ml">Riesgo ${{m.nivel}}</div>`;
  d.onclick=()=>map.flyTo([m.lat,m.lon],14,{{duration:1}});lm.appendChild(d);}});
</script></body></html>"""

        _ruta = _os2.path.abspath("mapa_arq.html")
        with open(_ruta, "w", encoding="utf-8") as _fh:
            _fh.write(_html)

        import webbrowser as _wb
        def _abrir(e=None):
            _wb.open(f"file:///{_ruta.replace(_os2.sep, '/')}")

        # Detectar si estamos en web
        _es_web = getattr(page, "web", False)

        if _es_web:
            mapa_widget = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WEB_ROUNDED, size=36, color=ACCENT),
                    ft.Text("Mapa en ejecución en web", size=14,
                            weight=ft.FontWeight.W_600, color=TEXT),
                    ft.Text("Instala flet-map para ver el mapa aquí:\npip install flet-map",
                            size=11, color=MUTED, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.Alignment(0, 0),
                height=180,
                bgcolor=ACCENT + "08",
                border=ft.border.all(1, ACCENT + "33"),
                border_radius=16,
            )
        else:
            mapa_widget = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("🗺️  Mapa Interactivo IARRI", size=13,
                                weight=ft.FontWeight.W_700, color=TEXT),
                        ft.Text("Instala flet-map para ver aquí, o abre en navegador:",
                                size=10, color=MUTED),
                        ft.Text("pip install flet-map", size=10,
                                color=ACCENT, font_family="monospace"),
                    ], spacing=3, expand=True),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.OPEN_IN_BROWSER_ROUNDED, color=WHITE, size=16),
                            ft.Text("Abrir mapa", size=12,
                                    weight=ft.FontWeight.BOLD, color=WHITE),
                        ], spacing=6, tight=True),
                        on_click=_abrir,
                        style=ft.ButtonStyle(
                            bgcolor=ACCENT,
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        ),
                    ),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ACCENT + "10",
                border=ft.border.all(1, ACCENT + "44"),
                border_radius=14, padding=14,
            )

    # ── Leyenda ───────────────────────────────────────────────
    leyenda = ft.Row([
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=LOW),
                ft.Text("Bajo",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=MID),
                ft.Text("Medio",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Container(width=8,height=8,border_radius=4,bgcolor=HIGH),
                ft.Text("Alto",size=10,color=MUTED)],spacing=4),
        ft.Row([ft.Text("🌳",size=11),ft.Text("🚶",size=11),
                ft.Text("⚽",size=11),ft.Text("🍟",size=11)]),
        ft.Text("OSM · INEGI 2020",size=9,color=MUTED,italic=True),
    ], spacing=10, wrap=True)

    # ── Mini-mapa de barras (siempre visible) ─────────────────
    def _mini():
        rows = []
        for _m in MUNICIPIOS:
            _iv = calc_iarri(_m["AV"],_m["IC"],_m["ED"],_m["EAR"],_m["IMP"])
            _nv, _cv = nivel_riesgo(_iv)
            rows.append(ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(_m["nombre"].split()[0], size=9,
                                    weight=ft.FontWeight.BOLD, color=_cv),
                            ft.Text(f"{_iv:.2f}", size=13,
                                    weight=ft.FontWeight.W_900, color=_cv),
                        ], spacing=1,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=_cv+"20", border=ft.border.all(1,_cv+"66"),
                        border_radius=10, padding=8, width=70,
                    ),
                    ft.Column([
                        *[ft.Row([
                            ft.Text(_ico, size=10),
                            ft.Container(
                                content=ft.Container(bgcolor=_vc,border_radius=2,
                                                     height=5,width=_vv*130),
                                bgcolor=BORDER,border_radius=2,height=5,
                                width=130,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            ),
                            ft.Text(f"{_vv:.2f}",size=9,color=_vc,
                                    width=26,text_align=ft.TextAlign.RIGHT),
                        ],spacing=4)
                        for _ico,_key,_inv in [("🌳","AV",True),("🚶","IC",True),
                                               ("⚽","ED",True),("🍟","EAR",False)]
                        for _vv in [_m[_key]]
                        for _vc in [LOW if (_vv if not _inv else 1-_vv)<0.33
                                    else MID if (_vv if not _inv else 1-_vv)<0.66
                                    else HIGH]
                        ],
                    ], spacing=3, expand=True),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD, border=ft.border.all(1,_cv+"33"),
                border_radius=14, padding=10,
                margin=ft.margin.only(bottom=6),
                shadow=ft.BoxShadow(blur_radius=4,color="#0000000a",offset=ft.Offset(0,1)),
            ))
        return rows

    # ── Variables territoriales ───────────────────────────────
    def _var_card(icon,titulo,valor_str,sub,pct,color,nota_izq="",nota_der=""):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(icon,size=20),bgcolor=color+"20",
                                 border_radius=10,width=38,height=38,
                                 alignment=ft.alignment.Alignment(0,0)),
                    ft.Column([ft.Text(titulo,size=11,weight=ft.FontWeight.W_600,color=TEXT),
                               ft.Text(sub,size=10,color=MUTED)],spacing=1,expand=True),
                    ft.Text(valor_str,size=18,weight=ft.FontWeight.W_900,color=color),
                ],spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Container(bgcolor=color,border_radius=4,height=7,
                                         width=max(4,min(1.0,pct))*300),
                    bgcolor=BORDER,border_radius=4,height=7,
                    expand=True,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Row([ft.Text(nota_izq,size=9,color=MUTED),
                        ft.Container(expand=True),
                        ft.Text(nota_der,size=9,color=MUTED)]),
            ],spacing=2),
            bgcolor=CARD, border=ft.border.all(1,color+"44"),
            border_radius=16, padding=14,
            shadow=ft.BoxShadow(blur_radius=6,color="#0000000a",offset=ft.Offset(0,1)),
            margin=ft.margin.only(bottom=10),
        )

    av_m2    = datos_ter.get("areas_verdes_m2",0)
    av_pct   = av_m2/datos_ter.get("oms_standard",9.0)
    av_col   = LOW if av_pct>=0.8 else MID if av_pct>=0.4 else HIGH
    dens     = datos_ter.get("densidad_pob",0)
    dens_pct = dens/datos_ter.get("densidad_max",12000)
    dens_col = HIGH if dens_pct>=0.8 else MID if dens_pct>=0.5 else LOW
    marg     = datos_ter.get("marginacion",0)
    marg_col = HIGH if marg>=0.6 else MID if marg>=0.3 else LOW
    equip    = datos_ter.get("equipamiento_dep",0)
    equip_pct= equip/datos_ter.get("equip_ideal",6.0)
    equip_col= LOW if equip_pct>=0.6 else MID if equip_pct>=0.3 else HIGH
    movil    = datos_ter.get("movilidad_peat",0)
    movil_col= LOW if movil>=0.6 else MID if movil>=0.35 else HIGH
    ultra    = datos_ter.get("tiendas_ultra",0)
    ultra_col= HIGH if ultra>=0.6 else MID if ultra>=0.4 else LOW

    # ── Ranking ───────────────────────────────────────────────
    munis_sorted = sorted(
        [{**_m,"iarri":calc_iarri(_m["AV"],_m["IC"],_m["ED"],_m["EAR"],_m["IMP"])}
         for _m in MUNICIPIOS], key=lambda x:x["iarri"])
    rank_rows = []
    for _i,_m in enumerate(munis_sorted):
        _nv,_cv = nivel_riesgo(_m["iarri"])
        rank_rows.append(ft.Container(
            content=ft.Row([
                ft.Text(f"#{_i+1}",size=16,weight=ft.FontWeight.W_900,color=MUTED,width=28),
                ft.Column([
                    ft.Text(_m["nombre"],size=12,weight=ft.FontWeight.W_600,color=TEXT),
                    ft.Container(
                        content=ft.Container(bgcolor=_cv,border_radius=3,height=5,
                                             width=_m["iarri"]*200),
                        bgcolor=BORDER,border_radius=3,height=5,
                        expand=True,clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        margin=ft.margin.only(top=4),
                    ),
                ],spacing=2,expand=True),
                ft.Column([
                    ft.Text(f"{_m['iarri']:.2f}",size=16,
                            weight=ft.FontWeight.W_900,color=_cv),
                    ft.Text(f"Prob RI {prob_ri(_m['iarri'])*100:.0f}%",
                            size=9,color=MUTED),
                ],spacing=0,horizontal_alignment=ft.CrossAxisAlignment.END),
            ],spacing=10,vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CARD,border=ft.border.all(1,_cv+"33"),
            border_radius=14,padding=14,
            margin=ft.margin.only(bottom=8),
            shadow=ft.BoxShadow(blur_radius=4,color="#0000000a",offset=ft.Offset(0,1)),
        ))

    # ── Layout final ──────────────────────────────────────────
    return ft.Column([
        perfil_header,
        ft.Container(height=10),
        ft.Container(
            content=mapa_widget,
            border=ft.border.all(1, BORDER),
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=6,color="#0000000a",offset=ft.Offset(0,2)),
        ),
        ft.Container(height=6),
        leyenda,
        ft.Container(height=14),
        titulo_seccion("COMPARATIVA RÁPIDA"),
        ft.Container(height=6),
        *_mini(),
        ft.Container(height=14),
        titulo_seccion("VARIABLES TERRITORIALES — INEGI / DENUE / CONAPO"),
        ft.Container(height=8),
        _var_card("🌳","Acceso a Áreas Verdes",f"{av_m2} m²/hab",
                  "OMS: 9 m²/hab",av_pct,av_col,"0 m²",
                  f"OMS 9 m² {'✓' if av_pct>=1 else '✗'}"),
        _var_card("🏘️","Densidad Poblacional",f"{dens:,}/km²".replace(",","  "),
                  "INEGI Censo 2020",dens_pct,dens_col,"Baja","Alta"),
        _var_card("📉","Índice de Marginación",f"{marg:.2f}",
                  "CONAPO",marg,marg_col,"Sin marginación","Muy alto"),
        _var_card("⚽","Equipamiento Deportivo",f"{equip}/10k hab",
                  "Instalaciones activas",equip_pct,equip_col,"0",
                  f"Ideal: {datos_ter.get('equip_ideal',6)}/10k"),
        _var_card("🚶","Movilidad Peatonal",f"{movil*100:.0f}%",
                  "Banquetas en buen estado",movil,movil_col,"0%","100%"),
        _var_card("🍟","Entorno Alimentario Riesgoso",f"{ultra*100:.0f}%",
                  "Ultraprocesados/total DENUE",ultra,ultra_col,"Sin riesgo","100%"),
        titulo_seccion("RANKING MUNICIPAL"),
        ft.Container(height=8),
        *rank_rows,
        ft.Container(height=28),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)
