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
        # Colonias principales
        "colonias": [
            {"nombre": "San Andrés Cholula Centro",        "iarri": 0.28, "av": 0.85, "ic": 0.70},
            {"nombre": "Ex-Hacienda Zavaleta",             "iarri": 0.34, "av": 0.65, "ic": 0.60},
            {"nombre": "La Carcaña",                       "iarri": 0.42, "av": 0.50, "ic": 0.45},
            {"nombre": "San Bernardino Tlaxcalancingo",    "iarri": 0.38, "av": 0.60, "ic": 0.55},
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
            {"nombre": "Xochimehuacan Norte", "iarri": 0.58, "av": 0.30, "ic": 0.35},
            {"nombre": "Xochimehuacan Sur",   "iarri": 0.64, "av": 0.25, "ic": 0.30},
            {"nombre": "El Barrio Nuevo",     "iarri": 0.55, "av": 0.35, "ic": 0.38},
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
            {"nombre": "Cuautlancingo Centro",  "iarri": 0.76, "av": 0.15, "ic": 0.22},
            {"nombre": "Lomas de Cuautlancingo","iarri": 0.71, "av": 0.20, "ic": 0.25},
            {"nombre": "San Pedro Zacachimalpa","iarri": 0.80, "av": 0.10, "ic": 0.18},
            {"nombre": "Parques Industriales",  "iarri": 0.74, "av": 0.18, "ic": 0.20},
        ],
    },
}

# ─── ENCUESTA ─────────────────────────────────────────────────────────────────
ENCUESTA = [
    {
        "variable": "AV",  # acceso a areas verdes
        "pregunta": "¿Como consideras tu estilo de vida?",
        "opciones": [
            {"texto": "Activo con servicios completos y lugares tranquilos para caminar.", "valor": 0.8},
            {"texto": "Inactivo con servicios y problemas de salud(actualmente) sin poder salir a un lugar a caminar.", "valor": 0.2},
            {"texto": "Prefiero no responder la pregunta", "valor": 0.5},
        ],
    },
    {
        "variable": "IC",  # indice de caminabilidad
        "pregunta": "¿Cuantas horas pasas al dia sentado?",
        "opciones": [
            {"texto": "Menos de dos horas al dia",               "valor": 0.8},
            {"texto": "Mas de seis horas al dia",                "valor": 0.2},
            {"texto": "Menos de una hora o quince minutos al dia","valor": 0.9},
        ],
    },
    {
        "variable": "ED",  # entrenamiento deportivo
        "pregunta": "¿Practica algun deporte, y soporta los sintomas del ritmo cardiaco elevado  que le produce?",
        "opciones": [
            {"texto": "Si entreno de forma constante.", "valor": 0.85},
            {"texto": "No practico ningun deporte.",    "valor": 0.1},
            {"texto": "Puedo hacerlo media hora y ya.", "valor": 0.4},
        ],
    },
    {
        "variable": "EAR",  # entorno alimentario riesgoso
        "pregunta": "Con que frecuencia consume azucar como productos empaquetados.",
        "opciones": [
            {"texto": "Lo hago al menos una vez a la semana.", "valor": 0.7},
            {"texto": "No consumo ese tipo de alimentos.",     "valor": 0.1},
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

# ─── RECOMENDACIONES ──────────────────────────────────────────────────────────
RECOMENDACIONES = [
    {"icon": "🌳", "color": "#22c55e", "titulo": "Incrementar Áreas Verdes",  "desc": "Corredores verdes y microparques. AV: 0.30 → 0.55",          "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🚶", "color": "#0ea5e9", "titulo": "Ruta Diaria de 15 min",     "desc": "Banquetas accesibles e iluminación. IC: 0.20 → 0.45",         "impacto": "↓ IARRI −0.0625 (−8%)"},
    {"icon": "⚽", "color": "#8b5cf6", "titulo": "Espacios Deportivos",        "desc": "2 unidades barriales abiertas. ED: 0.10 → 0.30",              "impacto": "↓ IARRI −0.03 (−3.8%)"},
    {"icon": "🏗️","color": "#f97316", "titulo": "Regulación Alimentaria",     "desc": "Reducir ultraprocesados. EAR: 0.80 → 0.60",                   "impacto": "↓ IARRI −0.05 (−6.4%)"},
    {"icon": "🪟", "color": "#f59e0b", "titulo": "Diseño Arquitectónico",      "desc": "Ventilación cruzada y acceso escaleras",                      "impacto": "Compensación: +18%"},
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
