"""
core/datos.py — Constantes de datos de la aplicación IARRI-MX

Municipios, datos territoriales, encuesta, variables, recomendaciones,
badges y lecciones educativas.

Sin imports de Flet ni de ninguna librería UI.
Fuente: main.py líneas 1-211, 2280-2431
"""

import os as _os
import csv as _csv

# ─── CARGA DATOS INEGI DESDE CSV ─────────────────────────────────────────────

def _cargar_datos_csv():
    """Lee datos_inegi_puebla.csv si existe. Retorna dict por nombre de municipio."""
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "datos_inegi_puebla.csv")
    ruta = _os.path.normpath(ruta)
    if not _os.path.exists(ruta):
        return None
    try:
        resultado = {}
        with open(ruta, encoding="utf-8-sig") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                nombre = row.get("nombre", "").strip()
                if nombre:
                    resultado[nombre] = {
                        "poblacion":        int(float(row.get("poblacion_2020", 0) or 0)),
                        "densidad_pob":     int(float(row.get("densidad_hab_km2", 0) or 0)),
                        "areas_verdes_m2":  float(row.get("areas_verdes_m2_hab", 0) or 0),
                        "marginacion":      float(row.get("indice_marginacion", 0) or 0),
                        "grado_marginacion":row.get("grado_marginacion", "—"),
                        "equipamiento_dep": float(row.get("equipamiento_dep_10k", 0) or 0),
                        "movilidad_peat":   float(row.get("movilidad_peatonal", 0) or 0),
                        "tiendas_ultra":    float(row.get("EAR", 0) or 0),
                        "fuente":           row.get("fuente", "CSV local"),
                    }
        print(f"[INEGI] CSV cargado: {len(resultado)} municipios")
        return resultado
    except Exception as ex:
        print(f"[INEGI] Error leyendo CSV: {ex}")
        return None


_csv_datos = _cargar_datos_csv()

# ─── MUNICIPIOS ───────────────────────────────────────────────────────────────
# Los tres municipios del área metropolitana de Puebla estudiados
MUNICIPIOS = [
    {"nombre": "San Andrés Cholula",      "AV": 0.80, "IC": 0.60, "ED": 0.40, "EAR": 0.45, "IMP": 0.10},
    {"nombre": "San Pablo Xochimehuacan", "AV": 0.50, "IC": 0.35, "ED": 0.20, "EAR": 0.60, "IMP": 0.55},
    {"nombre": "Cuautlancingo",           "AV": 0.30, "IC": 0.20, "ED": 0.10, "EAR": 0.80, "IMP": 0.70},
]

# ─── DATOS TERRITORIALES INEGI ────────────────────────────────────────────────
# Fuente: INEGI Censos 2020, DENUE, CONAPO (valores reales aproximados)
DATOS_TERRITORIALES = {
    "San Andrés Cholula": {
        # Densidad poblacional (hab/km²)
        "densidad_pob":     4800,
        "densidad_max":     12000,
        # Áreas verdes (m² por habitante)
        "areas_verdes_m2":  6.2,
        "oms_standard":     9.0,
        # Índice de marginación CONAPO (0=bajo, 1=muy alto)
        "marginacion":      0.10,
        # Equipamiento deportivo (instalaciones por 10k hab)
        "equipamiento_dep": 3.8,
        "equip_ideal":      6.0,
        # Movilidad peatonal — % banquetas en buen estado
        "movilidad_peat":   0.62,
        # Comercios ultraprocesados / comercios totales (DENUE)
        "tiendas_ultra":    0.41,
        # Población total (Censo 2020)
        "poblacion":        115_613,
        # Colonias — 5 variables completas + datos demográficos
        # av=Áreas Verdes, ic=Caminabilidad, ed=Equip.Deportivo, ear=Entorno Alim., imp=Marginación
        "colonias": [
            {
                "nombre": "San Andrés Cholula Centro",
                "iarri": 0.28, "av": 0.85, "ic": 0.70, "ed": 0.75, "ear": 0.30, "imp": 0.08,
                "poblacion": 18_200, "densidad_pob": 3800,
                "areas_verdes_m2": 8.2, "movilidad_peat": 0.78,
                "equipamiento_dep": 5.2, "tiendas_ultra": 0.30,
                "marginacion": 0.08, "grado_marginacion": "Muy bajo",
                "descripcion": "Zona histórica con buena infraestructura peatonal y parques.",
            },
            {
                "nombre": "Ex-Hacienda Zavaleta",
                "iarri": 0.34, "av": 0.65, "ic": 0.60, "ed": 0.55, "ear": 0.40, "imp": 0.12,
                "poblacion": 22_400, "densidad_pob": 5200,
                "areas_verdes_m2": 5.8, "movilidad_peat": 0.62,
                "equipamiento_dep": 3.8, "tiendas_ultra": 0.42,
                "marginacion": 0.12, "grado_marginacion": "Muy bajo",
                "descripcion": "Zona residencial de nivel medio-alto con centros comerciales.",
            },
            {
                "nombre": "La Carcaña",
                "iarri": 0.42, "av": 0.50, "ic": 0.45, "ed": 0.40, "ear": 0.55, "imp": 0.22,
                "poblacion": 31_500, "densidad_pob": 7100,
                "areas_verdes_m2": 4.1, "movilidad_peat": 0.45,
                "equipamiento_dep": 2.1, "tiendas_ultra": 0.56,
                "marginacion": 0.22, "grado_marginacion": "Bajo",
                "descripcion": "Zona de transición urbana con densidad media y servicios mixtos.",
            },
            {
                "nombre": "San Bernardino Tlaxcalancingo",
                "iarri": 0.38, "av": 0.60, "ic": 0.55, "ed": 0.50, "ear": 0.45, "imp": 0.18,
                "poblacion": 27_800, "densidad_pob": 6000,
                "areas_verdes_m2": 5.1, "movilidad_peat": 0.55,
                "equipamiento_dep": 2.9, "tiendas_ultra": 0.46,
                "marginacion": 0.18, "grado_marginacion": "Muy bajo",
                "descripcion": "Zona periférica en crecimiento con vegetación moderada.",
            },
        ],
    },
    "San Pablo Xochimehuacan": {
        "densidad_pob":     8200,
        "densidad_max":     12000,
        "areas_verdes_m2":  2.8,
        "oms_standard":     9.0,
        "marginacion":      0.55,
        "equipamiento_dep": 1.9,
        "equip_ideal":      6.0,
        "movilidad_peat":   0.35,
        "tiendas_ultra":    0.62,
        "poblacion":        52_408,
        "colonias": [
            {
                "nombre": "Xochimehuacan Norte",
                "iarri": 0.58, "av": 0.30, "ic": 0.35, "ed": 0.25, "ear": 0.65, "imp": 0.52,
                "poblacion": 18_600, "densidad_pob": 9200,
                "areas_verdes_m2": 2.2, "movilidad_peat": 0.30,
                "equipamiento_dep": 1.4, "tiendas_ultra": 0.66,
                "marginacion": 0.52, "grado_marginacion": "Medio",
                "descripcion": "Zona norte con alta densidad y escasos espacios verdes.",
            },
            {
                "nombre": "Xochimehuacan Sur",
                "iarri": 0.64, "av": 0.25, "ic": 0.30, "ed": 0.20, "ear": 0.72, "imp": 0.60,
                "poblacion": 20_100, "densidad_pob": 10_500,
                "areas_verdes_m2": 1.8, "movilidad_peat": 0.25,
                "equipamiento_dep": 0.9, "tiendas_ultra": 0.74,
                "marginacion": 0.60, "grado_marginacion": "Alto",
                "descripcion": "Zona de mayor vulnerabilidad. Alta densidad y entorno alimentario adverso.",
            },
            {
                "nombre": "El Barrio Nuevo",
                "iarri": 0.55, "av": 0.35, "ic": 0.38, "ed": 0.30, "ear": 0.60, "imp": 0.48,
                "poblacion": 13_700, "densidad_pob": 7800,
                "areas_verdes_m2": 2.9, "movilidad_peat": 0.34,
                "equipamiento_dep": 1.6, "tiendas_ultra": 0.60,
                "marginacion": 0.48, "grado_marginacion": "Medio",
                "descripcion": "Barrio emergente con servicios limitados y movilidad deficiente.",
            },
        ],
    },
    "Cuautlancingo": {
        "densidad_pob":     11400,
        "densidad_max":     12000,
        "areas_verdes_m2":  1.1,
        "oms_standard":     9.0,
        "marginacion":      0.70,
        "equipamiento_dep": 0.8,
        "equip_ideal":      6.0,
        "movilidad_peat":   0.22,
        "tiendas_ultra":    0.78,
        "poblacion":        103_994,
        "colonias": [
            {
                "nombre": "Cuautlancingo Centro",
                "iarri": 0.76, "av": 0.15, "ic": 0.22, "ed": 0.12, "ear": 0.82, "imp": 0.68,
                "poblacion": 28_400, "densidad_pob": 11_800,
                "areas_verdes_m2": 0.9, "movilidad_peat": 0.20,
                "equipamiento_dep": 0.6, "tiendas_ultra": 0.84,
                "marginacion": 0.68, "grado_marginacion": "Alto",
                "descripcion": "Centro urbano de alta densidad industrial. Mayor riesgo metabólico del municipio.",
            },
            {
                "nombre": "Lomas de Cuautlancingo",
                "iarri": 0.71, "av": 0.20, "ic": 0.25, "ed": 0.18, "ear": 0.78, "imp": 0.62,
                "poblacion": 31_200, "densidad_pob": 10_900,
                "areas_verdes_m2": 1.2, "movilidad_peat": 0.22,
                "equipamiento_dep": 0.9, "tiendas_ultra": 0.80,
                "marginacion": 0.62, "grado_marginacion": "Alto",
                "descripcion": "Zona habitacional densa con muy poca infraestructura verde o deportiva.",
            },
            {
                "nombre": "San Pedro Zacachimalpa",
                "iarri": 0.80, "av": 0.10, "ic": 0.18, "ed": 0.08, "ear": 0.88, "imp": 0.74,
                "poblacion": 22_600, "densidad_pob": 12_000,
                "areas_verdes_m2": 0.5, "movilidad_peat": 0.15,
                "equipamiento_dep": 0.4, "tiendas_ultra": 0.90,
                "marginacion": 0.74, "grado_marginacion": "Muy alto",
                "descripcion": "Zona crítica. Densidad máxima, sin áreas verdes y alta marginación.",
            },
            {
                "nombre": "Parques Industriales",
                "iarri": 0.74, "av": 0.18, "ic": 0.20, "ed": 0.15, "ear": 0.80, "imp": 0.66,
                "poblacion": 21_800, "densidad_pob": 11_200,
                "areas_verdes_m2": 1.0, "movilidad_peat": 0.18,
                "equipamiento_dep": 0.7, "tiendas_ultra": 0.82,
                "marginacion": 0.66, "grado_marginacion": "Alto",
                "descripcion": "Entorno industrial con habitantes en condiciones de alta vulnerabilidad metabólica.",
            },
        ],
    },
}

# ─── ENCUESTA ─────────────────────────────────────────────────────────────────
# NOTA: estas preguntas estiman la percepción personal del usuario sobre su entorno
# y hábitos. Los valores resultantes alimentan las mismas variables del modelo IARRI
# (AV, IC, ED, EAR) como proxy individual — NO reemplazan los datos INEGI/DENUE
# del análisis territorial del mapa.
ENCUESTA = [
    {
        "variable": "AV",  # proxy personal: percepción de acceso a espacios activos
        "pregunta": "¿Cómo describirías el acceso a espacios verdes o para caminar en tu zona?",
        "opciones": [
            {"texto": "Tengo parques o áreas verdes cerca y los uso regularmente.", "valor": 0.8},
            {"texto": "No tengo espacios cercanos o no puedo usarlos actualmente.", "valor": 0.2},
            {"texto": "Prefiero no responder.", "valor": 0.5},
        ],
    },
    {
        "variable": "IC",  # proxy personal: nivel de actividad física cotidiana
        "pregunta": "¿Cuántas horas pasás al día sentado (trabajo, transporte, pantallas)?",
        "opciones": [
            {"texto": "Menos de dos horas al día.",                "valor": 0.8},
            {"texto": "Más de seis horas al día.",                 "valor": 0.2},
            {"texto": "Menos de una hora al día.",                 "valor": 0.9},
        ],
    },
    {
        "variable": "ED",  # proxy personal: acceso y uso de infraestructura deportiva
        "pregunta": "¿Practicás algún deporte o actividad física estructurada de forma regular?",
        "opciones": [
            {"texto": "Sí, entreno de forma constante.",       "valor": 0.85},
            {"texto": "No practico ningún deporte.",           "valor": 0.1},
            {"texto": "Hago algo de actividad pero muy poco.", "valor": 0.4},
        ],
    },
    {
        "variable": "EAR",  # proxy personal: exposición a ultraprocesados
        "pregunta": "¿Con qué frecuencia consumís productos empaquetados con azúcar o ultraprocesados?",
        "opciones": [
            {"texto": "Al menos una vez a la semana.", "valor": 0.7},
            {"texto": "No consumo ese tipo de alimentos.", "valor": 0.1},
        ],
    },
]

# ─── VARIABLES ────────────────────────────────────────────────────────────────
# Definición de las 5 variables del modelo IARRI
# Los colores son strings hex — sin dependencia de UI
VARIABLES = [
    {"key": "AV",  "label": "Áreas Verdes",                          "icon": "🌳", "color": "#22c55e", "inv": True,  "desc": "Estándar OMS 9 m²/hab"},
    {"key": "IC",  "label": "Índice Caminabilidad",                   "icon": "🚶", "color": "#0ea5e9", "inv": True,  "desc": "Intersecciones + banquetas"},
    {"key": "ED",  "label": "Equipamiento Deportivo",                 "icon": "⚽", "color": "#8b5cf6", "inv": True,  "desc": "Equipamientos / población"},
    {"key": "EAR", "label": "Entorno Alimentario Riesgoso(LUGARES)",  "icon": "🍟", "color": "#f97316", "inv": False, "desc": "Tiendas ultraprocesados / total"},
    {"key": "IMP", "label": "Índice de Marginación",                  "icon": "📉", "color": "#f59e0b", "inv": False, "desc": "CONAPO normalizado"},
]

# ─── VARIABLES IARM ───────────────────────────────────────────────────────────
# Definición de los 4 factores del IARM (Índice Arquitectónico de Riesgo Metabólico)
# Todos son de riesgo DIRECTO: mayor valor = mayor riesgo ambiental territorial.
# Los colores son strings hex — sin dependencia de UI.
VARIABLES_IARM = [
    {
        "key":   "ST",
        "label": "Sedentarismo Territorial",
        "icon":  "🪑",
        "color": "#ef4444",
        "inv":   False,
        "desc":  "% población sin actividad física en la zona",
    },
    {
        "key":   "BAV",
        "label": "Baja Área Verde",
        "icon":  "🏜️",
        "color": "#f97316",
        "inv":   False,
        "desc":  "Déficit de m² de área verde por habitante",
    },
    {
        "key":   "DEN",
        "label": "Alta Densidad Poblacional",
        "icon":  "🏙️",
        "color": "#f59e0b",
        "inv":   False,
        "desc":  "Hab/km² normalizado respecto al máximo municipal",
    },
    {
        "key":   "BEA",
        "label": "Bajo Equipamiento Activo",
        "icon":  "🚫",
        "color": "#8b5cf6",
        "inv":   False,
        "desc":  "Déficit de instalaciones deportivas / 10k hab",
    },
]

# ─── RECOMENDACIONES IARM ─────────────────────────────────────────────────────
# Acciones e intervenciones según nivel de riesgo del IARM
RECOMENDACIONES_IARM = {
    "Bajo riesgo ambiental": {
        "icono":   "✅",
        "color":   "#22c55e",
        "titulo":  "Entorno favorable — mantener y reforzar",
        "items": [
            "Documentar las buenas prácticas de diseño urbano existentes.",
            "Promover la actividad física espontánea aprovechando la infraestructura actual.",
            "Participar en programas de mantenimiento de áreas verdes y equipamiento.",
        ],
    },
    "Riesgo medio": {
        "icono":   "🟡",
        "color":   "#f59e0b",
        "titulo":  "Intervención preventiva recomendada",
        "items": [
            "Identificar los 2 factores con peor puntaje y priorizar su mejora.",
            "Gestionar ante autoridades la ampliación de áreas verdes en déficit.",
            "Proponer rutas peatonales seguras para reducir sedentarismo territorial.",
            "Revisar densificación urbana y su impacto en calidad de vida activa.",
        ],
    },
    "Alto riesgo": {
        "icono":   "🚨",
        "color":   "#ef4444",
        "titulo":  "Alerta — intervención urgente requerida",
        "items": [
            "Gestión urgente de equipamiento deportivo: al menos 2 unidades barriales.",
            "Plan emergente de áreas verdes: mínimo 1 parque de bolsillo por colonia.",
            "Reducción de densidad en nuevos desarrollos mediante normativa.",
            "Programa municipal de activación física con incentivos comunitarios.",
            "Diagnóstico participativo con residentes para co-diseñar intervenciones.",
        ],
    },
}

# ─── RECOMENDACIONES ──────────────────────────────────────────────────────────
RECOMENDACIONES = [
    {"icon": "🌳", "color": "#22c55e", "titulo": "Incrementar Áreas Verdes",  "desc": "Corredores verdes y microparques. AV: 0.30 → 0.55",          "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🚶", "color": "#0ea5e9", "titulo": "Ruta Diaria de 15 min",     "desc": "Banquetas accesibles e iluminación. IC: 0.20 → 0.45",         "impacto": "↓ IARRI −0.0625 (−8%)"},
    {"icon": "⚽", "color": "#8b5cf6", "titulo": "Espacios Deportivos",        "desc": "2 unidades barriales abiertas. ED: 0.10 → 0.30",              "impacto": "↓ IARRI −0.03 (−3.8%)"},
    {"icon": "🏗️","color": "#f97316", "titulo": "Regulación Alimentaria",     "desc": "Reducir ultraprocesados. EAR: 0.80 → 0.60",                   "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🪟", "color": "#f59e0b", "titulo": "Diseño Arquitectónico",      "desc": "Ventilación cruzada y acceso escaleras",                      "impacto": "Compensación: +18%"},
]

# ─── ARQUITECTURA PREVENTIVA ──────────────────────────────────────────────────
# Recomendaciones personalizadas basadas en principios OMS de entorno saludable.
# Cada item tiene: id, icon, color, titulo, subtitulo, descripcion, pasos (lista),
# oms_ref (referencia OMS), impacto_estimado (texto), categoria.
ARQ_PREVENTIVA = [
    {
        "id":       "ruta_peatonal",
        "icon":     "🚶",
        "color":    "#0ea5e9",   # Azul cielo
        "titulo":   "Ruta Peatonal Diaria",
        "subtitulo": "15–30 min caminados en tu colonia",
        "descripcion": (
            "Diseñar una ruta peatonal personal y repetirla a diario activa el músculo "
            "sin necesitar instalaciones. La OMS recomienda al menos 150 min semanales "
            "de actividad física moderada — una caminata diaria de 20 min los cubre."
        ),
        "pasos": [
            "Identificá 2–3 rutas desde tu casa con banquetas accesibles.",
            "Fijá una hora fija (mañana o tarde) para crear hábito.",
            "Sumá 5 min cada semana hasta llegar a 30 min continuos.",
            "Registrá la ruta en un mapa y compartila con alguien de tu familia.",
        ],
        "oms_ref":          "OMS — Actividad física: 150 min/sem moderada (2020)",
        "impacto_estimado": "↓ 30% riesgo diabetes tipo 2 con 30 min/día",
        "categoria":        "movimiento",
    },
    {
        "id":       "rediseno_espacio",
        "icon":     "🏠",
        "color":    "#8b5cf6",   # Violeta
        "titulo":   "Rediseño de Patio o Vivienda",
        "subtitulo": "Espacios que invitan al movimiento",
        "descripcion": (
            "El diseño del hogar puede sumar o restar actividad física involuntaria. "
            "Reorganizar muebles, liberar pasillos y crear zonas activas dentro "
            "del hogar aumenta el movimiento espontáneo, especialmente en viviendas "
            "con espacio exterior limitado."
        ),
        "pasos": [
            "Liberá al menos 4 m² de espacio libre para estiramiento o ejercicio.",
            "Mové el escritorio/TV para que requieran levantarse con más frecuencia.",
            "Creá una zona de estiramiento con tapete y acceso a luz natural.",
            "Si tenés patio: habilitá un circuito corto (5 min) de caminata.",
        ],
        "oms_ref":          "OMS — Ciudades saludables: entorno construido activo (2016)",
        "impacto_estimado": "+8–12% actividad física diaria sin esfuerzo consciente",
        "categoria":        "diseño",
    },
    {
        "id":       "ventilacion_luz",
        "icon":     "🪟",
        "color":    "#f59e0b",   # Ámbar
        "titulo":   "Ventilación y Luz Natural",
        "subtitulo": "Neuroarquitectura aplicada al hogar",
        "descripcion": (
            "La luz natural regula el ritmo circadiano y mejora el sueño — factor "
            "directo en la sensibilidad a la insulina. La ventilación cruzada "
            "reduce el CO₂ interior y el cortisol. Estudios de neuroarquitectura "
            "muestran reducciones de hasta 18% en marcadores de estrés."
        ),
        "pasos": [
            "Abrí ventanas opuestas 10 min al día para ventilación cruzada.",
            "Exponete a luz solar directa dentro de la primera hora al despertar.",
            "Reubicá tu zona de trabajo cerca de la fuente de luz natural.",
            "Usá cortinas translúcidas en vez de opacas durante el día.",
        ],
        "oms_ref":          "OMS — Calidad de aire en interiores y salud (2010)",
        "impacto_estimado": "↓ 18% cortisol — mejora de sueño y sensibilidad insulínica",
        "categoria":        "diseño",
    },
    {
        "id":       "microhuerto",
        "icon":     "🌱",
        "color":    "#22c55e",   # Verde
        "titulo":   "Microhuerto Urbano",
        "subtitulo": "Vegetales frescos a costo mínimo",
        "descripcion": (
            "Un microhuerto en azotea, balcón o ventana provee acceso directo a "
            "vegetales frescos con bajo índice glucémico. Además, la actividad de "
            "jardinería urbana suma movimiento liviano diario y reduce el estrés. "
            "Es la intervención alimentaria de menor costo y mayor impacto en zonas "
            "con alto entorno alimentario riesgoso (EAR)."
        ),
        "pasos": [
            "Empezá con 3 plantas en macetas: jitomate, chile y hierba aromática.",
            "Ubicá las macetas en el espacio con más horas de sol directo.",
            "Dedicá 10 min diarios al riego — es actividad física y reducción de estrés.",
            "Expandí progresivamente con lechuga, espinaca o nopal.",
        ],
        "oms_ref":          "OMS — Agricultura urbana y seguridad alimentaria (2017)",
        "impacto_estimado": "↑ consumo de fibra vegetal — ↓ índice glucémico de la dieta",
        "categoria":        "nutricion",
    },
    {
        "id":       "escaleras_activas",
        "icon":     "🏛️",
        "color":    "#f97316",   # Naranja
        "titulo":   "Espacios Activos: Escaleras Visibles",
        "subtitulo": "Arquitectura que suma pasos sin pensarlo",
        "descripcion": (
            "Hacer que las escaleras sean el camino más obvio y atractivo incrementa "
            "su uso hasta en un 30% frente a los elevadores. Este principio de "
            "'default activo' es uno de los más estudiados por la OMS en intervenciones "
            "de entorno construido: no requiere motivación, solo buen diseño."
        ),
        "pasos": [
            "Si usás escaleras en tu edificio, priorizalas sobre el elevador siempre.",
            "En casa: colocá elementos que 'inviten' a subir (plantas en escalones, iluminación).",
            "Proponé a tu edificio señalizar las escaleras con mensajes motivadores.",
            "Contá pisos subidos por semana como métrica de actividad.",
        ],
        "oms_ref":          "OMS — Entornos físicamente activos: evidencia y guías (2021)",
        "impacto_estimado": "+30% uso de escaleras con diseño visible — +150 kcal/semana",
        "categoria":        "movimiento",
    },
]

# ─── BADGES ───────────────────────────────────────────────────────────────────
BADGES = [
    {"emoji": "🏛️", "nombre": "Arquitecto Preventivo", "earned": True},
    {"emoji": "🌱", "nombre": "Diseñador Bioactivo",    "earned": True},
    {"emoji": "⚡", "nombre": "Agente Metabólico",      "earned": False},
    {"emoji": "📊", "nombre": "Analista Territorial",   "earned": False},
    {"emoji": "🗺️", "nombre": "Mapeador Urbano",        "earned": True},
    {"emoji": "🔬", "nombre": "Investigador IARRI",     "earned": False},
]

# ─── LECCIONES ────────────────────────────────────────────────────────────────
# Módulo educativo — 7 lecciones con contenido y quiz
# Fuente: main.py líneas 2280-2431
# Los colores se referencian como strings hex (no como variables de Flet)
_ACCENT  = "#0ea5e9"   # Azul cielo
_ACCENT3 = "#8b5cf6"   # Violeta
_LOW     = "#22c55e"   # Verde
_MID     = "#f59e0b"   # Ámbar
_HIGH    = "#ef4444"   # Rojo

LECCIONES = [
    {
        "id": 0,
        "titulo": "¿Qué es la Resistencia a la Insulina?",
        "emoji": "🔬",
        "color": _ACCENT,
        "contenido": [
            ("¿Qué es la insulina?", "La insulina es una hormona producida por el páncreas. Su función es permitir que el azúcar (glucosa) de los alimentos entre a las células para usarse como energía."),
            ("¿Qué pasa con la resistencia?", "Cuando las células dejan de responder bien a la insulina, el páncreas produce cada vez más para compensar. Con el tiempo esto puede llevar a prediabetes y diabetes tipo 2."),
            ("¿Es común?", "En México, más del 30% de la población adulta tiene algún grado de resistencia a la insulina, muchas veces sin saberlo."),
            ("Señales de alerta", "Cansancio después de comer, antojos de azúcar, dificultad para bajar de peso en el abdomen y piel oscura en cuello o axilas (acantosis nigricans)."),
        ],
        "quiz": [
            {
                "pregunta": "¿Cuál es la función principal de la insulina?",
                "opciones": ["Quemar grasa directamente", "Permitir que la glucosa entre a las células", "Producir energía en el páncreas", "Regular la presión arterial"],
                "correcta": 1,
            },
            {
                "pregunta": "¿Cómo se llama la mancha oscura en cuello/axilas?",
                "opciones": ["Melanoma", "Acantosis nigricans", "Dermatitis", "Psoriasis"],
                "correcta": 1,
            },
            {
                "pregunta": "¿Qué porcentaje aprox. de adultos en México tiene resistencia a la insulina?",
                "opciones": ["5%", "10%", "30%", "60%"],
                "correcta": 2,
            },
        ],
    },
    {
        "id": 1,
        "titulo": "Entorno Urbano y Metabolismo",
        "emoji": "🏙️",
        "color": _ACCENT3,
        "contenido": [
            ("El entorno construido afecta tu salud", "El lugar donde vives influye directamente en tu metabolismo. Las ciudades diseñadas para el auto, sin banquetas ni áreas verdes, promueven el sedentarismo."),
            ("Áreas verdes y actividad física", "Según la OMS, cada habitante debería tener acceso a 9 m² de área verde. En municipios como Cuautlancingo este valor es muy bajo, reduciendo la actividad física espontánea."),
            ("Entorno alimentario riesgoso", "La alta densidad de tiendas de ultraprocesados en una colonia aumenta el consumo de azúcar y grasas trans, factores directos de resistencia a la insulina."),
            ("Índice IARRI-MX", "Este índice mide el riesgo metabólico de tu municipio combinando: acceso a áreas verdes, caminabilidad, equipamiento deportivo, entorno alimentario e índice de marginación."),
        ],
        "quiz": [
            {
                "pregunta": "¿Cuántos m² de área verde por habitante recomienda la OMS?",
                "opciones": ["3 m²", "6 m²", "9 m²", "15 m²"],
                "correcta": 2,
            },
            {
                "pregunta": "¿Qué mide el índice IARRI-MX?",
                "opciones": ["La calidad del aire", "El riesgo metabólico del entorno urbano", "La temperatura promedio", "El tráfico vehicular"],
                "correcta": 1,
            },
            {
                "pregunta": "¿Cuál de estos factores NO forma parte del IARRI-MX?",
                "opciones": ["Acceso a áreas verdes", "Equipamiento deportivo", "Número de hospitales", "Entorno alimentario"],
                "correcta": 2,
            },
        ],
    },
    {
        "id": 2,
        "titulo": "Arquitectura Preventiva",
        "emoji": "🏛️",
        "color": _LOW,
        "contenido": [
            ("¿Qué es la arquitectura preventiva?", "Es el diseño del espacio construido para promover hábitos saludables. Va desde el diseño de una vivienda hasta la planificación urbana de una ciudad."),
            ("Diseño que invita al movimiento", "Escaleras visibles y accesibles, pasillos amplios, patios activos y rutas peatonales seguras aumentan la actividad física sin que la persona lo note."),
            ("Ventilación y luz natural", "Espacios bien ventilados y con luz natural reducen el estrés y mejoran el sueño, dos factores clave en la prevención de resistencia a la insulina."),
            ("Microhuertos urbanos", "Los microhuertos en azoteas, patios o espacios comunitarios mejoran el acceso a vegetales frescos. Son una intervención de bajo costo y alto impacto metabólico."),
        ],
        "quiz": [
            {
                "pregunta": "¿Cuál es el objetivo principal de la arquitectura preventiva?",
                "opciones": ["Construir hospitales", "Diseñar espacios que promuevan hábitos saludables", "Reducir costos de construcción", "Aumentar la densidad de vivienda"],
                "correcta": 1,
            },
            {
                "pregunta": "¿Qué elemento arquitectónico simple aumenta la actividad física?",
                "opciones": ["Elevadores modernos", "Escaleras visibles y accesibles", "Estacionamientos amplios", "Ventanas pequeñas"],
                "correcta": 1,
            },
            {
                "pregunta": "¿Cómo ayuda la luz natural a prevenir la resistencia a la insulina?",
                "opciones": ["Quema calorías directamente", "Reduce el estrés y mejora el sueño", "Aumenta la producción de insulina", "No tiene relación"],
                "correcta": 1,
            },
        ],
    },
    {
        "id": 3,
        "titulo": "Alimentación Saludable",
        "emoji": "🥗",
        "color": _LOW,
        "tipo_quiz": "ordena_plato",
        "contenido": [
            ("¿Qué comemos y cómo nos afecta?", "La alimentación es uno de los factores más importantes en la resistencia a la insulina. Los alimentos ultraprocesados, ricos en azúcares simples y grasas trans, elevan rápidamente la glucosa en sangre."),
            ("El plato del buen comer", "Una alimentación saludable incluye: 50% verduras y frutas, 25% cereales integrales y 25% proteínas de calidad. Limitar azúcares, harinas refinadas y bebidas azucaradas es clave."),
            ("Índice glucémico", "Los alimentos con alto índice glucémico (pan blanco, refresco, papas fritas) elevan rápidamente el azúcar en sangre. Los de bajo índice (avena, legumbres, verduras) la elevan lentamente, protegiendo al páncreas."),
        ],
        "quiz": [
            {
                "tipo": "ordena_plato",
                "pregunta": "Clasifica cada alimento: ¿es SALUDABLE o NO SALUDABLE para prevenir resistencia a la insulina?",
                "alimentos": [
                    {"nombre": "Brócoli",      "saludable": True},
                    {"nombre": "Refresco",     "saludable": False},
                    {"nombre": "Avena",        "saludable": True},
                    {"nombre": "Papas fritas", "saludable": False},
                    {"nombre": "Manzana",      "saludable": True},
                    {"nombre": "Pan blanco",   "saludable": False},
                ],
            },
        ],
    },
    {
        "id": 4,
        "titulo": "Actividad Física Preventiva",
        "emoji": "🏃",
        "color": _ACCENT,
        "tipo_quiz": "verdadero_falso",
        "contenido": [
            ("¿Por qué moverse previene la resistencia?", "El músculo en movimiento consume glucosa sin necesitar insulina. 30 minutos de caminata diaria pueden reducir el riesgo de diabetes tipo 2 hasta en un 30%."),
            ("Tipos de ejercicio recomendados", "El ejercicio aeróbico (caminar, nadar, bicicleta) mejora la sensibilidad a la insulina. El ejercicio de fuerza aumenta la masa muscular que consume glucosa. La combinación es ideal."),
            ("Barreras arquitectónicas", "La falta de banquetas seguras, parques y ciclovías en colonias de Puebla reduce la actividad física involuntaria. El entorno construido puede ser aliado o enemigo de tu salud metabólica."),
        ],
        "quiz": [
            {"tipo": "verdadero_falso", "pregunta": "El músculo en movimiento puede consumir glucosa SIN necesitar insulina.",          "correcta": True},
            {"tipo": "verdadero_falso", "pregunta": "Solo el ejercicio intenso de más de 1 hora tiene beneficios metabólicos.",         "correcta": False},
            {"tipo": "verdadero_falso", "pregunta": "Caminar 30 minutos diarios puede reducir el riesgo de diabetes tipo 2.",           "correcta": True},
            {"tipo": "verdadero_falso", "pregunta": "El entorno urbano NO influye en cuánto ejercicio hace una persona.",               "correcta": False},
        ],
    },
    {
        "id": 5,
        "titulo": "Estres, Sueño y Metabolismo",
        "emoji": "😴",
        "color": _ACCENT3,
        "tipo_quiz": "sopa_letras",
        "contenido": [
            ("El estres eleva el azucar en sangre", "Cuando estas estresado, tu cuerpo libera cortisol. Esta hormona eleva la glucosa en sangre. Si el estres es cronico, el pancreas trabaja en exceso y puede desarrollarse resistencia a la insulina."),
            ("Dormir poco empeora la insulina", "Dormir menos de 6 horas aumenta la resistencia a la insulina en solo una semana. Durante el sueño, el cuerpo regula hormonas metabolicas clave como la leptina, grelina e insulina."),
            ("Diseño del espacio para reducir estres", "Espacios con luz natural, ventilacion cruzada y acceso a areas verdes reducen el cortisol. La arquitectura puede ser una intervencion directa contra el estres cronico."),
        ],
        "quiz": [
            {
                "tipo": "sopa_letras",
                "instruccion": "Escribe las palabras clave que aprendiste (una por cada pista):",
                "palabras": ["cortisol", "insulina", "glucosa", "sueño", "estres"],
                "pistas":   ["Hormona del estres", "Hormona del pancreas", "Azucar en sangre", "Descanso nocturno", "Tension cronica"],
            },
        ],
    },
    {
        "id": 6,
        "titulo": "Puebla y sus Datos IARRI",
        "emoji": "🗺️",
        "color": _MID,
        "tipo_quiz": "relaciona",
        "contenido": [
            ("Tres municipios, tres realidades", "San Andres Cholula, San Pablo Xochimehuacan y Cuautlancingo tienen indices IARRI muy diferentes. Sus condiciones de areas verdes, caminabilidad y entorno alimentario varian significativamente."),
            ("¿Que dicen los datos?", "San Andres Cholula tiene el mejor acceso a areas verdes (AV=0.80). Cuautlancingo tiene el mayor indice de entorno alimentario riesgoso (EAR=0.80), con alta densidad de tiendas de ultraprocesados."),
            ("Intervencion prioritaria", "Cuautlancingo requiere intervencion urgente: incrementar areas verdes, mejorar caminabilidad y fomentar equipamiento deportivo reduciria su IARRI de 0.78 a 0.64 (-18.2%)."),
        ],
        "quiz": [
            {
                "tipo": "relaciona",
                "pregunta": "Une cada municipio con su valor IARRI correcto:",
                "pares": [
                    {"municipio": "San Andres Cholula",      "iarri": "0.36", "nivel": "Bajo",  "col": _LOW},
                    {"municipio": "San Pablo Xochimehuacan", "iarri": "0.62", "nivel": "Medio", "col": _MID},
                    {"municipio": "Cuautlancingo",           "iarri": "0.78", "nivel": "Alto",  "col": _HIGH},
                ],
            },
        ],
    },
]

# ─── MICROCURSOS ──────────────────────────────────────────────────────────────
# Módulo de educación interactiva gamificada.
# Cada microcurso agrupa lecciones por tema, tiene XP, nivel y badge propio.
# Los IDs de lecciones referencian el campo "id" en LECCIONES.

MICROCURSOS = [
    {
        "id": "mc_ri",
        "titulo": "¿Qué es la Resistencia a la Insulina?",
        "descripcion": "Descubre cómo funciona la insulina, por qué el cuerpo puede volverse resistente y qué señales debes identificar.",
        "emoji": "🔬",
        "color": _ACCENT,
        "nivel_nombre": "Fundamentos",
        "xp_total": 150,
        "badge_emoji": "🧬",
        "badge_nombre": "Experto en Insulina",
        "lecciones_ids": [0],
        "evaluacion": {
            "titulo": "Evaluación: Resistencia a la Insulina",
            "descripcion": "Demuestra lo que aprendiste sobre la hormona que controla tu energía.",
            "preguntas": [
                {
                    "pregunta": "¿Cuál es la función principal de la insulina en el cuerpo?",
                    "opciones": [
                        "Descomponer las grasas en el hígado",
                        "Permitir que la glucosa entre a las células para producir energía",
                        "Regular la presión arterial",
                        "Producir glóbulos rojos",
                    ],
                    "correcta": 1,
                    "explicacion": "La insulina es la 'llave' que abre las células para que la glucosa pueda entrar y convertirse en energía.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Qué ocurre cuando las células se vuelven resistentes a la insulina?",
                    "opciones": [
                        "El páncreas produce menos insulina inmediatamente",
                        "El cuerpo quema más grasa automáticamente",
                        "El páncreas produce más insulina para compensar la resistencia",
                        "La glucosa se elimina por la orina sin consecuencias",
                    ],
                    "correcta": 2,
                    "explicacion": "El páncreas trabaja en exceso tratando de vencer la resistencia. Con el tiempo se agota, lo que puede llevar a diabetes tipo 2.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Cuál es la señal de alerta cutánea de la resistencia a la insulina?",
                    "opciones": [
                        "Manchas rojas en brazos",
                        "Piel escamosa en manos",
                        "Piel oscura en cuello o axilas (acantosis nigricans)",
                        "Uñas amarillas",
                    ],
                    "correcta": 2,
                    "explicacion": "La acantosis nigricans es una hiperpigmentación en pliegues de la piel directamente asociada a la hiperinsulinemia.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Qué porcentaje de adultos mexicanos tiene resistencia a la insulina?",
                    "opciones": ["5%", "15%", "30%", "50%"],
                    "correcta": 2,
                    "explicacion": "Más del 30% de la población adulta en México tiene algún grado de RI, muchas veces sin síntomas evidentes.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Cuál de estos NO es un síntoma típico de resistencia a la insulina?",
                    "opciones": [
                        "Cansancio intenso después de comer",
                        "Antojos frecuentes de azúcar",
                        "Dificultad para bajar de peso en el abdomen",
                        "Visión doble constante",
                    ],
                    "correcta": 3,
                    "explicacion": "La visión doble no es característica de la RI. Los síntomas clásicos son fatiga postprandial, antojos y adiposidad abdominal.",
                    "xp": 30,
                },
            ],
        },
    },
    {
        "id": "mc_entorno",
        "titulo": "Entorno Construido y Salud Metabólica",
        "descripcion": "Entiende cómo el diseño de tu ciudad, tus calles y tu barrio influyen directamente en el riesgo de resistencia a la insulina.",
        "emoji": "🏙️",
        "color": _ACCENT3,
        "nivel_nombre": "Territorio y Salud",
        "xp_total": 200,
        "badge_emoji": "🗺️",
        "badge_nombre": "Urbanista Metabólico",
        "lecciones_ids": [1, 6],
        "evaluacion": {
            "titulo": "Evaluación: Entorno y Metabolismo",
            "descripcion": "Ponemos a prueba tu comprensión del vínculo entre ciudad y salud.",
            "preguntas": [
                {
                    "pregunta": "¿Cuántos m² de área verde por habitante recomienda la OMS?",
                    "opciones": ["3 m²", "6 m²", "9 m²", "12 m²"],
                    "correcta": 2,
                    "explicacion": "La OMS establece 9 m² por habitante como estándar mínimo para promover la actividad física espontánea y el bienestar.",
                    "xp": 40,
                },
                {
                    "pregunta": "¿Cuál municipio de Puebla tiene el mayor entorno alimentario riesgoso (EAR)?",
                    "opciones": ["San Andrés Cholula", "San Pablo Xochimehuacan", "Cuautlancingo", "Puebla Centro"],
                    "correcta": 2,
                    "explicacion": "Cuautlancingo tiene EAR=0.80, con alta densidad de tiendas de ultraprocesados, lo que eleva el riesgo metabólico de sus habitantes.",
                    "xp": 40,
                },
                {
                    "pregunta": "¿Qué mide el Índice IARRI-MX?",
                    "opciones": [
                        "La calidad del aire urbano",
                        "El riesgo metabólico del entorno construido",
                        "La densidad de hospitales por municipio",
                        "El nivel socioeconómico promedio",
                    ],
                    "correcta": 1,
                    "explicacion": "IARRI-MX combina 5 variables: áreas verdes, caminabilidad, equipamiento deportivo, entorno alimentario e índice de marginación.",
                    "xp": 40,
                },
                {
                    "pregunta": "¿Cuál de estas variables del IARRI-MX es 'inversa' (mayor valor = menor riesgo)?",
                    "opciones": [
                        "EAR - Entorno Alimentario Riesgoso",
                        "IMP - Índice de Marginación",
                        "AV - Áreas Verdes",
                        "Ninguna de las anteriores",
                    ],
                    "correcta": 2,
                    "explicacion": "AV, IC y ED son inversas: más áreas verdes, caminabilidad y equipamiento deportivo = menor riesgo. EAR e IMP son directas.",
                    "xp": 40,
                },
                {
                    "pregunta": "¿Qué tipo de diseño urbano promueve el sedentarismo?",
                    "opciones": [
                        "Ciudades con ciclovías y banquetas amplias",
                        "Barrios con plazas y parques accesibles",
                        "Ciudades diseñadas para el automóvil, sin áreas peatonales",
                        "Colonias con equipamiento deportivo público",
                    ],
                    "correcta": 2,
                    "explicacion": "El urban sprawl centrado en el auto elimina la actividad física cotidiana (caminar al trabajo, a la tienda, etc.), aumentando el riesgo metabólico.",
                    "xp": 40,
                },
            ],
        },
    },
    {
        "id": "mc_prevencion",
        "titulo": "Prevención Activa",
        "descripcion": "Aprende estrategias prácticas de arquitectura preventiva, alimentación y actividad física para reducir tu riesgo metabólico.",
        "emoji": "🏃",
        "color": _LOW,
        "nivel_nombre": "Acción",
        "xp_total": 250,
        "badge_emoji": "🏅",
        "badge_nombre": "Agente Preventivo",
        "lecciones_ids": [2, 3, 4],
        "evaluacion": {
            "titulo": "Evaluación: Prevención Activa",
            "descripcion": "Demuestra que puedes aplicar lo aprendido para mejorar tu entorno y hábitos.",
            "preguntas": [
                {
                    "pregunta": "¿Cuántos minutos de caminata diaria reducen hasta 30% el riesgo de diabetes tipo 2?",
                    "opciones": ["10 minutos", "20 minutos", "30 minutos", "60 minutos"],
                    "correcta": 2,
                    "explicacion": "30 minutos de caminata diaria a ritmo moderado mejoran significativamente la sensibilidad a la insulina según múltiples estudios.",
                    "xp": 50,
                },
                {
                    "pregunta": "¿Cuál es la principal razón por la que el músculo consume glucosa sin insulina?",
                    "opciones": [
                        "El músculo produce su propia insulina local",
                        "Durante el ejercicio, las células musculares activan transportadores GLUT4 independientes de insulina",
                        "El glucógeno muscular reemplaza a la insulina",
                        "La adrenalina actúa como insulina durante el ejercicio",
                    ],
                    "correcta": 1,
                    "explicacion": "Durante el ejercicio, la contracción muscular activa transportadores GLUT4 que permiten la entrada de glucosa SIN necesitar insulina. Por eso el ejercicio es tan poderoso.",
                    "xp": 50,
                },
                {
                    "pregunta": "¿Qué alimento tiene bajo índice glucémico y protege al páncreas?",
                    "opciones": ["Pan blanco", "Refresco de cola", "Avena integral", "Papas fritas"],
                    "correcta": 2,
                    "explicacion": "La avena tiene bajo índice glucémico: libera glucosa lentamente, evitando picos de insulina que con el tiempo generan resistencia.",
                    "xp": 50,
                },
                {
                    "pregunta": "¿Qué característica arquitectónica simple aumenta la actividad física sin esfuerzo consciente?",
                    "opciones": [
                        "Elevadores rápidos y modernos",
                        "Escaleras visibles, amplias y atractivas",
                        "Estacionamientos grandes cerca de la entrada",
                        "Pasillos cortos para minimizar recorridos",
                    ],
                    "correcta": 1,
                    "explicacion": "Las escaleras visibles y bien diseñadas aumentan hasta 30% su uso frente a los elevadores, sumando actividad física cotidiana sin que la persona lo 'decida'.",
                    "xp": 50,
                },
                {
                    "pregunta": "¿Qué porcentaje del plato debe corresponder a verduras y frutas según el 'plato del buen comer'?",
                    "opciones": ["25%", "35%", "50%", "75%"],
                    "correcta": 2,
                    "explicacion": "El plato saludable se divide en: 50% verduras y frutas, 25% cereales integrales y 25% proteínas de calidad.",
                    "xp": 50,
                },
            ],
        },
    },
    {
        "id": "mc_estres_sueno",
        "titulo": "Estrés, Sueño y Metabolismo",
        "descripcion": "Explora el impacto del estrés crónico y la falta de sueño en la resistencia a la insulina, y cómo el diseño del espacio puede ayudarte.",
        "emoji": "😴",
        "color": _ACCENT3,
        "nivel_nombre": "Factores Invisibles",
        "xp_total": 150,
        "badge_emoji": "🌙",
        "badge_nombre": "Maestro del Descanso",
        "lecciones_ids": [5],
        "evaluacion": {
            "titulo": "Evaluación: Estrés y Sueño",
            "descripcion": "Comprueba tu dominio sobre los factores metabólicos que no siempre se ven.",
            "preguntas": [
                {
                    "pregunta": "¿Qué hormona del estrés eleva la glucosa en sangre?",
                    "opciones": ["Serotonina", "Cortisol", "Melatonina", "Leptina"],
                    "correcta": 1,
                    "explicacion": "El cortisol es la hormona del estrés. Cuando se libera crónicamente, eleva la glucosa y obliga al páncreas a producir más insulina, generando resistencia.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Cuántas horas de sueño mínimo se necesitan para no aumentar la resistencia a la insulina?",
                    "opciones": ["4 horas", "6 horas", "8 horas", "10 horas"],
                    "correcta": 1,
                    "explicacion": "Dormir menos de 6 horas por noche aumenta la resistencia a la insulina en tan solo una semana, según estudios clínicos controlados.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Cuál elemento del diseño arquitectónico ayuda a reducir el cortisol?",
                    "opciones": [
                        "Techos altos sin ventanas",
                        "Pasillos angostos y oscuros",
                        "Luz natural, ventilación cruzada y acceso a áreas verdes",
                        "Aislamiento total del exterior",
                    ],
                    "correcta": 2,
                    "explicacion": "Estudios de neuroarquitectura demuestran que la luz natural, las vistas a vegetación y la ventilación reducen los niveles de cortisol y mejoran el sueño.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Qué hormona regula el apetito y se desregula con la falta de sueño?",
                    "opciones": ["Insulina", "Adrenalina", "Grelina y leptina", "Tiroxina"],
                    "correcta": 2,
                    "explicacion": "La grelina (hormona del hambre) aumenta y la leptina (saciedad) disminuye cuando dormimos mal, generando mayor consumo calórico al día siguiente.",
                    "xp": 30,
                },
                {
                    "pregunta": "¿Qué relación tiene el estrés crónico con la diabetes tipo 2?",
                    "opciones": [
                        "No tiene relación directa",
                        "Reduce la producción de insulina temporalmente",
                        "El cortisol crónico genera resistencia a la insulina que puede derivar en diabetes tipo 2",
                        "Solo afecta a personas con predisposición genética",
                    ],
                    "correcta": 2,
                    "explicacion": "El estrés crónico mantiene el cortisol elevado de forma permanente, lo que genera resistencia a la insulina sostenida. Es un factor de riesgo independiente para diabetes tipo 2.",
                    "xp": 30,
                },
            ],
        },
    },
]

# ─── NIVELES DE XP ────────────────────────────────────────────────────────────
# Sistema de progresión del módulo educativo
NIVELES_XP = [
    {"nivel": 1, "titulo": "Aprendiz",          "xp_min": 0,   "emoji": "🌱"},
    {"nivel": 2, "titulo": "Explorador",         "xp_min": 100, "emoji": "🔍"},
    {"nivel": 3, "titulo": "Investigador",       "xp_min": 250, "emoji": "🔬"},
    {"nivel": 4, "titulo": "Analista Urbano",    "xp_min": 450, "emoji": "🏙️"},
    {"nivel": 5, "titulo": "Experto IARRI",      "xp_min": 700, "emoji": "⭐"},
]

# ─── RETOS SEMANALES ──────────────────────────────────────────────────────────
# Cada reto tiene:
#   id          str   — clave única en state (reto_{id}_completado, reto_{id}_progreso)
#   categoria   str   — "movimiento" | "diseño" | "nutricion" | "educacion" | "territorio"
#   emoji       str
#   color       str   — hex
#   titulo      str
#   descripcion str   — qué hacer exactamente
#   instruccion str   — texto de acción en la app
#   meta        int   — cantidad objetivo (pasos, días, lecciones, etc.)
#   unidad      str   — "pasos" | "días" | "lecciones" | "min" | "acciones"
#   xp          int   — XP al completar
#   badge_id    str | None  — badge que desbloquea al completar (o None)
#   semana      int   — semana del ciclo (1-4, rotación mensual)

RETOS_SEMANALES = [
    # ── Semana 1 — Movimiento ──────────────────────────────
    {
        "id":          "camina_colonia",
        "categoria":   "movimiento",
        "emoji":       "🚶",
        "color":       "#0ea5e9",
        "titulo":      "Camina 5 000 pasos en tu colonia",
        "descripcion": "Sal a caminar por tu colonia durante al menos 40 minutos. Observa las banquetas, áreas verdes y equipamiento deportivo cerca de tu casa.",
        "instruccion": "Registra cada día que completaste tu caminata",
        "meta":        5,
        "unidad":      "días",
        "xp":          80,
        "badge_id":    "arquitecto_bioactivo",
        "semana":      1,
        "pasos": [
            "Sal a caminar al menos 40 minutos",
            "Recorre un área verde o parque de tu colonia",
            "Identifica una banqueta en mal estado y fotográfiala",
            "Nota cuántas tiendas de ultraprocesados hay en tu ruta",
            "Comparte el recorrido con alguien de tu familia",
        ],
    },
    {
        "id":          "desayuno_real",
        "categoria":   "nutricion",
        "emoji":       "🥗",
        "color":       "#22c55e",
        "titulo":      "3 días sin ultraprocesados al desayuno",
        "descripcion": "Reemplaza los cereales azucarados, pan dulce o galletas por frutas, avena o huevo durante 3 mañanas consecutivas.",
        "instruccion": "Marca cada mañana que lo lograste",
        "meta":        3,
        "unidad":      "días",
        "xp":          60,
        "badge_id":    None,
        "semana":      1,
        "pasos": [
            "Prepara avena con fruta el lunes",
            "Huevo con verduras el miércoles",
            "Fruta fresca con nueces el viernes",
        ],
    },

    # ── Semana 2 — Diseño de espacio ──────────────────────
    {
        "id":          "redisena_estudio",
        "categoria":   "diseño",
        "emoji":       "🏛️",
        "color":       "#8b5cf6",
        "titulo":      "Rediseña tu espacio de estudio",
        "descripcion": "Aplica 3 principios de arquitectura preventiva en tu área de trabajo o estudio: luz natural, ventilación y una planta o elemento verde.",
        "instruccion": "Completa cada mejora y márcala",
        "meta":        3,
        "unidad":      "acciones",
        "xp":          100,
        "badge_id":    "disenador_preventivo",
        "semana":      2,
        "pasos": [
            "Mueve tu escritorio cerca de una ventana con luz natural",
            "Asegura ventilación cruzada: abre ventanas opuestas 10 min al día",
            "Agrega una planta pequeña (suculenta, pothos o albahaca) a tu espacio",
        ],
    },
    {
        "id":          "mapea_colonia",
        "categoria":   "territorio",
        "emoji":       "🗺️",
        "color":       "#f59e0b",
        "titulo":      "Mapea los riesgos de tu colonia",
        "descripcion": "Usa el módulo de Mapa para revisar el perfil territorial de tu colonia. Identifica las 2 variables con peor puntaje y piensa en una solución concreta.",
        "instruccion": "Completa los pasos de análisis",
        "meta":        3,
        "unidad":      "acciones",
        "xp":          70,
        "badge_id":    None,
        "semana":      2,
        "pasos": [
            "Abre el módulo Mapa y selecciona tu colonia",
            "Identifica las 2 variables con ✗ Crítico",
            "Escribe en papel una acción concreta para mejorar cada variable",
        ],
    },

    # ── Semana 3 — Educación activa ───────────────────────
    {
        "id":          "completa_microcurso",
        "categoria":   "educacion",
        "emoji":       "🔬",
        "color":       "#0ea5e9",
        "titulo":      "Completa un microcurso completo",
        "descripcion": "Termina todas las lecciones y la evaluación de cualquier microcurso en el módulo Educación.",
        "instruccion": "Completa lecciones y evaluación",
        "meta":        1,
        "unidad":      "microcurso",
        "xp":          120,
        "badge_id":    "agente_metabolico",
        "semana":      3,
        "pasos": [
            "Elige un microcurso en el módulo Aprender",
            "Completa todas sus lecciones",
            "Aprueba la evaluación final",
        ],
    },
    {
        "id":          "calcula_iarri",
        "categoria":   "territorio",
        "emoji":       "📊",
        "color":       "#f97316",
        "titulo":      "Calcula tu IARRI personal",
        "descripcion": "Usa la Calculadora IARRI con tus valores reales y guarda el resultado. Compara con el promedio de tu municipio.",
        "instruccion": "Guarda un cálculo en la Calculadora",
        "meta":        1,
        "unidad":      "cálculo",
        "xp":          50,
        "badge_id":    None,
        "semana":      3,
        "pasos": [
            "Abre la Calculadora IARRI",
            "Ajusta los sliders con tus valores reales",
            "Guarda el resultado con el botón 'Guardar'",
        ],
    },

    # ── Semana 4 — Reto integral ──────────────────────────
    {
        "id":          "semana_activa",
        "categoria":   "movimiento",
        "emoji":       "⚡",
        "color":       "#ef4444",
        "titulo":      "Semana activa — 7 días de movimiento",
        "descripcion": "El reto más completo: combina caminata diaria, un día de ejercicio de fuerza y tres días sin ultraprocesados en una sola semana.",
        "instruccion": "Registra cada día que cumpliste al menos uno de los criterios",
        "meta":        7,
        "unidad":      "días",
        "xp":          200,
        "badge_id":    "investigador_iarri",
        "semana":      4,
        "pasos": [
            "Lunes: caminata 40 min",
            "Martes: desayuno sin ultraprocesados",
            "Miércoles: ejercicio de fuerza (sentadillas, lagartijas) 20 min",
            "Jueves: caminata 40 min",
            "Viernes: desayuno sin ultraprocesados",
            "Sábado: recorre un parque o área verde con familia",
            "Domingo: planea la semana siguiente con los módulos de la app",
        ],
    },
]

# ─── INSIGNIAS GAMIFICACIÓN ───────────────────────────────────────────────────
# Sistema completo de insignias con condición de desbloqueo evaluable en runtime.
#
# condition_key  str  — qué clave del state se evalúa
# condition_type str  — "bool" | "gte" | "any_mc" | "reto"
#   "bool"    → state[condition_key] == True
#   "gte"     → state[condition_key] >= condition_value
#   "any_mc"  → any(state[f"mc_{mc_id}_evaluacion_completada"] for mc_id in condition_value)
#   "reto"    → state[f"reto_{condition_key}_completado"] == True

GAMIFICACION_BADGES = [
    {
        "id":          "arquitecto_bioactivo",
        "emoji":       "🏛️",
        "nombre":      "Arquitecto Bioactivo",
        "descripcion": "Completaste el reto de caminata semanal. Conocés tu colonia y la recorrés activamente.",
        "color":       "#0ea5e9",
        "condition_type":  "reto",
        "condition_key":   "camina_colonia",
        "condition_value": None,
        "xp_bonus":    50,
        "categoria":   "movimiento",
    },
    {
        "id":          "disenador_preventivo",
        "emoji":       "🌱",
        "nombre":      "Diseñador Preventivo",
        "descripcion": "Aplicaste arquitectura preventiva en tu espacio. Tu entorno ahora trabaja a favor de tu salud.",
        "color":       "#22c55e",
        "condition_type":  "reto",
        "condition_key":   "redisena_estudio",
        "condition_value": None,
        "xp_bonus":    60,
        "categoria":   "diseño",
    },
    {
        "id":          "agente_metabolico",
        "emoji":       "⚡",
        "nombre":      "Agente Metabólico",
        "descripcion": "Completaste un microcurso completo. Tenés el conocimiento para actuar sobre tu entorno metabólico.",
        "color":       "#8b5cf6",
        "condition_type":  "reto",
        "condition_key":   "completa_microcurso",
        "condition_value": None,
        "xp_bonus":    80,
        "categoria":   "educacion",
    },
    {
        "id":          "analista_territorial",
        "emoji":       "📊",
        "nombre":      "Analista Territorial",
        "descripcion": "Guardaste tu cálculo IARRI personal. Ya mediste tu riesgo metabólico con datos reales.",
        "color":       "#f97316",
        "condition_type":  "bool",
        "condition_key":   "iarri_guardado",
        "condition_value": None,
        "xp_bonus":    40,
        "categoria":   "territorio",
    },
    {
        "id":          "mapeador_urbano",
        "emoji":       "🗺️",
        "nombre":      "Mapeador Urbano",
        "descripcion": "Completaste el reto territorial y conocés los riesgos de tu colonia.",
        "color":       "#f59e0b",
        "condition_type":  "reto",
        "condition_key":   "mapea_colonia",
        "condition_value": None,
        "xp_bonus":    40,
        "categoria":   "territorio",
    },
    {
        "id":          "investigador_iarri",
        "emoji":       "🔬",
        "nombre":      "Investigador IARRI",
        "descripcion": "Completaste la Semana Activa de 7 días. Sos un referente de salud metabólica preventiva.",
        "color":       "#ef4444",
        "condition_type":  "reto",
        "condition_key":   "semana_activa",
        "condition_value": None,
        "xp_bonus":    120,
        "categoria":   "movimiento",
    },
    {
        "id":          "experto_educacion",
        "emoji":       "🎓",
        "nombre":      "Experto en Educación",
        "descripcion": "Completaste todos los microcursos del módulo Educación.",
        "color":       "#0ea5e9",
        "condition_type":  "gte",
        "condition_key":   "microcursos_completados",
        "condition_value": 4,
        "xp_bonus":    200,
        "categoria":   "educacion",
    },
]
