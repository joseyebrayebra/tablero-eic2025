# Proyecto: Tablero educativo – Encuesta Intercensal 2025 (INEGI)

## Objetivo
Tablero visual para toma de decisiones con eje en EDUCACIÓN, en tres niveles:
(1) nacional, (2) Guanajuato y sus 46 municipios, (3) comparativo Guanajuato vs nación
vs estados pares (Querétaro, Jalisco, Aguascalientes, San Luis Potosí, Michoacán).

## Datos
- Microdatos EIC 2025 en data/raw/eic2025/ (personas, viviendas y, si existe, migración).
- Censo 2020 (opcional, para tendencia) en data/raw/cpv2020/.
- Descriptor de archivos y cuestionario en data/raw/docs/.
- NUNCA inventes nombres de variables: verifícalos siempre en el descriptor o en los datos.

## Reglas estadísticas (obligatorias)
- Toda estimación usa el factor de expansión. Nunca reportes conteos sin ponderar.
- Errores estándar con el diseño muestral (estrato y UPM), por linealización de Taylor.
- Cada estimación lleva: valor, error estándar, CV y n muestral sin ponderar.
- Calidad por CV: <15 % alta; 15–30 % media (mostrar con advertencia); >30 % baja (no publicar).
- El universo son viviendas particulares habitadas; documentarlo en el tablero.
- Las variables de hogar (alimentación, desplazamiento, ingresos no laborales) se
  analizan como hogares, nunca convertidas a personas.

## Rendimiento
- Los archivos son muy grandes (decenas de millones de personas). Convierte a Parquet,
  lee solo las columnas necesarias y usa polars o DuckDB en lugar de pandas completo.

## Stack
Python. polars/DuckDB para procesamiento, samplics (o implementación propia validada)
para varianzas, Streamlit + Plotly para el tablero, GeoPandas con el Marco Geoestadístico
de INEGI para mapas.

## Arquitectura
data/raw → data/processed (parquet) → src/indicadores (motor) →
data/output/indicadores.parquet (tabla larga) → app/ (tablero, solo lee esa tabla).
Tabla larga: geo_nivel, geo_id, geo_nombre, indicador, desagregacion, categoria,
anio, valor, ee, cv, n_muestral, calidad.

## Forma de trabajo
Trabaja por fases. Al terminar cada fase, detente, resume lo hecho y lo pendiente, y
espera mi aprobación. Si una variable no existe o es ambigua, pregúntame.

## Entorno y comandos
- Entorno: `.venv` (Python 3.14). Dependencias del tablero (lo que se publica) en `requirements.txt`; las del procesamiento en `requirements-procesamiento.txt`.
- Publicación: Streamlit Community Cloud con acceso restringido por correo (`docs/publicacion.md`). El código de `app/` debe correr en Python 3.12: nada de f-strings con comillas anidadas iguales.
- Ingesta CSV → Parquet: `.venv/bin/python -m src.ingesta` (agrega `--forzar` para rehacer).
- Parquet por entidad: `data/processed/eic2025/<tabla>/ent=<NN>.parquet`.
- Mapas: `.venv/bin/python -m src.geo` → `data/processed/geo/*.geojson`.
- Inventario de variables por tema, con códigos de no especificado y faltantes: `docs/inventario_variables.md`.
- Diccionario de variables y categorías (del descriptor de INEGI): `docs/diccionario_eic2025.csv`.
- Pruebas (estimador propio vs samplics): `.venv/bin/python -m pytest tests -q` (tarda ~1 min).
- Motor de indicadores: `.venv/bin/python -m src.indicadores.motor` → `data/output/indicadores.parquet`, `catalogo.csv`, `geo/`.
- Tablero: `.venv/bin/streamlit run app/tablero.py` (solo lee `data/output/` y `config/semaforo.yaml`); guía en `docs/tablero.md`.
- Brief de frases de perspectiva (solo Guanajuato, educación): `.venv/bin/python -m src.brief.generar`; reglas de redondeo en `src/brief/frases.py`.
- Contraste con tabulados de INEGI: `.venv/bin/python -m src.validacion.contraste_inegi`; resultados en `docs/contraste_inegi.md`. Valores y errores estándar deben coincidir.
- Catálogo de indicadores aprobado por el usuario el 2026-10-02 (decisiones en `docs/fase1_catalogo_indicadores.md`).
- Carga de microdatos siempre con `src.datos.escanear` (excluye el archivo nacional `ent=00` para no duplicar entidades).
- Factores asociados (módulo aparte del eje educativo): `.venv/bin/python -m src.factores.estimar` y luego `-m src.factores.regresiones`; salidas `data/output/factores*.{parquet,csv}`; método y resultados en `docs/factores_asociados.md`. Son asociaciones, no causalidad.
- Hechos verificados en los datos: `docs/fase0_diagnostico.md`.
- Decisiones metodológicas y catálogo de indicadores: `docs/fase1_catalogo_indicadores.md`.
- Microdatos disponibles: nacional (`ent=00`, 32 entidades), Guanajuato (11) y pares (01, 14, 16, 22, 24) por separado.
- Decisión del usuario (2026-10-02): no usar el Censo 2020; el semáforo trabaja solo con nivel (`anio_base: null`).
