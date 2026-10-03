"""Definición de los factores asociados, a partir de variables verificadas en el descriptor.

Los factores de hogar usan la vivienda como unidad (una fila = un hogar) y nunca
se convierten a personas. Las columnas CON_MENORES y ESC_MAX_HOGAR se derivan en
src/factores/datos.py.
"""

from __future__ import annotations

import polars as pl

from src.indicadores.catalogo import ASISTE, ESCOACUM, OCUPADO, Indicador, edad

TODO = pl.lit(True)
DORMITORIOS = pl.col("CUADORM").cast(pl.Int32, strict=False)
RESIDENTES = pl.col("NUMPERS").cast(pl.Float64, strict=False)
ACTIVO = OCUPADO | (pl.col("CONACT") == "30")
HIJOS = pl.col("HIJOS_NAC_VIVOS").cast(pl.Int32, strict=False)

# Alguna de las seis situaciones de los menores de 18 años por falta de dinero o recursos
MENORES_AFECTADOS = pl.any_horizontal(
    (pl.col("ALIM_MEN1") == "1").fill_null(False),
    (pl.col("ALIM_MEN2") == "3").fill_null(False),
    (pl.col("ALIM_MEN3") == "5").fill_null(False),
    (pl.col("ING_ALIM_MEN1") == "1").fill_null(False),
    (pl.col("ING_ALIM_MEN2") == "3").fill_null(False),
    (pl.col("ING_ALIM_MEN3") == "5").fill_null(False),
)
DESPLAZADO = (pl.col("DESP_INSEGURIDAD") == "1").fill_null(False) | (pl.col("DESP_CATASTROFES") == "3").fill_null(False)

TEMA = "Factores asociados"

FACTORES = [
    Indicador("viv_internet", "Viviendas con internet", TEMA, "viviendas", "porcentaje", TODO, pl.col("INTERNET") == "7"),
    Indicador("viv_computadora", "Viviendas con computadora, laptop o tablet", TEMA, "viviendas", "porcentaje",
              TODO, pl.col("COMPUTADORA") == "1"),
    Indicador("viv_hacinamiento", "Viviendas con hacinamiento (más de 2.5 residentes por dormitorio)", TEMA,
              "viviendas", "porcentaje", DORMITORIOS.is_between(1, 25), RESIDENTES / DORMITORIOS > 2.5),
    Indicador("viv_lena_carbon", "Viviendas que cocinan principalmente con leña o carbón", TEMA, "viviendas",
              "porcentaje", TODO, pl.col("COMBUSTIBLE") == "1"),
    Indicador("hog_remesas", "Hogares que reciben ingresos de alguien que vive en otro país", TEMA, "viviendas",
              "porcentaje", TODO, pl.col("INGR_PEROTROPAIS") == "1"),
    Indicador("hog_programas_gobierno", "Hogares que reciben ingresos de programas de gobierno", TEMA, "viviendas",
              "porcentaje", TODO, pl.col("INGR_AYUGOB") == "5"),
    Indicador("hog_inseguridad_alim_menores", "Hogares con menores de 18 años donde algún menor tuvo carencias de alimentación",
              TEMA, "viviendas", "porcentaje", pl.col("CON_MENORES"), MENORES_AFECTADOS),
    Indicador("hog_desplazamiento", "Hogares con desplazamiento forzado interno (inseguridad o catástrofes)", TEMA,
              "viviendas", "porcentaje", TODO, DESPLAZADO),
    Indicador("jovenes_15_17_activos", "Jóvenes de 15 a 17 años económicamente activos", TEMA, "personas",
              "porcentaje", edad(15, 17), ACTIVO),
    Indicador("mujeres_15_19_con_hijos", "Mujeres de 15 a 19 años con al menos una hija o hijo nacido vivo", TEMA,
              "personas", "porcentaje", (pl.col("SEXO") == "3") & edad(15, 19), HIJOS.is_between(1, 25)),
]

# Contexto para las regresiones: distribución de la población por tamaño de localidad
# y escolaridad de la población adulta.
CONTEXTO = [
    Indicador("pob_loc_menos_2500", "Población en localidades de menos de 2,500 habitantes", "Contexto", "personas",
              "porcentaje", TODO, pl.col("TAMLOC") == "1"),
    Indicador("pob_loc_2500_14999", "Población en localidades de 2,500 a 14,999 habitantes", "Contexto", "personas",
              "porcentaje", TODO, pl.col("TAMLOC") == "2"),
    Indicador("pob_loc_15000_49999", "Población en localidades de 15,000 a 49,999 habitantes", "Contexto", "personas",
              "porcentaje", TODO, pl.col("TAMLOC") == "3"),
    Indicador("escolaridad_promedio_25mas", "Grado promedio de escolaridad de la población de 25 años y más", "Contexto",
              "personas", "media", edad(25) & (ESCOACUM <= 24), variable=ESCOACUM, unidad="grados"),
]

# Resultados educativos que se relacionan con los factores (definidos igual que en el eje educativo)
RESULTADOS = [
    Indicador("asistencia_15_17", "Población de 15 a 17 años que asiste a la escuela", "Resultado educativo",
              "personas", "porcentaje", edad(15, 17), ASISTE),
    Indicador("media_superior_completa_20_24", "Jóvenes de 20 a 24 años con educación media superior completa",
              "Resultado educativo", "personas", "porcentaje", edad(20, 24), ESCOACUM.is_between(12, 24)),
]

# Escolaridad máxima de las personas de 18 años y más del hogar (grados acumulados)
ESC_HOGAR_CATEGORIAS = ["1 Sin primaria completa", "2 Primaria completa", "3 Secundaria completa",
                        "4 Media superior completa", "5 Superior (4 años o más)"]
_esc = pl.col("ESC_MAX_HOGAR")
ESC_HOGAR_CAT = (
    pl.when(_esc.is_null()).then(pl.lit("9 Sin adultos o no especificado"))
    .when(_esc < 6).then(pl.lit(ESC_HOGAR_CATEGORIAS[0]))
    .when(_esc < 9).then(pl.lit(ESC_HOGAR_CATEGORIAS[1]))
    .when(_esc < 12).then(pl.lit(ESC_HOGAR_CATEGORIAS[2]))
    .when(_esc < 16).then(pl.lit(ESC_HOGAR_CATEGORIAS[3]))
    .otherwise(pl.lit(ESC_HOGAR_CATEGORIAS[4]))
)
