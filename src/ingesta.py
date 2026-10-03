"""Convierte los CSV de microdatos de la EIC 2025 a Parquet.

Uso:
    python -m src.ingesta            # convierte todo lo que haya en data/raw/eic2025
    python -m src.ingesta --forzar   # reescribe aunque el parquet ya exista

Todas las columnas se conservan como texto (los códigos traen ceros a la
izquierda), salvo las numéricas listadas en NUMERICAS. Cada archivo
<tabla><ent>.csv se escribe en data/processed/eic2025/<tabla>/ent=<ent>.parquet.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS = RAIZ / "data" / "raw" / "eic2025"
PROCESADOS = RAIZ / "data" / "processed" / "eic2025"

# Columnas cuyo carácter numérico se verificó en los datos (no en catálogos).
NUMERICAS = {
    "personas": {"FACTOR": "INTEGER", "EDAD": "SMALLINT"},
    "viviendas": {"FACTOR": "INTEGER"},
    "migrantes": {"FACTOR": "INTEGER"},
}

PATRON = re.compile(r"^(personas|viviendas|migrantes)(\d{2})\.csv$", re.IGNORECASE)


def convertir(csv: Path, forzar: bool = False) -> Path | None:
    m = PATRON.match(csv.name)
    if not m:
        return None
    tabla, ent = m.group(1).lower(), m.group(2)
    destino = PROCESADOS / tabla / f"ent={ent}.parquet"
    if destino.exists() and not forzar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    origen = f"read_csv('{csv}', header=true, all_varchar=true)"
    columnas = [c[0] for c in con.execute(f"describe select * from {origen}").fetchall()]
    tipos = NUMERICAS[tabla]
    seleccion = ", ".join(
        f'cast("{c}" as {tipos[c]}) as "{c}"' if c in tipos else f'"{c}"' for c in columnas
    )
    con.execute(
        f"copy (select {seleccion} from {origen}) to '{destino}' "
        "(format parquet, compression zstd)"
    )
    n_csv = con.execute(f"select count(*) from {origen}").fetchone()[0]
    n_pq = con.execute(f"select count(*) from '{destino}'").fetchone()[0]
    if n_csv != n_pq:
        destino.unlink()
        raise RuntimeError(f"{csv.name}: {n_csv} filas en CSV vs {n_pq} en Parquet")
    print(f"{csv.name}: {n_pq:,} filas, {len(columnas)} columnas -> {destino.relative_to(RAIZ)}")
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--forzar", action="store_true", help="reescribe parquets existentes")
    args = ap.parse_args()
    archivos = sorted(CRUDOS.rglob("*.csv"))
    if not archivos:
        raise SystemExit(f"No hay CSV en {CRUDOS}")
    for csv in archivos:
        convertir(csv, args.forzar)


if __name__ == "__main__":
    main()
