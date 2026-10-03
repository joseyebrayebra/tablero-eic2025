"""Carga de microdatos con las columnas derivadas que necesitan los factores."""

from __future__ import annotations

import polars as pl

from src.datos import SALIDA, escanear, nombres_geo  # noqa: F401  (reexportados)
from src.indicadores.catalogo import ESCOACUM, edad

DISENO = ["CVEGEO", "CVE_ENT", "ID_VIV", "ESTRATO", "UPM", "FACTOR"]
COLUMNAS = {
    "personas": [*DISENO, "TAMLOC", "SEXO", "EDAD", "ASISTEN", "ESCOACUM", "CONACT", "HIJOS_NAC_VIVOS"],
    "viviendas": [*DISENO, "INTERNET", "COMPUTADORA", "NUMPERS", "CUADORM", "COMBUSTIBLE", "INGR_PEROTROPAIS",
                  "INGR_AYUGOB", "ALIM_MEN1", "ALIM_MEN2", "ALIM_MEN3", "ING_ALIM_MEN1", "ING_ALIM_MEN2",
                  "ING_ALIM_MEN3", "DESP_INSEGURIDAD", "DESP_CATASTROFES"],
}
AMBITOS = {  # ámbito → (usa el archivo nacional, sufijo de los archivos de salida, descripción)
    "pares": (False, "", "Municipios de Guanajuato y estados pares"),
    "nacional": (True, "_nacional", "Todos los municipios del país"),
}


def cargar(nacional: bool = False) -> dict[str, pl.LazyFrame]:
    """Personas y viviendas (en memoria, solo las columnas necesarias) con derivadas de hogar."""
    personas = escanear("personas", nacional).select(COLUMNAS["personas"]).collect()
    hogar = personas.group_by("ID_VIV").agg(
        CON_MENORES=edad(0, 17).any(),
        ESC_MAX_HOGAR=ESCOACUM.filter(edad(18) & (ESCOACUM <= 24)).max(),
    )
    viviendas = escanear("viviendas", nacional).select(COLUMNAS["viviendas"]).collect().join(hogar, on="ID_VIV", how="left")
    return {"personas": personas.join(hogar, on="ID_VIV", how="left").lazy(), "viviendas": viviendas.lazy()}
