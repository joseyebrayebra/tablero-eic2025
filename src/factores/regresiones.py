"""Relación de los factores con los resultados educativos, controlando por tamaño de localidad.

Uso: python -m src.factores.regresiones [pares|nacional]   (requiere data/output/factores[_nacional].parquet)

Tres análisis, todos descriptivos (asociaciones, no causalidad):
1. Microdatos: asistencia de 15 a 17 años según la escolaridad máxima de los adultos
   del hogar, con modelo lineal de probabilidad ponderado y errores agrupados por UPM.
2. Municipal: un modelo por factor, con y sin control por tamaño de localidad.
3. Desviación positiva: resultado observado contra el esperado por las condiciones.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import polars as pl
import statsmodels.formula.api as smf

from src.indicadores.catalogo import edad

from .catalogo import ESC_HOGAR_CAT, FACTORES, RESULTADOS
from .datos import AMBITOS, SALIDA, cargar

ENTIDAD_FOCO = "11"
Z_90 = 1.645
CONTROL_LOCALIDAD = ["pob_loc_menos_2500", "pob_loc_2500_14999", "pob_loc_15000_49999"]
# Condiciones del hogar y del entorno que entran al modelo de resultado esperado.
# Se excluyen el trabajo adolescente y la maternidad temprana (compiten con la asistencia,
# no son condiciones previas) y el desplazamiento (estimación municipal poco precisa).
CONDICIONES = ["viv_internet", "viv_computadora", "viv_hacinamiento", "viv_lena_carbon",
               "hog_remesas", "hog_programas_gobierno", "hog_inseguridad_alim_menores"]
ESCOLARIDAD_ADULTA = "escolaridad_promedio_25mas"


# ---------------------------------------------------------------- 1. Microdatos
def modelo_hogar(ambito: str = "pares") -> pd.DataFrame:
    """Brecha de asistencia 15-17 por escolaridad máxima del hogar, ajustada por
    tamaño de localidad, sexo y edad. Referencia: secundaria completa."""
    nacional, _, _ = AMBITOS[ambito]
    personas = cargar(nacional)["personas"]
    df = (
        personas.filter(edad(15, 17) & pl.col("ASISTEN").is_in(["1", "3"]))
        .select(
            "CVE_ENT", "TAMLOC", "SEXO", "EDAD", "FACTOR",
            asiste=(pl.col("ASISTEN") == "1").cast(pl.Float64) * 100,
            esc_hogar=ESC_HOGAR_CAT,
            upm=pl.col("ESTRATO") + "|" + pl.col("UPM"),
        )
        .filter(~pl.col("esc_hogar").str.starts_with("9"))
        .collect()
        .to_pandas()
    )
    ref = "3 Secundaria completa"
    formula = f"asiste ~ C(esc_hogar, Treatment('{ref}')) + C(TAMLOC) + C(SEXO) + C(EDAD)"
    filas = []
    for ambito, datos, extra in [
        ("Guanajuato", df[df.CVE_ENT == ENTIDAD_FOCO], ""),
        ("Todo el país" if nacional else "Guanajuato y estados pares", df, " + C(CVE_ENT)"),
    ]:
        for etiqueta, f in [("sin controles", f"asiste ~ C(esc_hogar, Treatment('{ref}'))" + extra),
                            ("con tamaño de localidad, sexo y edad", formula + extra)]:
            m = smf.wls(f, datos, weights=datos.FACTOR).fit(
                cov_type="cluster", cov_kwds={"groups": pd.factorize(datos.upm)[0]})
            for termino in m.params.index:
                if "esc_hogar" in termino:
                    filas.append({
                        "analisis": "microdatos_asistencia_15_17", "ambito": ambito, "modelo": etiqueta,
                        "resultado": "asistencia_15_17", "termino": termino.split("[T.")[1].rstrip("]"),
                        "coef": m.params[termino], "ee": m.bse[termino],
                        "li90": m.params[termino] - Z_90 * m.bse[termino],
                        "ls90": m.params[termino] + Z_90 * m.bse[termino],
                        "p": m.pvalues[termino], "n": int(m.nobs), "r2": m.rsquared,
                    })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------- 2 y 3. Municipal
def tabla_municipal(sufijo: str = "") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Una fila por municipio: valores y errores estándar de cada indicador."""
    t = pl.read_parquet(SALIDA / f"factores{sufijo}.parquet").filter(
        (pl.col("geo_nivel") == "municipio") & (pl.col("desagregacion") == "total"))
    ancho = lambda col: (t.pivot(on="indicador", index=["geo_id", "geo_nombre"], values=col)
                         .sort("geo_id").to_pandas().set_index("geo_id"))
    valores, ee = ancho("valor"), ancho("ee")
    valores["entidad"] = valores.index.str[:2]
    return valores, ee


def _z(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def modelos_por_factor(valores: pd.DataFrame, descripcion: str) -> pd.DataFrame:
    """Para cada factor: resultado ~ factor, sin y con control por tamaño de localidad.
    El coeficiente es el cambio en puntos porcentuales del resultado por cada
    desviación estándar del factor; errores robustos HC3; efectos fijos de entidad."""
    filas = []
    control = " + ".join(CONTROL_LOCALIDAD)
    for res in RESULTADOS:
        for fac in FACTORES:
            d = valores.dropna(subset=[fac.clave, res.clave, *CONTROL_LOCALIDAD])
            d = d.assign(x=_z(d[fac.clave]), y=d[res.clave])
            for etiqueta, f in [("sin control", "y ~ x + C(entidad)"),
                                ("con tamaño de localidad", f"y ~ x + {control} + C(entidad)")]:
                m = smf.ols(f, d).fit(cov_type="HC3")
                filas.append({
                    "analisis": "municipal_por_factor", "ambito": descripcion,
                    "modelo": etiqueta, "resultado": res.clave, "termino": fac.clave,
                    "coef": m.params["x"], "ee": m.bse["x"],
                    "li90": m.params["x"] - Z_90 * m.bse["x"], "ls90": m.params["x"] + Z_90 * m.bse["x"],
                    "p": m.pvalues["x"], "n": int(m.nobs), "r2": m.rsquared,
                })
    return pd.DataFrame(filas)


def desviacion_positiva(valores: pd.DataFrame, ee: pd.DataFrame) -> pd.DataFrame:
    """Compara el resultado observado con el esperado por las condiciones del municipio.

    Modelo base: condiciones del hogar + tamaño de localidad + efectos fijos de entidad.
    Modelo ampliado: agrega la escolaridad promedio de la población de 25 años y más.
    Desviación positiva: residuo estandarizado >= 1 y residuo mayor que el margen de
    error muestral del valor observado (1.645 × EE). Es "robusta" si se cumple en ambos.
    """
    base = " + ".join(CONDICIONES + CONTROL_LOCALIDAD) + " + C(entidad)"
    partes = []
    for res in RESULTADOS:
        completos = valores.dropna(subset=[*CONDICIONES, *CONTROL_LOCALIDAD, ESCOLARIDAD_ADULTA, res.clave])
        d = completos.assign(y=completos[res.clave])
        salida = pd.DataFrame({
            "geo_id": d.index, "geo_nombre": d.geo_nombre.values, "resultado": res.clave,
            "observado": d.y.values, "ee_observado": ee.loc[d.index, res.clave].values,
        }, index=d.index)
        for nombre, f in [("base", f"y ~ {base}"), ("ampliado", f"y ~ {base} + {ESCOLARIDAD_ADULTA}")]:
            m = smf.ols(f, d).fit()
            estandar = m.get_influence().resid_studentized_external
            salida[f"esperado_{nombre}"] = m.fittedvalues
            salida[f"residuo_{nombre}"] = m.resid
            salida[f"residuo_est_{nombre}"] = estandar
            salida[f"r2_{nombre}"] = m.rsquared
            supera_error = m.resid > Z_90 * salida.ee_observado
            salida[f"positiva_{nombre}"] = (estandar >= 1) & supera_error
            salida[f"negativa_{nombre}"] = (estandar <= -1) & (m.resid < -Z_90 * salida.ee_observado)
        salida["desviacion_positiva_robusta"] = salida.positiva_base & salida.positiva_ampliado
        partes.append(salida[salida.geo_id.str.startswith(ENTIDAD_FOCO)])
    return pd.concat(partes, ignore_index=True)


def main(ambito: str = "pares") -> None:
    _, sufijo, descripcion = AMBITOS[ambito]
    valores, ee = tabla_municipal(sufijo)
    regresiones = pd.concat([modelo_hogar(ambito), modelos_por_factor(valores, descripcion)], ignore_index=True)
    regresiones.to_csv(SALIDA / f"factores_regresiones{sufijo}.csv", index=False)
    desviacion = desviacion_positiva(valores, ee)
    desviacion["municipios_modelo"] = len(valores)
    desviacion.to_csv(SALIDA / f"factores_desviacion_positiva{sufijo}.csv", index=False)

    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200,
                  "display.float_format", "{:.2f}".format)
    print(regresiones[regresiones.analisis.str.startswith("micro")][["ambito", "modelo", "termino", "coef", "ee", "p", "n"]])
    print(regresiones[regresiones.analisis.str.startswith("muni")]
          .pivot(index=["resultado", "termino"], columns="modelo", values=["coef", "p"]))
    print("municipios en los modelos:", len(valores), "| R2:",
          desviacion.groupby("resultado")[["r2_base", "r2_ampliado"]].first().to_dict())
    cols = ["geo_nombre", "observado", "esperado_base", "residuo_base", "residuo_est_base",
            "residuo_ampliado", "residuo_est_ampliado", "positiva_base", "desviacion_positiva_robusta"]
    for res, g in desviacion.groupby("resultado"):
        print(f"\n== {res}: mayores residuos positivos y negativos (Guanajuato)")
        g = g.sort_values("residuo_base", ascending=False)
        print(g[cols].head(8)); print(g[cols + ["negativa_base"]].tail(5))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pares")
