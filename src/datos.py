"""Rutas y carga de microdatos procesados, compartidas por el eje educativo y los factores."""

from __future__ import annotations

import csv
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / "data" / "processed" / "eic2025"
GEO = RAIZ / "data" / "processed" / "geo"
SALIDA = RAIZ / "data" / "output"
MUNICIPIOS = RAIZ / "data" / "raw" / "docs" / "clasificaciones_csv" / "MUNICIPIO.csv"

NACIONAL = "00"  # el archivo nacional de INEGI contiene a las 32 entidades
ENTIDAD_FOCO = "11"
PARES = ["01", "14", "16", "22", "24"]


def hay_nacional(tabla: str = "personas") -> bool:
    return (PROCESADOS / tabla / f"ent={NACIONAL}.parquet").exists()


def escanear(tabla: str, nacional: bool = False) -> pl.LazyFrame:
    """Microdatos de una tabla. Por entidad (sin el archivo nacional, que las duplicaría)
    o solo el archivo nacional."""
    carpeta = PROCESADOS / tabla
    if nacional:
        return pl.scan_parquet(carpeta / f"ent={NACIONAL}.parquet")
    archivos = sorted(a for a in carpeta.glob("ent=*.parquet") if a.stem != f"ent={NACIONAL}")
    return pl.scan_parquet(archivos)


def nombres_geo() -> dict[str, dict[str, str]]:
    """Nombres de entidad y municipio del clasificador de INEGI."""
    entidades, municipios = {}, {}
    with open(MUNICIPIOS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ent = r["CVE_ENT"][-2:]
            entidades[ent] = r["DESC_ENT"]
            municipios[ent + r["CVE_MUN"]] = r["DESC_MUN"]
    return {"entidad": entidades, "municipio": municipios}
