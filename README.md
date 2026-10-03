# Tablero educativo – Encuesta Intercensal 2025

Tablero de consulta sobre educación en Guanajuato, con comparación nacional y con estados pares, construido con
los microdatos de la Encuesta Intercensal 2025 de INEGI.

- **Ver el tablero:** usa el enlace que se te compartió. El acceso está restringido a correos invitados.
- **Fuente:** INEGI, Encuesta Intercensal 2025, microdatos. Universo: viviendas particulares habitadas.
- **Calidad:** cada cifra lleva error estándar y coeficiente de variación. Las de calidad media se marcan con ⚠ y
  las de calidad baja no se muestran. Los valores y errores coinciden con los tabulados publicados por INEGI
  (`docs/contraste_inegi.md`).

## Contenido del repositorio

| Carpeta | Qué contiene |
|---|---|
| `app/` | Tablero Streamlit (solo lee `data/output/` y `config/`) |
| `config/semaforo.yaml` | Reglas del semáforo, editables sin tocar código |
| `data/output/` | Indicadores ya calculados (3.5 MB). Los microdatos no se incluyen |
| `src/` | Procesamiento de microdatos, estimación con diseño muestral, factores y brief |
| `docs/` | Metodología, catálogo, contraste con INEGI, publicación |

Ejecutar en un equipo propio: `pip install -r requirements.txt` y `streamlit run app/tablero.py`.
Actualizar las cifras requiere los microdatos y `requirements-procesamiento.txt` (ver `docs/tablero.md`).
