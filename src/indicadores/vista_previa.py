"""Vista previa del catálogo a nivel entidad, para revisar definiciones.

Uso: python -m src.indicadores.vista_previa
Escribe data/output/vista_previa_entidad.csv con la estructura de la tabla larga.
"""

from __future__ import annotations

import polars as pl

from src.datos import SALIDA as CARPETA_SALIDA
from src.datos import escanear

from .catalogo import CATALOGO, edad
from .varianza import estimar, upm_por_estrato

SALIDA = CARPETA_SALIDA / "vista_previa_entidad.csv"

ENTIDADES = {"01": "Aguascalientes", "11": "Guanajuato", "14": "Jalisco",
             "16": "Michoacán de Ocampo", "22": "Querétaro", "24": "San Luis Potosí"}


def cargar() -> dict[str, pl.LazyFrame]:
    personas = escanear("personas")
    con_escolar = personas.filter(edad(3, 17)).select("ID_VIV").unique().with_columns(CON_EDAD_ESCOLAR=pl.lit(True))
    viviendas = (
        escanear("viviendas")
        .join(con_escolar, on="ID_VIV", how="left")
        .with_columns(pl.col("CON_EDAD_ESCOLAR").fill_null(False))
    )
    return {"personas": personas, "viviendas": viviendas}


def main() -> None:
    tablas = cargar()
    n_upm = {t: upm_por_estrato(lf) for t, lf in tablas.items()}
    filas = []
    for ind in CATALOGO:
        est = estimar(tablas[ind.tabla], ind.num(), ind.den(), ["CVE_ENT"], n_upm[ind.tabla])
        if ind.tipo == "porcentaje":
            est = est.with_columns(pl.col("valor", "ee", "li90", "ls90") * 100)
        filas.append(
            est.select(
                geo_nivel=pl.lit("entidad"),
                geo_id=pl.col("CVE_ENT"),
                geo_nombre=pl.col("CVE_ENT").replace_strict(ENTIDADES),
                indicador=pl.lit(ind.clave),
                desagregacion=pl.lit("total"),
                categoria=pl.lit("total"),
                anio=pl.lit(2025),
                valor="valor", ee="ee", cv="cv", n_muestral="n_muestral", calidad="calidad",
            )
        )
    tabla = pl.concat(filas)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tabla.write_csv(SALIDA)

    ancho = tabla.pivot(on="geo_nombre", index="indicador", values="valor", sort_columns=True)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=220, float_precision=2, fmt_str_lengths=40):
        print(ancho)
        print(tabla.filter(pl.col("geo_id") == "11").select("indicador", "valor", "ee", "cv", "n_muestral", "calidad"))
        print("CV máximo:", tabla["cv"].max(), "| calidad:", tabla["calidad"].value_counts().to_dicts())


if __name__ == "__main__":
    main()
