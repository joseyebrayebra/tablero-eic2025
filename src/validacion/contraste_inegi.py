"""Contrasta data/output/indicadores.parquet con el tabulado de Educación publicado por INEGI.

Uso: python -m src.validacion.contraste_inegi
Lee data/raw/tabulados/eic2025_educacion.xlsx (hojas 04, 06 y 10: nacional y 32 entidades)
y escribe data/output/contraste_inegi.csv con valor y error estándar de ambas fuentes.
"""

from __future__ import annotations

import warnings

import openpyxl
import polars as pl

from src.datos import RAIZ, SALIDA

TABULADO = RAIZ / "data" / "raw" / "tabulados" / "eic2025_educacion.xlsx"
SEXOS = {"Total": None, "Hombres": "Hombres", "Mujeres": "Mujeres"}


def _hoja(wb, nombre: str) -> tuple[list[str], list[tuple]]:
    filas = list(wb[nombre].iter_rows(values_only=True))
    ini = next(i for i, f in enumerate(filas) if f[0] == "Entidad federativa")
    encabezado = [a or b for a, b in zip(filas[ini + 1], filas[ini])]
    datos = [f for f in filas[ini + 2:] if f[3] in ("Valor", "Error estándar")]
    return [str(e).strip() if e else "" for e in encabezado], datos


def _geo(etiqueta: str) -> tuple[str, str]:
    if etiqueta == "Estados Unidos Mexicanos":
        return "nacional", "00"
    return "entidad", etiqueta[:2]


def leer_tabulado() -> pl.DataFrame:
    """Tabla larga con las cifras de INEGI en las mismas claves que indicadores.parquet."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(TABULADO, read_only=True, data_only=True)
    registros: dict[tuple, dict] = {}

    def anotar(f: tuple, indicador: str, desag: str, categoria: str, valor) -> None:
        nivel, gid = _geo(f[0])
        llave = (nivel, gid, indicador, desag, categoria)
        registros.setdefault(llave, {})["valor_inegi" if f[3] == "Valor" else "ee_inegi"] = float(valor)

    # Hoja 04: alfabetismo de 15 años y más
    enc, datos = _hoja(wb, "04")
    col = next(i for i, e in enumerate(enc) if e.startswith("Analfabeta"))
    for f in datos:
        if f[2] == "Total":
            sexo = SEXOS[f[1]]
            anotar(f, "analfabetismo_15mas", "sexo" if sexo else "total", sexo or "total", f[col])

    # Hoja 06: asistencia escolar por edad individual (3 a 19 años)
    enc, datos = _hoja(wb, "06")
    col = next(i for i, e in enumerate(enc) if e.startswith("Asiste"))
    for f in datos:
        if f[2].endswith(" años") and len(f[2]) == 7:
            sexo, edad = SEXOS[f[1]], f[2][:2]
            anotar(f, "asistencia_edad", "edad_sexo" if sexo else "edad", f"{edad}|{sexo}" if sexo else edad, f[col])

    # Hoja 10: sin escolaridad y grado promedio de escolaridad, 15 años y más
    enc, datos = _hoja(wb, "10")
    col_sin = next(i for i, e in enumerate(enc) if e.startswith("Sin escolaridad"))
    col_gpe = next(i for i, e in enumerate(enc) if e.startswith("Grado promedio"))
    for f in datos:
        if f[2] == "Total":
            sexo = SEXOS[f[1]]
            anotar(f, "escolaridad_promedio_15mas", "sexo" if sexo else "total", sexo or "total", f[col_gpe])
            anotar(f, "nivel_sin_escolaridad_15mas", "sexo" if sexo else "total", sexo or "total", f[col_sin])

    return pl.DataFrame(
        [dict(zip(["geo_nivel", "geo_id", "indicador", "desagregacion", "categoria"], k), **v) for k, v in registros.items()]
    )


def main() -> pl.DataFrame:
    inegi = leer_tabulado()
    propio = pl.read_parquet(SALIDA / "indicadores.parquet").select(
        "geo_nivel", "geo_id", "geo_nombre", "indicador", "desagregacion", "categoria", "valor", "ee")
    c = inegi.join(propio, on=["geo_nivel", "geo_id", "indicador", "desagregacion", "categoria"], how="left").with_columns(
        dif_valor=pl.col("valor") - pl.col("valor_inegi"),
        razon_ee=pl.when(pl.col("ee_inegi") > 0).then(pl.col("ee") / pl.col("ee_inegi")),
    )
    c.write_csv(SALIDA / "contraste_inegi.csv")
    resumen = c.group_by("indicador", "desagregacion").agg(
        comparaciones=pl.len(),
        sin_pareja=pl.col("valor").is_null().sum(),
        dif_max_abs=pl.col("dif_valor").abs().max(),
        razon_ee_mediana=pl.col("razon_ee").median(),
        razon_ee_min=pl.col("razon_ee").min(),
        razon_ee_max=pl.col("razon_ee").max(),
    ).sort("indicador", "desagregacion")
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=200, float_precision=4, fmt_str_lengths=40):
        print(resumen)
        print(c.filter(pl.col("geo_id").is_in(["00", "11"]) & pl.col("desagregacion").is_in(["total"]))
              .select("geo_id", "indicador", "valor_inegi", "valor", "ee_inegi", "ee", "razon_ee").sort("indicador", "geo_id"))
    return c


if __name__ == "__main__":
    main()
