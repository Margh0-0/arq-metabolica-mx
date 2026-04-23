"""
core/iarri.py — Lógica científica IARRI-MX (pura, sin UI)

Índice Arquitectónico de Riesgo de Resistencia a la Insulina.
Sin dependencias de Flet ni de ninguna librería UI.
"""

import random
from math import exp

# ─── PESOS DEL MODELO ────────────────────────────────────────────────────────
# α + β + γ + δ + ε = 1.00  (PDF pág. 23)
WEIGHTS = {
    "AV":  0.20,  # Áreas Verdes / Acceso a espacios activos
    "IC":  0.25,  # Índice de Caminabilidad
    "ED":  0.15,  # Equipamiento Deportivo
    "EAR": 0.25,  # Entorno Alimentario Riesgoso
    "IMP": 0.15,  # Índice de Marginación / Impacto
}

# ─── RANGOS DE RIESGO ────────────────────────────────────────────────────────
# Colores como strings hexadecimales (independientes de UI)
_LOW  = "#22c55e"   # Verde  — riesgo bajo
_MID  = "#f59e0b"   # Ámbar  — riesgo medio
_HIGH = "#ef4444"   # Rojo   — riesgo alto


def calc_iarri(AV: float, IC: float, ED: float, EAR: float, IMP: float) -> float:
    """
    Calcula el Índice IARRI-MX a partir de las cinco variables.

    Variables de protección (inv=True): AV, IC, ED — mayor valor = MENOR riesgo
    Variables de riesgo (inv=False):    EAR, IMP   — mayor valor = MAYOR riesgo

    Retorna float en [0, 1].
    """
    return (
        WEIGHTS["AV"]  * (1 - AV) +
        WEIGHTS["IC"]  * (1 - IC) +
        WEIGHTS["ED"]  * (1 - ED) +
        WEIGHTS["EAR"] * EAR +
        WEIGHTS["IMP"] * IMP
    )


def prob_ri(v: float) -> float:
    """
    Probabilidad de Resistencia a la Insulina — función sigmoide logística.

    Fórmula: 1 / (1 + exp(-10 * (v - 0.5)))
    - En v=0.5 retorna exactamente 0.5
    - En v=0.0 retorna ≈ 0.0067 (< 0.007)
    - En v=1.0 retorna ≈ 0.9933 (> 0.993)

    NOTA: main.py usa una versión LINEAL incorrecta: min(1.0, 0.10 + 0.50*v)
    Esta es la versión CORRECTA (ver iarri.py standalone, autor confirmado).
    """
    return 1.0 / (1.0 + exp(-10.0 * (v - 0.5)))


def nivel_riesgo(iarri: float) -> tuple[str, str]:
    """
    Clasifica el valor IARRI en nivel de riesgo.

    Retorna (label, color_hex):
    - (0.00, 0.33) → ("Bajo",  "#22c55e")
    - (0.33, 0.66) → ("Medio", "#f59e0b")
    - (0.66, 1.00) → ("Alto",  "#ef4444")
    """
    if iarri < 0.33:
        return "Bajo", _LOW
    if iarri < 0.66:
        return "Medio", _MID
    return "Alto", _HIGH


def monte_carlo(
    variables: dict,
    n: int = 1000,
    sigma: float = 0.12,
) -> tuple:
    """
    Simulación Monte Carlo del IARRI perturbando las variables con ruido gaussiano.

    Args:
        variables: dict con claves AV, IC, ED, EAR, IMP (valores en [0, 1])
        n:         número de iteraciones (default 1000)
        sigma:     desviación estándar del ruido (default 0.12)

    Retorna tuple de 5 elementos:
        (resultados_lista, media, desv_std, ci_2_5, ci_97_5)
    """
    resultados = []
    for _ in range(n):
        perturbado = {
            k: max(0.0, min(1.0, v + random.gauss(0, sigma)))
            for k, v in variables.items()
        }
        resultados.append(calc_iarri(**perturbado))

    # Calcular estadísticas sin numpy (pura stdlib)
    m = len(resultados)
    media = sum(resultados) / m
    varianza = sum((x - media) ** 2 for x in resultados) / m
    desv = varianza ** 0.5

    ordenados = sorted(resultados)
    idx_low = max(0, int(0.025 * m) - 1)
    idx_high = min(m - 1, int(0.975 * m))
    ci_low = ordenados[idx_low]
    ci_high = ordenados[idx_high]

    return (resultados, media, desv, ci_low, ci_high)
