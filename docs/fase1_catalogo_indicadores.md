# Catálogo de indicadores educativos (aprobado el 2026-10-02)

Definiciones en código: `src/indicadores/catalogo.py`. Estimador: `src/indicadores/varianza.py`.
Vista previa por entidad: `python -m src.indicadores.vista_previa` → `data/output/vista_previa_entidad.csv`.

## Decisiones metodológicas tomadas

| Decisión | Elección | Motivo |
|---|---|---|
| Varianza | Implementación propia de Taylor (conglomerados últimos, `ESTRATO` + `UPM`) sobre polars | Coincide con `samplics` en valor y error estándar (4 pruebas en `tests/test_varianza.py`) y corre los 6 estados en ~2 s; `samplics` está archivado y tardó más de un minuto solo en Guanajuato |
| Corrección por población finita | No se aplica | El microdato no trae el total de UPM por estrato. Los errores estándar quedan conservadores: un indicador nunca se publicará con mejor calidad de la que tiene |
| Municipios censados (`COBERTURA` = 1) | Se tratan igual que los muestreados | Así lo hace INEGI en sus tabulados; con ello los errores estándar coinciden con los publicados (`docs/contraste_inegi.md`) |
| Intervalo de confianza | 90 % (z = 1.645) | Es el que publica INEGI; permite comparar con sus tabulados |
| Denominadores | Los porcentajes incluyen el "no especificado" en el denominador; las medias lo excluyen | Convención de los tabulados de INEGI |
| Registros imputados (`TIPO_REG` = 1) | Se incluyen | Forman parte de la estimación oficial |
| Universo | Todo el archivo | Todas las clases de `CLAVIVP` son vivienda particular habitada |

## Decisiones aprobadas por el usuario

1. Rezago educativo: se mide como población de 15 años y más sin educación básica completa; no se agrega la definición de CONEVAL.
2. No estudia ni trabaja: quien busca trabajo cuenta como "no trabaja". El "no especificado" de condición de actividad no entra al numerador.
3. Indicadores de hogar: sobre hogares con población de 3 a 17 años.
4. Brechas: sexo, tamaño de localidad, habla de lengua indígena, autoadscripción indígena y discapacidad.
5. Resumen ejecutivo: los 12 indicadores de `config/semaforo.yaml`.
6. Referente del semáforo: la nación. Sin tendencia (no se usa el Censo 2020).

## Indicadores de personas

Edad con `EDAD` (999 = no especificado, queda fuera de todos los grupos).

| Clave | Indicador | Numerador | Denominador |
|---|---|---|---|
| `asistencia_3_5`, `_6_11`, `_12_14`, `_15_17`, `_18_24` | Población que asiste a la escuela, por grupo de edad | `ASISTEN` = 1 | Población del grupo de edad |
| `no_asiste_3_17` (y `_total`) | Población de 3 a 17 años que no asiste | `ASISTEN` = 3 | Población de 3 a 17 |
| `no_estudia_no_trabaja_15_24` | Jóvenes que no asisten ni están ocupados | `ASISTEN` = 3 y `CONACT` en 30, 40, 50, 60, 70, 80 | Población de 15 a 24 |
| `escolaridad_promedio_15mas` | Grado promedio de escolaridad | Suma de `ESCOACUM` | Población de 15+ con `ESCOACUM` especificado |
| `analfabetismo_15mas` (y `_total`) | Población analfabeta | `ALFABET` = 3 | Población de 15+ |
| `sin_basica_completa_15mas` (y `_total`) | Sin educación básica completa | `ESCOACUM` < 9 | Población de 15+ |
| `nivel_sin_escolaridad_15mas` | Sin escolaridad | `NIVACAD` = 00 | Población de 15+ |
| `nivel_basica_15mas` | Básica como último nivel | `NIVACAD` en 01, 02, 03, 06 | Población de 15+ |
| `nivel_media_superior_15mas` | Media superior como último nivel | `NIVACAD` en 04, 05, 07, 09 | Población de 15+ |
| `nivel_superior_15mas` | Con educación superior | `NIVACAD` en 08, 10–14 | Población de 15+ |
| `media_superior_completa_20_24` | Jóvenes con media superior completa | `ESCOACUM` de 12 a 24 | Población de 20 a 24 |
| `superior_25mas` | Con educación superior | `NIVACAD` en 08, 10–14 | Población de 25+ |
| `estudia_otro_municipio` | Estudiantes con escuela en otro municipio, estado o país | `MUN_ASI` ≠ municipio de residencia o `ENT_PAIS_ASI` ≠ entidad de residencia, sin contar el no especificado | Población de 3+ que asiste |
| `traslado_mas_30min` | Estudiantes que tardan más de 30 minutos | `TIE_TRASLADO_ESCU` en 3, 4, 5 | Estudiantes que se trasladan (`TIE_TRASLADO_ESCU` 1–5) |
| `traslado_caminando` | Van caminando | 01 en alguno de `MED_TRASLADO_ESC1-3` | Estudiantes que se trasladan |
| `traslado_transporte_publico` | Usan transporte público | 03–06 en alguno de `MED_TRASLADO_ESC1-3` | Estudiantes que se trasladan |
| `traslado_vehiculo_particular` | Van en automóvil o motocicleta | 10 u 11 en alguno de `MED_TRASLADO_ESC1-3` | Estudiantes que se trasladan |

Los medios de traslado admiten hasta tres respuestas, así que sus porcentajes no suman 100.

## Indicadores de hogar

Unidad: la vivienda (una fila = un hogar), ponderada con su propio `FACTOR`. El universo son los hogares con al
menos un residente de 3 a 17 años; ese filtro se deriva de la tabla de personas, pero la estimación nunca se
convierte a personas.

| Clave | Indicador | Numerador |
|---|---|---|
| `hogares_escolar_sin_internet` | Sin internet | `INTERNET` = 8 |
| `hogares_escolar_sin_computadora` | Sin computadora, laptop o tablet | `COMPUTADORA` = 2 |
| `hogares_escolar_programas_gobierno` | Reciben ingresos de programas de gobierno (becas, pensiones, apoyos) | `INGR_AYUGOB` = 5 |
| `hogares_escolar_sin_comida` | Se quedaron sin comida por falta de dinero en los últimos tres meses | `ALIMENTACION` = 1 |

## Desagregaciones propuestas

| Desagregación | Variable | Categorías |
|---|---|---|
| Sexo | `SEXO` | Hombres, mujeres |
| Tamaño de localidad | `TAMLOC` | Menos de 2,500; 2,500–14,999; 15,000–49,999; 50,000 y más (dominios de INEGI) |
| Habla lengua indígena | `HLENGUA` | Sí, no |
| Autoadscripción indígena | `PERTE_INDIGENA` | Sí, no |
| Discapacidad | `DIS_*` | Con discapacidad (mucha dificultad o no puede, códigos 3 y 4, en alguna actividad), sin discapacidad |

Niveles geográficos: nacional, entidad (Guanajuato y pares) y los 46 municipios de Guanajuato. Todas las
combinaciones se calculan; la regla de CV decide qué se publica (>30 % no se muestra).

## Verificación

Los valores y errores estándar se contrastaron contra el tabulado de Educación publicado por INEGI
(`docs/contraste_inegi.md`). Las cifras vigentes están en `data/output/indicadores.parquet` y en el tablero.
