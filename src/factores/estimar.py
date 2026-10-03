"""Estima factores, contexto y resultados por entidad y municipio.

Uso: python -m src.factores.estimar [pares|nacional]
Escribe data/output/factores.parquet (o factores_nacional.parquet) con la estructura de la tabla larga.
"""

from __future__ import annotations

import sys

import polars as pl

from src.indicadores.catalogo import ASISTE, Indicador, edad
from src.indicadores.varianza import estimar, upm_por_estrato

from .catalogo import CONTEXTO, ESC_HOGAR_CAT, FACTORES, RESULTADOS
from .datos import AMBITOS, SALIDA, cargar, nombres_geo

NIVELES = {"entidad": "CVE_ENT", "municipio": "CVEGEO"}
ANIO = 2025


def tabla_larga(est: pl.DataFrame, ind: Indicador, nivel: str, nombres: dict[str, str],
                desagregacion: str = "total", categoria: pl.Expr = pl.lit("total")) -> pl.DataFrame:
    if ind.tipo == "porcentaje":
        est = est.with_columns(pl.col("valor", "ee") * 100)
    return est.select(
        geo_nivel=pl.lit(nivel),
        geo_id=pl.col(NIVELES[nivel]),
        geo_nombre=pl.col(NIVELES[nivel]).replace_strict(nombres, default=None),
        indicador=pl.lit(ind.clave),
        desagregacion=pl.lit(desagregacion),
        categoria=categoria,
        anio=pl.lit(ANIO),
        valor="valor", ee="ee", cv="cv", n_muestral="n_muestral", calidad="calidad",
    )


def main(ambito: str = "pares") -> pl.DataFrame:
    nacional, sufijo, _ = AMBITOS[ambito]
    tablas = cargar(nacional)
    n_upm = {t: upm_por_estrato(lf) for t, lf in tablas.items()}
    nombres = nombres_geo()
    partes = []
    for ind in FACTORES + CONTEXTO + RESULTADOS:
        for nivel, col in NIVELES.items():
            est = estimar(tablas[ind.tabla], ind.num(), ind.den(), [col], n_upm[ind.tabla])
            partes.append(tabla_larga(est, ind, nivel, nombres[nivel]))

    # Asistencia de 15 a 17 años según la escolaridad máxima de los adultos del hogar
    asistencia = RESULTADOS[0]
    personas = tablas["personas"].filter(edad(15, 17)).with_columns(ESC_HOGAR=ESC_HOGAR_CAT)
    for nivel, col in NIVELES.items():
        est = estimar(personas, asistencia.num(), asistencia.den(), [col, "ESC_HOGAR"], n_upm["personas"])
        partes.append(tabla_larga(est, asistencia, nivel, nombres[nivel], "escolaridad_max_hogar", pl.col("ESC_HOGAR")))

    tabla = pl.concat(partes)
    SALIDA.mkdir(parents=True, exist_ok=True)
    tabla.write_parquet(SALIDA / f"factores{sufijo}.parquet")
    pl.DataFrame(
        [{"clave": i.clave, "nombre": i.nombre, "tema": i.tema, "tipo": i.tipo, "unidad": i.unidad,
          "unidad_analisis": "hogares" if i.tabla == "viviendas" else "personas"}
         for i in FACTORES + CONTEXTO + RESULTADOS]
    ).write_csv(SALIDA / "factores_catalogo.csv")
    print(f"factores{sufijo}.parquet: {tabla.height:,} estimaciones")
    print(tabla.group_by("geo_nivel", "calidad").len().sort("geo_nivel", "calidad"))
    return tabla


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pares")
