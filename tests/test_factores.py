"""Pruebas de las definiciones de factores con registros sintéticos."""

import polars as pl

from src.factores.catalogo import ESC_HOGAR_CAT, FACTORES

POR_CLAVE = {f.clave: f for f in FACTORES}


def _evaluar(clave: str, filas: dict) -> tuple[list, list]:
    ind = POR_CLAVE[clave]
    r = pl.DataFrame(filas).select(num=ind.num(), den=ind.den())
    return r["num"].to_list(), r["den"].to_list()


def test_hacinamiento_umbral_y_no_especificado():
    num, den = _evaluar("viv_hacinamiento", {"NUMPERS": ["5", "5", "6", "3"], "CUADORM": ["2", "1", "99", None]})
    assert num == [0.0, 1.0, 0.0, 0.0]  # 5/2 = 2.5 no es hacinamiento; 5/1 sí
    assert den == [1.0, 1.0, 0.0, 0.0]  # 99 y nulo quedan fuera del universo


def test_inseguridad_alimentaria_solo_hogares_con_menores():
    filas = {
        "CON_MENORES": [True, True, False],
        "ALIM_MEN1": ["2", None, None], "ALIM_MEN2": ["3", None, None], "ALIM_MEN3": ["6", None, None],
        "ING_ALIM_MEN1": ["2", None, None], "ING_ALIM_MEN2": ["4", None, None], "ING_ALIM_MEN3": ["6", None, None],
    }
    num, den = _evaluar("hog_inseguridad_alim_menores", filas)
    assert num == [1.0, 0.0, 0.0]  # blanco por pase cuenta como "no"
    assert den == [1.0, 1.0, 0.0]


def test_desplazamiento_usa_codigos_distintos_por_pregunta():
    num, _ = _evaluar("hog_desplazamiento", {"DESP_INSEGURIDAD": ["1", "2", "2", "9"], "DESP_CATASTROFES": ["4", "3", "4", "9"]})
    assert num == [1.0, 1.0, 0.0, 0.0]


def test_mujeres_con_hijos_excluye_no_especificado():
    filas = {"SEXO": ["3", "3", "3", "1"], "EDAD": [17, 19, 16, 18], "HIJOS_NAC_VIVOS": ["1", "98", "0", None]}
    num, den = _evaluar("mujeres_15_19_con_hijos", filas)
    assert num == [1.0, 0.0, 0.0, 0.0]
    assert den == [1.0, 1.0, 1.0, 0.0]


def test_categorias_escolaridad_del_hogar():
    cat = pl.DataFrame({"ESC_MAX_HOGAR": [None, 5, 6, 9, 12, 15, 16]}).select(c=ESC_HOGAR_CAT)["c"].to_list()
    assert [c[0] for c in cat] == ["9", "1", "2", "3", "4", "4", "5"]
