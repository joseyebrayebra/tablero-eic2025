# Factores asociados al resultado educativo (EIC 2025)

Módulo `src/factores/`, separado del eje educativo. Usa el mismo estimador con diseño muestral
(`src/indicadores/varianza.py`), así que cada estimación lleva valor, error estándar, CV, n muestral y calidad.

> **Son asociaciones, no causalidad.** Todo lo que sigue describe qué condiciones aparecen junto a mejores o
> peores resultados educativos en un corte transversal de 2025. No demuestra que cambiar un factor cambie el
> resultado: hay variables omitidas (ingreso, oferta de planteles, mercado laboral local), la dirección puede ser
> la inversa (un joven que deja la escuela empieza a trabajar) y los modelos municipales están sujetos a la
> falacia ecológica. Sirven para priorizar preguntas y territorios, no para atribuir efectos.

## Cómo se ejecuta

```
.venv/bin/python -m src.factores.estimar       # → data/output/factores.parquet
.venv/bin/python -m src.factores.regresiones   # → factores_regresiones.csv y factores_desviacion_positiva.csv
```

Cobertura: los 372 municipios de Guanajuato y los cinco estados pares, más el nivel entidad. No incluye el
nivel nacional porque el archivo nacional de microdatos no está disponible.

## Definiciones

| Clave | Factor | Unidad | Numerador | Denominador |
|---|---|---|---|---|
| `viv_internet` | Viviendas con internet | vivienda | `INTERNET` = 7 | Todas las viviendas |
| `viv_computadora` | Viviendas con computadora, laptop o tablet | vivienda | `COMPUTADORA` = 1 | Todas las viviendas |
| `viv_hacinamiento` | Hacinamiento | vivienda | `NUMPERS` / `CUADORM` > 2.5 | Viviendas con `CUADORM` especificado |
| `viv_lena_carbon` | Cocinan principalmente con leña o carbón | vivienda | `COMBUSTIBLE` = 1 | Todas las viviendas |
| `hog_remesas` | Reciben ingresos de alguien que vive en otro país | hogar | `INGR_PEROTROPAIS` = 1 | Todos los hogares |
| `hog_programas_gobierno` | Reciben ingresos de programas de gobierno | hogar | `INGR_AYUGOB` = 5 | Todos los hogares |
| `hog_inseguridad_alim_menores` | Algún menor tuvo carencias de alimentación | hogar | Sí en alguna de `ALIM_MEN1-3`, `ING_ALIM_MEN1-3` | Hogares con menores de 18 años |
| `hog_desplazamiento` | Desplazamiento forzado interno | hogar | `DESP_INSEGURIDAD` = 1 o `DESP_CATASTROFES` = 3 | Todos los hogares |
| `jovenes_15_17_activos` | Jóvenes económicamente activos | persona | `CONACT` en 10, 13–20 (ocupados) o 30 (buscó trabajo) | Población de 15 a 17 |
| `mujeres_15_19_con_hijos` | Mujeres con al menos una hija o hijo nacido vivo | persona | `HIJOS_NAC_VIVOS` de 1 a 25 | Mujeres de 15 a 19 |

Notas de definición:
- Hacinamiento sigue el umbral de CONEVAL (más de 2.5 residentes por dormitorio).
- Las preguntas de alimentación de menores solo se aplican cuando hay menores en el hogar y los adultos
  reportaron alguna carencia; el blanco por pase se cuenta como "no".
- Las variables de hogar se estiman como hogares (una fila de `viviendas` = un hogar), nunca como personas.
- Remesas y programas de gobierno se reportan por separado; la EIC solo capta si reciben, no el monto.

## Precisión a nivel municipal (Guanajuato, 46 municipios)

| Factor | Mínimo | Mediana | Máximo | Calidad |
|---|---|---|---|---|
| Viviendas con internet | 55.5 (Coroneo) | 69.5 | 82.8 (Celaya) | 46 alta |
| Viviendas con computadora | 11.4 (Atarjea) | 23.8 | 48.3 (Guanajuato) | 46 alta |
| Hacinamiento | 6.9 (Moroleón) | 12.6 | 18.4 (Tierra Blanca) | 46 alta |
| Leña o carbón | 0.7 (León) | 5.2 | 48.0 (Atarjea) | 42 alta, 4 media |
| Remesas | 3.5 (Guanajuato) | 14.8 | 33.7 (Santiago Maravatío) | 46 alta |
| Programas de gobierno | 36.2 (Apaseo el Grande) | 52.1 | 65.8 (Atarjea) | 46 alta |
| Inseguridad alimentaria de menores | 3.5 (Xichú) | 10.7 | 17.5 (Coroneo) | 43 alta, 3 media |
| Jóvenes 15–17 activos | 9.6 (Atarjea) | 19.9 | 40.7 (Purísima del Rincón) | 45 alta, 1 media |
| Mujeres 15–19 con hijos | 2.9 (Moroleón) | 6.8 | 10.0 (Tarandacuao) | 22 alta, 22 media, 2 baja |
| Desplazamiento | 0.2 (Xichú) | 1.0 | 2.5 (León) | 9 alta, 30 media, 7 baja |

Desplazamiento y maternidad de 15 a 19 años son fenómenos poco frecuentes: a nivel municipal la mayoría de las
estimaciones tiene calidad media o baja y deben mostrarse con advertencia o no publicarse. A nivel estatal
ambas son de calidad alta.

## Asistencia de 15 a 17 años según la escolaridad máxima del hogar

Escolaridad máxima = el mayor número de grados aprobados (`ESCOACUM`) entre las personas de 18 años y más
que viven en el hogar. Estimación con diseño muestral, porcentaje que asiste:

| Escolaridad máxima de los adultos | Guanajuato | Aguascalientes | Jalisco | Michoacán | Querétaro | San Luis Potosí |
|---|---|---|---|---|---|---|
| Sin primaria completa | 38.9 | 47.7 | 43.7 | 34.3 | 36.9 | 41.5 |
| Primaria completa | 42.2 | 39.3 | 43.9 | 38.1 | 42.1 | 45.3 |
| Secundaria completa | 58.0 | 58.4 | 58.7 | 57.8 | 62.3 | 58.8 |
| Media superior completa | 82.7 | 81.6 | 79.6 | 80.3 | 82.7 | 82.6 |
| Superior (4 años o más) | 94.6 | 95.9 | 92.2 | 92.4 | 93.6 | 93.8 |

En Guanajuato todas las categorías tienen calidad alta (CV de 0.6 % a 9.2 %). El dato de "sin primaria
completa" en Aguascalientes es de calidad media (CV 17 %). También se calculó por municipio, pero 35 de las
celdas municipales de Guanajuato son de calidad baja.

Modelo lineal de probabilidad con microdatos (ponderado, errores agrupados por UPM), diferencia en puntos
porcentuales frente a hogares con secundaria completa, Guanajuato (n = 42,581):

| Escolaridad máxima | Sin controles | Con tamaño de localidad, sexo y edad |
|---|---|---|
| Sin primaria completa | −19.1 | −18.1 |
| Primaria completa | −15.6 | −15.1 |
| Media superior completa | +24.7 | +23.9 |
| Superior | +36.6 | +35.4 |

La brecha casi no cambia al controlar por tamaño de localidad: no se explica por vivir en una localidad
rural o urbana. El patrón es igual con los seis estados juntos (n = 249,761).

## Relación de cada factor con los resultados (nivel municipal)

Un modelo por factor sobre 372 municipios, con efectos fijos de entidad y errores robustos (HC3). El
coeficiente es el cambio en puntos porcentuales del resultado por cada desviación estándar del factor.
Control de tamaño de localidad: porcentaje de la población municipal en localidades de menos de 2,500, de
2,500 a 14,999 y de 15,000 a 49,999 habitantes.

| Factor | Asistencia 15–17: sin control | con control | Media superior completa 20–24: sin control | con control |
|---|---|---|---|---|
| Viviendas con computadora | +4.9 | +6.6 | +5.9 | +7.9 |
| Viviendas con internet | +2.3 | +1.2 (no sig.) | +2.9 | +1.5 |
| Hacinamiento | −2.1 | −1.4 | −2.9 | −2.1 |
| Leña o carbón | −0.5 (no sig.) | +0.9 (no sig.) | −1.4 | 0.0 (no sig.) |
| Remesas | −2.3 | −1.4 | −2.0 | −0.8 (no sig.) |
| Programas de gobierno | −0.7 (no sig.) | +1.9 | −1.2 | +1.7 |
| Inseguridad alimentaria de menores | −0.3 (no sig.) | 0.0 (no sig.) | −0.6 (no sig.) | −0.3 (no sig.) |
| Desplazamiento | +1.1 (no sig.) | +0.7 (no sig.) | +0.4 (no sig.) | −0.2 (no sig.) |
| Jóvenes 15–17 activos | −6.7 | −6.5 | −5.8 | −5.5 |
| Mujeres 15–19 con hijos | −3.2 | −2.8 | −4.4 | −3.9 |

"No sig." = p ≥ 0.10. Lecturas principales:
- El control cambia conclusiones. Programas de gobierno pasa de asociación negativa a positiva al comparar
  municipios con la misma estructura de localidades; internet y leña pierden la asociación. Una correlación
  simple habría llevado a lecturas equivocadas.
- Las asociaciones más fuertes y estables son trabajo adolescente, computadora en la vivienda y maternidad
  temprana. Las dos de comportamiento (trabajo y maternidad) compiten directamente con la asistencia: son
  parte del mismo fenómeno más que condiciones previas.
- Inseguridad alimentaria y desplazamiento no muestran asociación a nivel municipal. En desplazamiento influye
  que la estimación municipal es poco precisa, lo que atenúa cualquier relación.

## Desviación positiva en Guanajuato

Resultado esperado: modelo sobre los 372 municipios con las condiciones del hogar (internet, computadora,
hacinamiento, leña, remesas, programas de gobierno, inseguridad alimentaria de menores), el tamaño de
localidad y efectos fijos de entidad. Se excluyen trabajo adolescente y maternidad temprana (no son
condiciones previas) y desplazamiento (poco preciso). El modelo ampliado agrega la escolaridad promedio de
la población de 25 años y más. R² de 0.53 y 0.67 para asistencia; 0.57 y 0.71 para media superior completa.

Un municipio tiene desviación positiva si su residuo estandarizado es ≥ 1 y el residuo supera el margen de
error muestral del valor observado (1.645 × EE). Es robusta si se cumple en los dos modelos.

Asistencia de 15 a 17 años (puntos porcentuales):

| Municipio | Observado | Esperado | Diferencia | Diferencia con escolaridad adulta |
|---|---|---|---|---|
| Apaseo el Alto | 77.1 | 67.4 | +9.7 | +10.3 |
| Santiago Maravatío | 80.1 | 71.0 | +9.1 | +9.6 |
| Villagrán | 80.3 | 71.6 | +8.7 | +8.0 |
| Tarimoro | 74.9 | 66.9 | +8.0 | +8.9 |
| Jaral del Progreso | 75.9 | 68.0 | +7.8 | +6.4 |
| Atarjea | 79.0 | 71.5 | +7.5 | +6.3 |

Comonfort y Santa Catarina cumplen solo en el modelo base.

Jóvenes de 20 a 24 años con media superior completa:

| Municipio | Observado | Esperado | Diferencia | Diferencia con escolaridad adulta |
|---|---|---|---|---|
| Atarjea | 70.8 | 53.8 | +16.9 | +15.7 |
| Santa Catarina | 62.0 | 50.7 | +11.3 | +6.5 |
| Villagrán | 64.4 | 56.9 | +7.6 | +6.8 |
| San José de Iturbide | 70.6 | 63.4 | +7.2 | +8.5 |

Villagrán y Atarjea aparecen en ambos resultados.

En sentido contrario, con resultado menor al esperado en los dos modelos de asistencia: Manuel Doblado
(−15.9), Purísima del Rincón (−15.4), San Francisco del Rincón (−15.0), Ocampo (−12.9), Dolores Hidalgo
(−8.6), León (−8.4) y Xichú (−6.9). Purísima y San Francisco del Rincón tienen además la mayor
participación económica de jóvenes de 15 a 17 años del estado.

## Modelo nacional (apartado separado)

El mismo análisis se repite con todos los municipios del país:

```
.venv/bin/python -m src.factores.estimar nacional       # → data/output/factores_nacional.parquet
.venv/bin/python -m src.factores.regresiones nacional   # → factores_regresiones_nacional.csv, factores_desviacion_positiva_nacional.csv
```

En el tablero aparece como página aparte ("Modelo nacional"). Los valores de cada municipio de Guanajuato son
los mismos; lo que cambia es contra quién se calcula el resultado esperado. Las cifras de este documento
corresponden al modelo con estados pares.

## Límites de este análisis

- La lista de desviación positiva depende de qué condiciones entran al modelo. Es un punto de partida para
  revisar qué se hace distinto en esos municipios, no un ranking de desempeño.
- Atarjea y Santa Catarina son municipios muy pequeños: sus valores tienen errores estándar de 3 a 4 puntos.
  El criterio ya descuenta ese margen, pero conviene confirmarlos con otra fuente.
- Los jóvenes de 20 a 24 años se miden donde viven hoy, no donde estudiaron; la migración puede mover el
  indicador de media superior completa en municipios chicos.
- Los regresores municipales son estimaciones con error muestral, lo que sesga los coeficientes hacia cero.
- Los errores estándar no llevan corrección por población finita, así que son conservadores.
- La EIC no trae ingreso no laboral en monto, oferta educativa ni tipo de escuela; esas omisiones pueden
  explicar parte de los residuos.
