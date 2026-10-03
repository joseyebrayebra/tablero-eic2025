"""Reglas de redondeo de las frases de perspectiva y regla de calidad del brief."""

import json
from pathlib import Path

import pytest

from src.brief import frases as f

BRIEF = Path(__file__).resolve().parents[1] / "data/output/brief_guanajuato.json"


@pytest.mark.parametrize("p, esperado", [
    (71.2, "7 de cada 10"), (28.7, "3 de cada 10"), (27.8, "casi 3 de cada 10"), (22.0, "más de 2 de cada 10"),
    (88.0, "casi 9 de cada 10"), (4.1, "1 de cada 24"),
])
def test_de_cada_10(p, esperado):
    assert f.de_cada_10(p) == esperado


def test_cantidades():
    assert f.cantidad(208_888) == "209 mil"
    assert f.cantidad(1_394_986) == "1.39 millones de"


def test_equivalencia_municipal():
    pobs = {"A": 100_000, "B": 300_000, "León": 1_700_000, "Irapuato": 600_000}
    assert "prácticamente toda la población del municipio de A" == f.equivalencia_municipal(98_000, pobs, ["León", "Irapuato"])
    assert "unas 2 veces la población del municipio de Irapuato" == f.equivalencia_municipal(1_200_000, pobs, ["León", "Irapuato"])


def test_escolaridad_en_palabras():
    assert f.escolaridad_en_palabras(9.58) == "la secundaria terminada y poco más de la mitad del primer año de bachillerato"


@pytest.mark.skipif(not BRIEF.exists(), reason="falta data/output/brief_guanajuato.json")
def test_brief_sin_cifras_de_calidad_baja():
    brief = json.loads(BRIEF.read_text(encoding="utf-8"))
    assert brief["frases"]
    for frase in brief["frases"]:
        for r in frase["respaldo"]:
            assert r["calidad"] != "baja"
            if r["tipo"] == "estimación":
                assert r["ee"] is not None and r["cv"] is not None and r["n_muestral"] > 0
