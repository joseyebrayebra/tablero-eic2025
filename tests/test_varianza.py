"""Valida el estimador propio de Taylor contra samplics con los datos de Guanajuato."""

import warnings
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from src.indicadores.varianza import estimar, upm_por_estrato

PERSONAS = Path(__file__).resolve().parents[1] / "data/processed/eic2025/personas/ent=11.parquet"
COLUMNAS = ["CVEGEO", "CVE_ENT", "ESTRATO", "UPM", "FACTOR", "EDAD", "SEXO", "ALFABET", "ESCOACUM"]

pytestmark = pytest.mark.skipif(not PERSONAS.exists(), reason="faltan los microdatos de Guanajuato")


@pytest.fixture(scope="module")
def datos():
    lf = pl.scan_parquet(PERSONAS).select(COLUMNAS)
    return lf, upm_por_estrato(lf), lf.collect()


def _samplics(df: pl.DataFrame, parametro: str, y, x=None, dominio=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from samplics.estimation import TaylorEstimator
        from samplics.utils.types import PopParam

        est = TaylorEstimator(getattr(PopParam, parametro))
        est.estimate(
            y=y,
            x=x,
            samp_weight=df["FACTOR"].to_numpy().astype(float),
            stratum=df["ESTRATO"].to_numpy(),
            psu=(df["ESTRATO"] + "|" + df["UPM"]).to_numpy(),
            domain=None if dominio is None else df[dominio].to_numpy(),
            remove_nan=True,
        )
    return est


def test_proporcion_estatal_analfabetismo(datos):
    lf, n_upm, df = datos
    universo = (pl.col("EDAD").is_between(15, 130)).cast(pl.Float64)
    num = universo * (pl.col("ALFABET") == "3").cast(pl.Float64)
    propio = estimar(lf, num, universo, ["CVE_ENT"], n_upm).row(0, named=True)

    ref = _samplics(
        df, "ratio", y=df.select(num).to_series().to_numpy(), x=df.select(universo).to_series().to_numpy()
    )
    assert propio["valor"] == pytest.approx(float(ref.point_est), rel=1e-10)
    assert propio["ee"] == pytest.approx(float(ref.stderror), rel=1e-6)


def test_media_municipal_escolaridad(datos):
    lf, n_upm, df = datos
    universo = (pl.col("EDAD").is_between(15, 130) & (pl.col("ESCOACUM") != "99")).fill_null(False)
    den = universo.cast(pl.Float64)
    num = pl.when(universo).then(pl.col("ESCOACUM").cast(pl.Float64)).otherwise(0.0)
    propio = estimar(lf, num, den, ["CVEGEO"], n_upm)

    ref = _samplics(
        df,
        "ratio",
        y=df.select(num).to_series().to_numpy(),
        x=df.select(den).to_series().to_numpy(),
        dominio="CVEGEO",
    )
    assert propio.height == 46
    for fila in propio.iter_rows(named=True):
        assert fila["valor"] == pytest.approx(float(ref.point_est[fila["CVEGEO"]]), rel=1e-10)
        assert fila["ee"] == pytest.approx(float(ref.stderror[fila["CVEGEO"]]), rel=1e-6)


def test_total_por_sexo(datos):
    lf, n_upm, df = datos
    num = (pl.col("EDAD").is_between(15, 130) & (pl.col("ALFABET") == "3")).fill_null(False).cast(pl.Float64)
    propio = estimar(lf, num, None, ["SEXO"], n_upm)

    ref = _samplics(df, "total", y=df.select(num).to_series().to_numpy(), dominio="SEXO")
    for fila in propio.iter_rows(named=True):
        assert fila["valor"] == pytest.approx(float(ref.point_est[fila["SEXO"]]), rel=1e-10)
        assert fila["ee"] == pytest.approx(float(ref.stderror[fila["SEXO"]]), rel=1e-6)


def test_estrato_con_una_sola_upm_no_aporta_varianza():
    df = pl.DataFrame({"ESTRATO": ["a"] * 4, "UPM": ["1"] * 4, "FACTOR": [1] * 4, "y": [1.0, 0.0, 1.0, 1.0], "g": ["x"] * 4})
    r = estimar(df.lazy(), pl.col("y"), pl.lit(1.0), ["g"], upm_por_estrato(df.lazy())).row(0, named=True)
    assert r["valor"] == pytest.approx(0.75)
    assert r["ee"] == 0.0
