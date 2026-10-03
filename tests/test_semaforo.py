"""Reglas del semáforo: nivel × tendencia → color, leídas de config/semaforo.yaml."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import comun  # noqa: E402

CONF = comun.semaforo_config()
REGLA = {"clave": "x", "sentido": "mayor_es_mejor"}


def est(valor, ee=0.1):
    return pd.Series({"valor": valor, "ee": ee})


@pytest.mark.parametrize("actual, ref, base, nivel, tendencia, color", [
    (80, 70, 70, "mejor", "mejora", "verde"),
    (80, 70, 90, "mejor", "empeora", "amarillo"),
    (70, 80, 60, "peor", "mejora", "amarillo"),
    (70, 80, 70, "peor", "estable", "rojo"),
    (70, 70.5, None, "similar", "sin_dato", "amarillo"),
    (70, None, None, "sin_dato", "sin_dato", "gris"),
])
def test_matriz(actual, ref, base, nivel, tendencia, color):
    r = comun.evaluar(est(actual), est(ref) if ref else None, est(base) if base else None, REGLA, CONF, "porcentaje")
    assert (r["nivel"], r["tendencia"], r["color"]) == (nivel, tendencia, color)


def test_diferencia_no_significativa_es_similar():
    r = comun.evaluar(est(75, ee=4), est(70, ee=4), None, REGLA, CONF, "porcentaje")
    assert r["nivel"] == "similar"


def test_sentido_menor_es_mejor():
    regla = {"clave": "x", "sentido": "menor_es_mejor"}
    assert comun.evaluar(est(5), est(10), None, regla, CONF, "porcentaje")["nivel"] == "mejor"


def test_calidad_baja_no_se_muestra():
    df = pd.DataFrame({"valor": [1.0, 2.0, 3.0], "ee": [0.1, 0.5, 1.5], "calidad": ["alta", "media", "baja"]})
    p = comun.publicable(df)
    assert p.oculto.tolist() == [False, False, True] and p.aviso.tolist() == [False, True, False]
    assert pd.isna(p.valor.iloc[2]) and comun.fmt(p.valor.iloc[2]) == comun.NO_PUBLICABLE
