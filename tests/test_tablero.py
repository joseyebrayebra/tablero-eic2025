"""Corre cada página del tablero sin navegador y verifica que no falle."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (RAIZ / "data/output/indicadores.parquet").exists(), reason="falta data/output")

PAGINAS = ["resumen", "ficha", "trayectoria", "logro", "brechas", "mapa", "comparativo", "brief", "factores", "factores_nacional"]


@pytest.mark.parametrize("geografia", ["Guanajuato", "Nación"])
@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sin_errores(pagina, geografia, monkeypatch):
    monkeypatch.syspath_prepend(str(RAIZ / "app"))
    at = AppTest.from_file(str(RAIZ / "app" / "paginas" / f"{pagina}.py"), default_timeout=90)
    at.session_state["geografia"] = geografia
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.title
