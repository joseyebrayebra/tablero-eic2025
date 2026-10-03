"""Motor de indicadores: microdatos procesados → data/output/indicadores.parquet (tabla larga).

Uso: python -m src.indicadores.motor

Niveles geográficos: nacional (solo si está el archivo nacional), entidad, grupo de
estados pares y municipios de Guanajuato. También deja en data/output el catálogo de
indicadores y las capas geográficas, para que el tablero lea únicamente esa carpeta.
"""

from __future__ import annotations

import shutil
import time

import polars as pl

from src.datos import ENTIDAD_FOCO, GEO, PARES, SALIDA, escanear, hay_nacional, nombres_geo

from .catalogo import LOGRO, PERSONAS, TRAYECTORIA, VIVIENDAS, Indicador, edad
from .varianza import estimar, upm_por_estrato

ANIO = 2025
SEXO = pl.col("SEXO").replace_strict({"1": "Hombres", "3": "Mujeres"}, default=None)
TAM_LOCALIDAD = pl.col("TAMLOC").replace_strict(
    {"1": "1 Menos de 2,500", "2": "2 2,500 a 14,999", "3": "3 15,000 a 49,999",
     "4": "4 50,000 y más", "5": "4 50,000 y más"}, default=None)
DIFICULTADES = ["DIS_VER", "DIS_OIR", "DIS_CAMINAR", "DIS_RECORDAR", "DIS_BANARSE", "DIS_HABLAR"]
COHORTE = (
    pl.when(pl.col("EDAD") > 130).then(None)
    .when(pl.col("EDAD") >= 65).then(pl.lit("65+"))
    .when(pl.col("EDAD") >= 55).then(pl.lit("55-64"))
    .when(pl.col("EDAD") >= 45).then(pl.lit("45-54"))
    .when(pl.col("EDAD") >= 35).then(pl.lit("35-44"))
    .when(pl.col("EDAD") >= 25).then(pl.lit("25-34"))
    .when(pl.col("EDAD") >= 20).then(pl.lit("20-24"))
    .when(pl.col("EDAD") >= 15).then(pl.lit("15-19"))
)
EDAD_TXT = pl.when(pl.col("EDAD") <= 130).then(pl.col("EDAD").cast(pl.String).str.zfill(2))

# nombre de la desagregación → expresión que da la categoría (nulo = fuera de la desagregación)
DESAGREGACIONES = {
    "total": pl.lit("total"),
    "sexo": SEXO,
    "tam_localidad": TAM_LOCALIDAD,
    "lengua_indigena": pl.col("HLENGUA").replace_strict(
        {"1": "Habla lengua indígena", "3": "No habla lengua indígena"}, default=None),
    "autoadscripcion_indigena": pl.col("PERTE_INDIGENA").replace_strict(
        {"1": "Se considera indígena", "3": "No se considera indígena"}, default=None),
    "discapacidad": pl.when(pl.any_horizontal([pl.col(c).is_in(["3", "4"]) for c in DIFICULTADES]))
    .then(pl.lit("Con discapacidad")).otherwise(pl.lit("Sin discapacidad")),
    "edad": EDAD_TXT,
    "edad_sexo": EDAD_TXT + "|" + SEXO,
    "cohorte": COHORTE,
    "cohorte_sexo": COHORTE + "|" + SEXO,
}
DESAG_PERSONAS = ["total", "sexo", "tam_localidad", "lengua_indigena", "autoadscripcion_indigena", "discapacidad"]
DESAG_VIVIENDAS = ["total", "tam_localidad"]

COLUMNAS = {
    "personas": ["CVEGEO", "CVE_ENT", "CVE_MUN", "ID_VIV", "ESTRATO", "UPM", "FACTOR", "TAMLOC",
                 "SEXO", "EDAD", "ASISTEN", "ALFABET", "NIVACAD", "ESCOACUM", "CONACT", "HLENGUA", "PERTE_INDIGENA",
                 "MUN_ASI", "ENT_PAIS_ASI", "TIE_TRASLADO_ESCU", "MED_TRASLADO_ESC1", "MED_TRASLADO_ESC2",
                 "MED_TRASLADO_ESC3", *DIFICULTADES],
    "viviendas": ["CVEGEO", "CVE_ENT", "ID_VIV", "ESTRATO", "UPM", "FACTOR", "TAMLOC",
                  "INTERNET", "COMPUTADORA", "INGR_AYUGOB", "ALIMENTACION"],
}


def plan() -> list[tuple[Indicador, list[str]]]:
    tareas = []
    for ind in PERSONAS:
        tareas.append((ind, ["total", "sexo"] if ind.tipo == "total" else DESAG_PERSONAS))
    tareas += [(ind, DESAG_VIVIENDAS) for ind in VIVIENDAS]
    tareas += [(ind, ["edad", "edad_sexo"]) for ind in TRAYECTORIA]
    tareas += [(ind, ["cohorte", "cohorte_sexo"]) for ind in LOGRO]
    return tareas


def cargar(nacional: bool) -> dict[str, pl.LazyFrame]:
    geo = dict(
        G_nacional=pl.lit("00") if nacional else pl.lit(None, dtype=pl.String),
        G_entidad=pl.col("CVE_ENT"),
        G_grupo=pl.when(pl.col("CVE_ENT").is_in(PARES)).then(pl.lit("pares")),
        G_municipio=pl.when(pl.col("CVE_ENT") == ENTIDAD_FOCO).then(pl.col("CVEGEO")),
    )
    personas = escanear("personas", nacional).select(COLUMNAS["personas"]).with_columns(**geo).collect()
    escolar = personas.filter(edad(3, 17)).select("ID_VIV").unique().with_columns(CON_EDAD_ESCOLAR=pl.lit(True))
    viviendas = (
        escanear("viviendas", nacional).select(COLUMNAS["viviendas"]).with_columns(**geo).collect()
        .join(escolar, on="ID_VIV", how="left").with_columns(pl.col("CON_EDAD_ESCOLAR").fill_null(False))
    )
    return {"personas": personas.lazy(), "viviendas": viviendas.lazy()}


def main() -> pl.DataFrame:
    inicio = time.time()
    nacional = hay_nacional()
    tablas = cargar(nacional)
    n_upm = {t: upm_por_estrato(lf) for t, lf in tablas.items()}
    nombres = nombres_geo()
    nombres_nivel = {
        "nacional": {"00": "Nacional"},
        "entidad": nombres["entidad"],
        "grupo": {"pares": "Estados pares"},
        "municipio": nombres["municipio"],
    }
    niveles = (["nacional"] if nacional else []) + ["entidad", "grupo", "municipio"]

    partes = []
    for ind, desagregaciones in plan():
        for desag in desagregaciones:
            lf = tablas[ind.tabla].with_columns(_cat=DESAGREGACIONES[desag]).filter(pl.col("_cat").is_not_null())
            for nivel in niveles:
                col = f"G_{nivel}"
                est = estimar(lf.filter(pl.col(col).is_not_null()), ind.num(), ind.den(), [col, "_cat"], n_upm[ind.tabla])
                if ind.tipo == "porcentaje":
                    est = est.with_columns(pl.col("valor", "ee") * 100)
                partes.append(est.select(
                    geo_nivel=pl.lit(nivel),
                    geo_id=pl.col(col),
                    geo_nombre=pl.col(col).replace_strict(nombres_nivel[nivel], default=None),
                    indicador=pl.lit(ind.clave),
                    desagregacion=pl.lit(desag),
                    categoria=pl.col("_cat"),
                    anio=pl.lit(ANIO),
                    valor="valor", ee="ee", cv="cv", n_muestral="n_muestral", calidad="calidad",
                ))
    tabla = pl.concat(partes)

    SALIDA.mkdir(parents=True, exist_ok=True)
    tabla.write_parquet(SALIDA / "indicadores.parquet")
    pl.DataFrame(
        [{"clave": i.clave, "nombre": i.nombre, "tema": i.tema, "tipo": i.tipo, "unidad": i.unidad,
          "unidad_analisis": "hogares" if i.tabla == "viviendas" else "personas"}
         for i, _ in plan()]
    ).write_csv(SALIDA / "catalogo.csv")
    (SALIDA / "geo").mkdir(exist_ok=True)
    for capa in GEO.glob("*.geojson"):
        shutil.copy2(capa, SALIDA / "geo" / capa.name)

    print(f"indicadores.parquet: {tabla.height:,} estimaciones en {time.time() - inicio:.0f} s "
          f"({'con' if nacional else 'sin'} nivel nacional)")
    print(tabla.group_by("geo_nivel", "calidad").len().sort("geo_nivel", "calidad"))
    return tabla


if __name__ == "__main__":
    main()
