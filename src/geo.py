"""Prepara las capas del Marco Geoestadístico (EIC 2025) para el tablero.

Uso: python -m src.geo
Lee los shapefiles de data/raw/mg2025, simplifica la geometría, reproyecta a
WGS84 y escribe GeoJSON ligeros en data/processed/geo/.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

RAIZ = Path(__file__).resolve().parents[1]
MG = RAIZ / "data" / "raw" / "mg2025"
SALIDA = RAIZ / "data" / "processed" / "geo"

# (shapefile de origen, archivo de salida, tolerancia de simplificación en metros)
CAPAS = [
    (MG / "11_guanajuato" / "conjunto_de_datos" / "11mun.shp", "municipios_11.geojson", 100),
    (MG / "integrado" / "conjunto_de_datos" / "00ent.shp", "entidades.geojson", 500),
]


def preparar(origen: Path, nombre: str, tolerancia: float) -> Path | None:
    if not origen.exists():
        print(f"Falta {origen.relative_to(RAIZ)}; se omite {nombre}")
        return None
    capa = gpd.read_file(origen)
    capa["geometry"] = capa.geometry.simplify(tolerancia, preserve_topology=True)
    capa = capa.to_crs(4326)
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / nombre
    capa.to_file(destino, driver="GeoJSON", COORDINATE_PRECISION=5)
    print(f"{nombre}: {len(capa)} polígonos, {destino.stat().st_size / 1e6:.2f} MB")
    return destino


def main() -> None:
    for origen, nombre, tolerancia in CAPAS:
        preparar(origen, nombre, tolerancia)


if __name__ == "__main__":
    main()
