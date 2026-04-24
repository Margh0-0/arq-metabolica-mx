"""
ui/theme.py — Paleta de colores y temas visuales de la app.

Contiene COLORES (constantes individuales), PALETAS (variantes de tema)
y el helper get_paleta().
"""

import flet as ft

# ═══════════════════════════════════════════════════════════
#  COLORES — Tema claro, amigable, sin fatiga visual
# ═══════════════════════════════════════════════════════════
COLORES = {
    "BG":      "#f8fafb",   # Fondo principal blanco cálido
    "SURFACE": "#ffffff",   # Superficies blancas puras
    "CARD":    "#ffffff",   # Tarjetas blancas con sombra suave
    "BORDER":  "#e2e8f0",   # Bordes grises claros
    "ACCENT":  "#0ea5e9",   # Azul cielo — acción principal
    "ACCENT2": "#f97316",   # Naranja suave — secundario
    "ACCENT3": "#8b5cf6",   # Violeta suave — gamificación
    "LOW":     "#22c55e",   # Verde — bajo riesgo
    "MID":     "#f59e0b",   # Ámbar — riesgo medio
    "HIGH":    "#ef4444",   # Rojo — alto riesgo
    "TEXT":    "#1e293b",   # Texto oscuro principal
    "MUTED":   "#64748b",   # Texto secundario gris medio
    "WHITE":   "#ffffff",
}

# Atajos de módulo (compat con code que importa directamente)
BG      = COLORES["BG"]
SURFACE = COLORES["SURFACE"]
CARD    = COLORES["CARD"]
BORDER  = COLORES["BORDER"]
ACCENT  = COLORES["ACCENT"]
ACCENT2 = COLORES["ACCENT2"]
ACCENT3 = COLORES["ACCENT3"]
LOW     = COLORES["LOW"]
MID     = COLORES["MID"]
HIGH    = COLORES["HIGH"]
TEXT    = COLORES["TEXT"]
MUTED   = COLORES["MUTED"]
WHITE   = COLORES["WHITE"]

# ═══════════════════════════════════════════════════════════
#  PALETAS — Variantes de tema visual seleccionables
# ═══════════════════════════════════════════════════════════
PALETAS = {
    "Claro (actual)": {
        "BG": "#f8fafb", "SURFACE": "#ffffff", "CARD": "#ffffff",
        "BORDER": "#e2e8f0", "TEXT": "#1e293b", "MUTED": "#64748b",
        "ACCENT": "#0ea5e9", "modo": ft.ThemeMode.LIGHT,
    },
    "Oscuro (original)": {
        "BG": "#0a0e1a", "SURFACE": "#111827", "CARD": "#161f35",
        "BORDER": "#1e2d4a", "TEXT": "#e8edf5", "MUTED": "#6b7fa3",
        "ACCENT": "#00e5c8", "modo": ft.ThemeMode.DARK,
    },
    "Verde salud": {
        "BG": "#f0fdf4", "SURFACE": "#ffffff", "CARD": "#ffffff",
        "BORDER": "#bbf7d0", "TEXT": "#14532d", "MUTED": "#4b7a5c",
        "ACCENT": "#16a34a", "modo": ft.ThemeMode.LIGHT,
    },
}

_DEFAULT_PALETA = "Claro (actual)"


def get_paleta(nombre: str) -> dict:
    """Devuelve la paleta por nombre; cae en la default si no existe."""
    return PALETAS.get(nombre, PALETAS[_DEFAULT_PALETA])
