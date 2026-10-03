"""Estimación con diseño muestral: razones, proporciones, medias y totales.

Varianza por linealización de Taylor (conglomerados últimos) con ESTRATO y UPM,
la misma técnica que usa INEGI para la EIC 2025. Decisiones documentadas en
docs/fase1_catalogo_indicadores.md:

- Sin corrección por población finita: el microdato no trae el total de UPM por
  estrato, así que los errores estándar son conservadores.
- Los municipios censados (COBERTURA = 1) se tratan igual que los muestreados: así
  lo hace INEGI en sus tabulados, y con ello los errores estándar coinciden con los
  publicados (ver src/validacion/contraste_inegi.py).
- Un estrato con una sola UPM en muestra no aporta varianza.
- La UPM se identifica con ESTRATO + UPM y el número de UPM por estrato se toma
  de la muestra completa, no del subconjunto del dominio.
"""

from __future__ import annotations

import polars as pl

ESTRATO, UPM, FACTOR = "ESTRATO", "UPM", "FACTOR"

CV_ALTA, CV_MEDIA = 15.0, 30.0
Z_90 = 1.645


def upm_por_estrato(lf: pl.LazyFrame) -> pl.DataFrame:
    """Número de UPM en muestra por estrato, calculado sobre la muestra completa."""
    return (
        lf.select(ESTRATO, UPM)
        .unique()
        .group_by(ESTRATO)
        .agg(n_upm=pl.len())
        .collect()
    )


def calidad(cv: pl.Expr) -> pl.Expr:
    return (
        pl.when(cv.is_null())
        .then(None)
        .when(cv < CV_ALTA)
        .then(pl.lit("alta"))
        .when(cv <= CV_MEDIA)
        .then(pl.lit("media"))
        .otherwise(pl.lit("baja"))
    )


def estimar(
    lf: pl.LazyFrame,
    num: pl.Expr,
    den: pl.Expr | None,
    grupos: list[str],
    n_upm: pl.DataFrame,
) -> pl.DataFrame:
    """Estima sum(w·num) / sum(w·den) por dominio, con su error estándar.

    num y den son valores por registro, ya en cero fuera del universo.
    Proporción: num = indicadora de la característica, den = indicadora del universo.
    Media: num = valor de la variable dentro del universo, den = indicadora del universo.
    Total: den = None.
    grupos son las columnas que definen el dominio (geografía y desagregación).

    Devuelve una fila por dominio con valor, ee, cv (%), n_muestral (registros
    sin ponderar del universo), li90 y ls90.
    """
    es_total = den is None
    w = pl.col(FACTOR).cast(pl.Float64)
    y = num.cast(pl.Float64)
    x = y if es_total else den.cast(pl.Float64)

    por_upm = (
        lf.with_columns(_y=y * w, _x=x * w, _n=(x != 0).cast(pl.Int64))
        .filter((pl.col("_x") != 0) | (pl.col("_y") != 0))
        .group_by([*grupos, ESTRATO, UPM])
        .agg(Y=pl.col("_y").sum(), X=pl.col("_x").sum(), n=pl.col("_n").sum())
        .collect()
    )

    dominio = por_upm.group_by(grupos).agg(
        Yt=pl.col("Y").sum(), Xt=pl.col("X").sum(), n_muestral=pl.col("n").sum()
    )
    if es_total:
        dominio = dominio.with_columns(valor=pl.col("Yt"))
        z = pl.col("Y")
    else:
        dominio = dominio.with_columns(valor=pl.col("Yt") / pl.col("Xt"))
        z = (pl.col("Y") - pl.col("valor") * pl.col("X")) / pl.col("Xt")

    varianza = (
        por_upm.join(dominio.select(*grupos, "valor", "Xt"), on=grupos, nulls_equal=True)
        .with_columns(z=z)
        .group_by([*grupos, ESTRATO])
        .agg(s1=pl.col("z").sum(), s2=(pl.col("z") ** 2).sum())
        .join(n_upm, on=ESTRATO)
        .with_columns(
            v=pl.when(pl.col("n_upm") < 2)
            .then(0.0)
            .otherwise(
                pl.col("n_upm")
                / (pl.col("n_upm") - 1)
                * (pl.col("s2") - pl.col("s1") ** 2 / pl.col("n_upm"))
            )
        )
        .group_by(grupos)
        .agg(var=pl.col("v").sum())
    )

    return (
        dominio.join(varianza, on=grupos, nulls_equal=True)
        .with_columns(ee=pl.col("var").clip(lower_bound=0).sqrt())
        .with_columns(
            cv=pl.when(pl.col("valor") != 0).then(pl.col("ee") / pl.col("valor").abs() * 100),
            li90=pl.col("valor") - Z_90 * pl.col("ee"),
            ls90=pl.col("valor") + Z_90 * pl.col("ee"),
        )
        .with_columns(calidad=calidad(pl.col("cv")))
        .select(*grupos, "valor", "ee", "cv", "n_muestral", "li90", "ls90", "calidad")
        .sort(grupos)
    )
