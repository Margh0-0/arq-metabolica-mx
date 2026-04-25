"""
core/iarm.py — Lógica científica IARM (pura, sin UI)

Índice Arquitectónico de Riesgo Metabólico.
Mide el riesgo del ENTORNO CONSTRUIDO a nivel territorial.

Todos los factores son de riesgo DIRECTO: mayor valor = mayor riesgo ambiental.
Sin dependencias de Flet ni de ninguna librería UI.
"""

# ─── FACTORES DEL MODELO ──────────────────────────────────────────────────────
# Los 4 factores tienen peso igual (promedio simple).
# Todos directos: 0 = entorno protector, 1 = entorno de máximo riesgo.
IARM_WEIGHTS = {
    "ST":  0.25,   # Sedentarismo Territorial
    "BAV": 0.25,   # Baja Área Verde
    "DEN": 0.25,   # Alta Densidad Poblacional
    "BEA": 0.25,   # Bajo Equipamiento Activo
}

# ─── RANGOS DE RIESGO ────────────────────────────────────────────────────────
_LOW  = "#22c55e"   # Verde  — bajo riesgo ambiental
_MID  = "#f59e0b"   # Ámbar  — riesgo medio
_HIGH = "#ef4444"   # Rojo   — alto riesgo


def calc_iarm(ST: float, BAV: float, DEN: float, BEA: float) -> float:
    """
    Calcula el Índice IARM a partir de los cuatro factores territoriales.

    Fórmula:
        IARM = (ST + BAV + DEN + BEA) / 4

    Todos los factores son directos (mayor valor = mayor riesgo).
    Retorna float en [0, 1].
    """
    return (
        IARM_WEIGHTS["ST"]  * ST  +
        IARM_WEIGHTS["BAV"] * BAV +
        IARM_WEIGHTS["DEN"] * DEN +
        IARM_WEIGHTS["BEA"] * BEA
    )


def nivel_riesgo_iarm(iarm: float) -> tuple[str, str]:
    """
    Clasifica el valor IARM en nivel de riesgo ambiental.

    Retorna (label, color_hex):
    - [0.00, 0.33) → ("Bajo riesgo ambiental",  "#22c55e")
    - [0.33, 0.66) → ("Riesgo medio",            "#f59e0b")
    - [0.66, 1.00] → ("Alto riesgo",             "#ef4444")
    """
    if iarm < 0.33:
        return "Bajo riesgo ambiental", _LOW
    if iarm < 0.66:
        return "Riesgo medio", _MID
    return "Alto riesgo", _HIGH


def narrativa_combinada(nivel_iarri: str, nivel_iarm: str) -> dict:
    """
    Genera la narrativa combinada IARRI (individual) + IARM (territorial).

    Retorna dict con:
      - titulo   str  — encabezado de la narrativa
      - mensaje  str  — descripción de la situación combinada
      - accion   str  — recomendación de acción concreta
      - color    str  — color hex del nivel de alerta combinado
      - icono    str  — emoji representativo
    """
    par = (nivel_iarri, nivel_iarm)

    # ── Combinaciones críticas ────────────────────────────────────────────────
    if par == ("Alto", "Alto riesgo"):
        return {
            "titulo":  "⚠️ Situación crítica: doble riesgo",
            "mensaje": "Tu riesgo individual es alto Y tu entorno construido "
                       "presenta alto riesgo ambiental. La combinación amplifica "
                       "significativamente la probabilidad de resistencia a la insulina.",
            "accion":  "Intervención urgente: considera cambiar hábitos Y presiona "
                       "por mejoras urbanas en tu colonia (áreas verdes, equipamiento activo).",
            "color":   _HIGH,
            "icono":   "🚨",
        }
    if par == ("Alto", "Riesgo medio"):
        return {
            "titulo":  "⚠️ Riesgo individual alto en entorno limitante",
            "mensaje": "Tu riesgo personal es alto. Tu entorno tiene deficiencias "
                       "moderadas que dificultan cambiar hábitos por falta de "
                       "infraestructura adecuada.",
            "accion":  "Prioriza cambios personales mientras gestionas mejoras "
                       "en el entorno inmediato (buscar parques, rutas peatonales).",
            "color":   _HIGH,
            "icono":   "⚠️",
        }
    if par == ("Alto", "Bajo riesgo ambiental"):
        return {
            "titulo":  "Riesgo individual alto, entorno favorable",
            "mensaje": "Tu entorno tiene buena infraestructura activa, pero tu "
                       "riesgo individual es alto. El entorno no está siendo "
                       "aprovechado suficientemente.",
            "accion":  "Tu entorno es un aliado: úsalo. Incrementa uso de áreas "
                       "verdes, rutas peatonales y equipamiento deportivo cercano.",
            "color":   _MID,
            "icono":   "🔶",
        }
    if par == ("Medio", "Alto riesgo"):
        return {
            "titulo":  "Entorno de alto riesgo con vulnerabilidad individual media",
            "mensaje": "Tu entorno construido presenta alto riesgo ambiental, lo "
                       "que puede empeorar progresivamente tu situación metabólica "
                       "individual si no se interviene.",
            "accion":  "El entorno es tu mayor obstáculo ahora. Busca activamente "
                       "espacios activos alternativos y reduce exposición a "
                       "ultraprocesados en tu zona.",
            "color":   _MID,
            "icono":   "🔶",
        }
    if par == ("Medio", "Riesgo medio"):
        return {
            "titulo":  "Riesgo moderado en ambos frentes",
            "mensaje": "Tanto tu situación individual como tu entorno muestran "
                       "riesgo moderado. Hay margen de mejora en los dos niveles "
                       "antes de que escale.",
            "accion":  "Momento ideal para actuar: pequeñas mejoras personales "
                       "y presión por mejoras urbanas pueden reducir el riesgo "
                       "significativamente.",
            "color":   _MID,
            "icono":   "🟡",
        }
    if par == ("Medio", "Bajo riesgo ambiental"):
        return {
            "titulo":  "Buen entorno, riesgo individual a trabajar",
            "mensaje": "Tu entorno es favorable. El riesgo proviene principalmente "
                       "de factores individuales que podés mejorar con el apoyo "
                       "de la infraestructura disponible.",
            "accion":  "Aprovechá tu entorno: establecé rutinas de actividad en "
                       "los espacios disponibles cerca de vos.",
            "color":   _LOW,
            "icono":   "🟢",
        }
    if par == ("Bajo", "Alto riesgo"):
        return {
            "titulo":  "Entorno de alto riesgo, bajo riesgo individual",
            "mensaje": "Actualmente tu riesgo individual es bajo, pero vivís en "
                       "un entorno de alto riesgo ambiental. Sin cambios, tu "
                       "situación puede deteriorarse con el tiempo.",
            "accion":  "Mantené tus hábitos actuales y participá en iniciativas "
                       "de mejora urbana de tu colonia. La prevención comunitaria "
                       "es clave aquí.",
            "color":   _MID,
            "icono":   "🔔",
        }
    if par == ("Bajo", "Riesgo medio"):
        return {
            "titulo":  "Situación favorable con entorno a mejorar",
            "mensaje": "Tu riesgo individual es bajo y tu entorno tiene áreas de "
                       "mejora moderadas. Estás en buena posición para mantener "
                       "y mejorar.",
            "accion":  "Seguí con tus hábitos actuales. Explorá opciones para "
                       "mejorar el entorno con tu comunidad.",
            "color":   _LOW,
            "icono":   "✅",
        }
    # Bajo + Bajo riesgo ambiental (mejor caso)
    return {
        "titulo":  "✅ Situación óptima",
        "mensaje": "Tu riesgo individual es bajo y tu entorno construido es "
                   "favorable. Estás en la mejor posición posible para mantener "
                   "una salud metabólica óptima.",
        "accion":  "Mantené tus hábitos y aprovechá tu entorno. Compartí este "
                   "resultado como referencia positiva en tu comunidad.",
        "color":   _LOW,
        "icono":   "🏆",
    }
