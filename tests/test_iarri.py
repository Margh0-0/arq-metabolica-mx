"""
tests/test_iarri.py — Tests unitarios del modelo científico IARRI-MX

Ejecutar con:  pytest tests/test_iarri.py -v
"""

import random
from math import exp

from core.iarri import calc_iarri, prob_ri, nivel_riesgo, monte_carlo, WEIGHTS


# ─── TESTS: prob_ri ───────────────────────────────────────────────────────────

def test_prob_ri_sigmoide_punto_medio():
    """En v=0.5 la sigmoide debe dar exactamente 0.5"""
    assert abs(prob_ri(0.5) - 0.5) < 1e-10


def test_prob_ri_sigmoide_extremos():
    """Extremos deben acercarse a 0 y 1"""
    assert prob_ri(0.0) < 0.007
    assert prob_ri(1.0) > 0.993


def test_prob_ri_NO_es_lineal():
    """Verificar que NO es la versión lineal incorrecta de main.py"""
    # main.py (incorrecto): min(1.0, 0.10 + 0.50 * v) → para v=0.5 da 0.35
    lineal = min(1.0, 0.10 + 0.50 * 0.5)   # 0.35
    sigmoide = prob_ri(0.5)                   # 0.50
    assert abs(sigmoide - lineal) > 0.1       # son claramente distintas


def test_prob_ri_monotona():
    """La función sigmoide debe ser estrictamente creciente"""
    valores = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    resultados = [prob_ri(v) for v in valores]
    for i in range(len(resultados) - 1):
        assert resultados[i] < resultados[i + 1], (
            f"prob_ri no es monótona: prob_ri({valores[i]})={resultados[i]} "
            f">= prob_ri({valores[i+1]})={resultados[i+1]}"
        )


def test_prob_ri_formula_exacta():
    """Verificar la fórmula sigmoide exacta con valores calculados manualmente"""
    v = 0.3
    esperado = 1.0 / (1.0 + exp(-10.0 * (v - 0.5)))  # 1/(1+e^2) ≈ 0.1192
    assert abs(prob_ri(v) - esperado) < 1e-12


# ─── TESTS: WEIGHTS ───────────────────────────────────────────────────────────

def test_calc_iarri_pesos_correctos():
    """Verificar que los pesos suman 1.0 (α + β + γ + δ + ε = 1)"""
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-10


def test_weights_claves_correctas():
    """Los pesos deben tener exactamente las 5 claves del modelo"""
    assert set(WEIGHTS.keys()) == {"AV", "IC", "ED", "EAR", "IMP"}


# ─── TESTS: calc_iarri ────────────────────────────────────────────────────────

def test_calc_iarri_valores_conocidos():
    """Valores de Cuautlancingo como golden test — resultado en [0, 1]"""
    result = calc_iarri(0.30, 0.20, 0.10, 0.80, 0.70)
    assert 0.0 <= result <= 1.0


def test_calc_iarri_riesgo_bajo():
    """Municipio con excelentes condiciones debe tener IARRI bajo"""
    result = calc_iarri(AV=1.0, IC=1.0, ED=1.0, EAR=0.0, IMP=0.0)
    assert result < 0.33, f"Esperaba IARRI bajo, obtuvo {result}"


def test_calc_iarri_riesgo_alto():
    """Municipio con malas condiciones debe tener IARRI alto"""
    result = calc_iarri(AV=0.0, IC=0.0, ED=0.0, EAR=1.0, IMP=1.0)
    assert result > 0.33, f"Esperaba IARRI alto, obtuvo {result}"


def test_calc_iarri_variables_protectoras():
    """AV, IC, ED son inversas: mayor valor = menor riesgo"""
    bajo = calc_iarri(AV=0.9, IC=0.5, ED=0.5, EAR=0.5, IMP=0.5)
    alto = calc_iarri(AV=0.1, IC=0.5, ED=0.5, EAR=0.5, IMP=0.5)
    assert bajo < alto, "AV debería ser inversamente proporcional al IARRI"


def test_calc_iarri_variables_riesgo():
    """EAR, IMP son directas: mayor valor = mayor riesgo"""
    bajo = calc_iarri(AV=0.5, IC=0.5, ED=0.5, EAR=0.1, IMP=0.5)
    alto = calc_iarri(AV=0.5, IC=0.5, ED=0.5, EAR=0.9, IMP=0.5)
    assert bajo < alto, "EAR debería ser directamente proporcional al IARRI"


# ─── TESTS: nivel_riesgo ─────────────────────────────────────────────────────

def test_nivel_riesgo_bajo():
    label, _ = nivel_riesgo(0.20)
    assert label.lower() in ("bajo", "riesgo bajo")


def test_nivel_riesgo_medio():
    label, _ = nivel_riesgo(0.50)
    assert label.lower() in ("medio", "riesgo medio")


def test_nivel_riesgo_alto():
    label, _ = nivel_riesgo(0.80)
    assert label.lower() in ("alto", "riesgo alto")


def test_nivel_riesgo_retorna_color():
    """nivel_riesgo debe retornar un color hex válido"""
    _, color = nivel_riesgo(0.50)
    assert color.startswith("#"), f"Color inválido: {color}"
    assert len(color) == 7, f"Color hex debe tener 7 chars: {color}"


def test_nivel_riesgo_cobre_todos_los_rangos():
    """Los tres umbrales deben cubrir el rango completo [0, 1]"""
    label_cero, _ = nivel_riesgo(0.0)
    label_uno, _  = nivel_riesgo(1.0)
    label_medio, _ = nivel_riesgo(0.5)
    assert label_cero.lower() in ("bajo", "riesgo bajo")
    assert label_uno.lower() in  ("alto",  "riesgo alto")
    assert label_medio.lower() in ("medio", "riesgo medio")


# ─── TESTS: monte_carlo ───────────────────────────────────────────────────────

def test_monte_carlo_retorna_tuple():
    """monte_carlo debe retornar una tupla de 5 elementos"""
    variables = {"AV": 0.5, "IC": 0.5, "ED": 0.5, "EAR": 0.5, "IMP": 0.5}
    result = monte_carlo(variables, n=100)
    assert len(result) == 5  # array, mean, std, ci_low, ci_high


def test_monte_carlo_resultado_en_rango():
    """Media del Monte Carlo debe estar en [0, 1] y CI debe ser coherente"""
    random.seed(42)
    variables = {"AV": 0.5, "IC": 0.5, "ED": 0.5, "EAR": 0.5, "IMP": 0.5}
    arr, media, desv, ci_lo, ci_hi = monte_carlo(variables, n=100)
    assert 0.0 <= media <= 1.0
    assert ci_lo < media < ci_hi


def test_monte_carlo_n_iteraciones():
    """El array de resultados debe tener exactamente n elementos"""
    variables = {"AV": 0.3, "IC": 0.4, "ED": 0.2, "EAR": 0.7, "IMP": 0.6}
    arr, _, _, _, _ = monte_carlo(variables, n=50)
    assert len(arr) == 50


def test_monte_carlo_desviacion_positiva():
    """La desviación estándar debe ser positiva (hay variabilidad)"""
    random.seed(7)
    variables = {"AV": 0.5, "IC": 0.5, "ED": 0.5, "EAR": 0.5, "IMP": 0.5}
    _, _, desv, _, _ = monte_carlo(variables, n=200)
    assert desv > 0.0, "La simulación Monte Carlo debe tener variabilidad"
