# Fase 0 – Diagnóstico de datos y entorno (2026-10-02)

## Qué datos hay

| Insumo | Estado |
|---|---|
| EIC 2025 Guanajuato (`personas11`, `viviendas11`, `migrantes11`) | Disponible. Enlazado desde `~/Downloads/eic2025_micro_11_csv` y convertido a Parquet |
| EIC 2025 nacional (`eic2025_micro_00_csv.zip`) | Descarga en curso en `~/Downloads` al momento del diagnóstico; sin tocar |
| Descriptor, clasificaciones, diseño de la muestra y cuestionario (`data/raw/docs/`) | Disponibles |
| Censo 2020 (`data/raw/cpv2020/`) | Falta (opcional) |
| Marco Geoestadístico EIC 2025 (`data/raw/mg2025/`) | Guanajuato disponible; capa nacional de entidades en descarga |

## Guanajuato: lo verificado en los datos

Todas las cifras "expandidas" usan `FACTOR`; las "muestrales" son filas sin ponderar.

| Concepto | Muestral | Expandido |
|---|---|---|
| Personas | 796,597 | 6,423,384 |
| Viviendas | 223,876 | 1,808,630 |
| Migrantes internacionales | 17,670 | — |
| Municipios | 46 | |
| Estratos (`ESTRATO`) | 137 | |
| UPM (`ESTRATO` + `UPM`) | 18,531 | |

Diseño muestral:
- `ESTRATO`, `UPM` y `FACTOR` existen en las tres tablas; `FACTOR` no tiene nulos (1 a 278, media 8.06).
- El código de `UPM` se repite entre estratos (412 casos): la UPM debe identificarse como `ESTRATO` + `UPM`.
- Ningún estrato tiene una sola UPM y ninguna UPM cruza municipios, así que la linealización de Taylor es
  aplicable a nivel municipal sin colapsar estratos.
- El factor es el mismo para la vivienda y todas sus personas; la suma de `FACTOR × NUMPERS` en viviendas
  coincide exactamente con la población expandida de personas (6,423,384).
- El municipio más chico en muestra tiene 3,866 personas en 252 UPM.

Variables educativas presentes en `personas`: `ASISTEN`, `MUN_ASI`, `ENT_PAIS_ASI`, `TIE_TRASLADO_ESCU`,
`MED_TRASLADO_ESC1-3`, `NIVACAD`, `ESCOLARI`, `ALFABET`, `ESCOACUM`.
Variables para desagregar: `SEXO`, `EDAD`, `TAMLOC`, `LOC50K`, `HLENGUA`, `PERTE_INDIGENA`, `AFRODES`,
`DIS_*`, `CONACT`, `INGTRMEN`.

Valores observados (el significado de cada código está pendiente del descriptor):

| Variable | Códigos observados | Notas de los datos |
|---|---|---|
| `ASISTEN` | 1, 3, 9; nulo | Nulo solo en edades 0–2 |
| `ALFABET` | 1, 3, 9; nulo | Nulo solo en edades 0–4 |
| `NIVACAD` | 00–14, 99; nulo | Nulo solo en edades 0–2 |
| `ESCOLARI` | 00–08, 99; nulo | |
| `ESCOACUM` | 0–24, 99; nulo | |
| `EDAD` | 0–108, 999 | 999 en 4 registros |
| `SEXO` | 1, 3 | |
| `TAMLOC` | 1–5 | |
| `COBERTURA` | 2 | Valor único en Guanajuato |
| `TIPO_REG` | 0, 1 | 1 en 4,591 personas (35,300 expandidas); en viviendas solo 0 |
| `CLAVIVP` | 01–05, 07–09, 99 | |
| `ALIMENTACION` (viviendas) | 1, 3, 9 | |
| `TIPOHOG` (viviendas) | 1–6, 9 | |

## Dudas resueltas con el descriptor (descargado de INEGI el 2026-10-02)

Fuentes en `data/raw/docs/`: descriptor (`eic2025_micro_fd.xlsx`), clasificaciones, diseño de la muestra,
cuestionario. El descriptor está tabulado en `docs/diccionario_eic2025.csv` (206 variables con sus categorías).

| Tema | Lo que dice la documentación |
|---|---|
| Universo | Viviendas particulares habitadas y sus residentes habituales. Todos los códigos de `CLAVIVP` (01–09, 99) son clases de vivienda particular: todo el archivo está dentro del universo |
| `TIPO_REG` | 0 = encuestado, 1 = imputado (por no respuesta). Los imputados forman parte de la estimación |
| `COBERTURA` | 1 = municipio censado (factor 1, sin error de muestreo), 2 = muestreado, 3 = muestra insuficiente. Guanajuato solo tiene 2; a nivel nacional hay 753 municipios censados |
| No especificado | 9 / 99 / 999 = no especificado; nulo = blanco por pase (no aplica por edad) |
| `SEXO`, `ASISTEN`, `ALFABET`, `HLENGUA` | 1 = sí / hombre, 3 = no / mujer, 9 = no especificado |
| `NIVACAD` | 00 ninguno, 01 preescolar, 02 primaria, 03 secundaria, 04 preparatoria o bachillerato general, 05 bachillerato tecnológico, 06–08 estudios técnicos o comerciales (con primaria / secundaria / preparatoria terminada), 09 normal con primaria o secundaria, 10 normal de licenciatura, 11 licenciatura, 12 especialidad, 13 maestría, 14 doctorado |
| `ESCOLARI` | Grado aprobado dentro del nivel (01–08) |
| `ESCOACUM` | Grados aprobados acumulados (0–24), con tabla de equivalencias en clasificaciones |
| `TAMLOC` | 1 = menos de 2,500; 2 = 2,500–14,999; 3 = 15,000–49,999; 4 = 50,000–99,999; 5 = 100,000 y más |
| Hogar | `TIPOHOG` e `INGTRHOG` están en `viviendas` como variables auxiliares, una fila por vivienda: la unidad de hogar es la vivienda |

Diseño de la muestra (documento de INEGI):
- Probabilístico, estratificado, por conglomerados, en una sola etapa; en cada UPM se entrevistan todas las viviendas.
- Dominios: nacional, entidad, entidad por tamaño de localidad, cada municipio y localidades de 50 mil y más.
- INEGI estima varianzas con series de Taylor y publica intervalos al 90 % (z = 1.645).
- La fórmula de INEGI incluye corrección por población finita (1 − n_h/N_h). El microdato no trae N_h y el
  factor no es constante dentro del estrato (135 de 137 estratos de Guanajuato), así que esa corrección no se
  puede reproducir exactamente. Sin ella los errores estándar quedan sobreestimados (conservadores), sobre todo
  en municipios chicos con fracción de muestreo alta.

## Marco Geoestadístico

Se usa el "Marco Geoestadístico, Encuesta Intercensal 2025" (producto 794551196649), en `data/raw/mg2025/`.
`python -m src.geo` genera las capas simplificadas en `data/processed/geo/`. Los 46 municipios de Guanajuato
coinciden uno a uno con `CVEGEO` de los microdatos.

## Entorno

Python 3.14 en `.venv`: polars 1.44, duckdb 1.5, pyarrow 25, samplics 0.6.1, streamlit 1.64, plotly 7.1,
geopandas 1.2.

`samplics` avisa al importarse que está archivado y sin mantenimiento (sus autores recomiendan `svy`).
