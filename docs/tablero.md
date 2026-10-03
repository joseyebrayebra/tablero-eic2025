# Tablero educativo – cómo se usa y cómo se actualiza

## Ejecutar

```
.venv/bin/python -m src.indicadores.motor      # microdatos → data/output/indicadores.parquet (~5 min con el nacional)
.venv/bin/python -m src.factores.estimar pares && .venv/bin/python -m src.factores.regresiones pares
.venv/bin/python -m src.factores.estimar nacional && .venv/bin/python -m src.factores.regresiones nacional
.venv/bin/python -m src.brief.generar          # → brief_guanajuato.json y brief_guanajuato.md
.venv/bin/python -m src.validacion.contraste_inegi   # contraste con el tabulado publicado por INEGI
.venv/bin/streamlit run app/tablero.py
```

El tablero solo lee `data/output/` y `config/semaforo.yaml`; no importa nada de `src/`.

## Páginas

| Sección | Página | Qué muestra |
|---|---|---|
| Educación | Resumen ejecutivo | 12 indicadores con semáforo: nivel frente a la nación |
| Educación | Ficha educativa | Consulta rápida: todos los indicadores educativos de un territorio, con referente, posición y descarga |
| Educación | Trayectoria por edad | Curva de asistencia de los 3 a los 24 años |
| Educación | Logro por nivel y cohorte | Básica, media superior y superior por generación |
| Educación | Brechas | Un indicador por sexo, tamaño de localidad, lengua indígena, autoadscripción o discapacidad |
| Educación | Mapa y ranking | Los 46 municipios (o las 32 entidades en la vista Nación) |
| Educación | Comparativo | Guanajuato frente a la nación y los estados pares |
| Para comunicar | Brief: cifras en perspectiva | Frases de perspectiva (matemática social) para Guanajuato, con cifras de respaldo |
| Factores asociados | Modelo con estados pares | Factores, escolaridad del hogar, regresiones y desviación positiva (372 municipios) |
| Factores asociados | Modelo nacional | Lo mismo, comparando contra los 2,478 municipios del país |

## Semáforo

Las reglas están en `config/semaforo.yaml` y se releen al recargar la página: referente por nivel geográfico,
tolerancias, exigencia de significancia estadística, matriz nivel × tendencia → color, lista de indicadores
del resumen y sentido de cada indicador (mayor o menor es mejor).

## Regla de calidad

Calidad media (CV de 15 a 30 %): el valor lleva ⚠ y las barras llevan trama rayada. Calidad baja (CV > 30 %):
el valor no se dibuja y en tablas aparece como "n.p."; la página avisa cuántas unidades quedaron sin dato.

## Estado de los datos (2026-10-02)

- Archivo nacional procesado (25.2 millones de personas en muestra, 130.4 millones expandidas): hay vista
  **Nación**, las 32 entidades y referente nacional para el semáforo. El motor tarda unos 5 minutos.
- **Tendencia vs 2020: desactivada por decisión** (no se usa el Censo 2020). El semáforo usa solo el nivel.
  Para activarla, poner `anio_base: 2020` en `config/semaforo.yaml` y agregar filas con `anio = 2020` a
  `indicadores.parquet`.
- Los factores asociados siguen calculados con Guanajuato y sus cinco estados pares.
