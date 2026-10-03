# Contraste con los tabulados publicados por INEGI (2026-10-02)

Fuente de comparación: tabulado de Educación de la EIC 2025 (`data/raw/tabulados/eic2025_educacion.xlsx`,
elaborado por INEGI el 22/09/2026), hojas 04, 06 y 10: nacional y 32 entidades.
Se repite con `.venv/bin/python -m src.validacion.contraste_inegi` → `data/output/contraste_inegi.csv`.

## Resultado

Las 1,980 cifras comparadas coinciden con las de INEGI, tanto en valor como en error estándar.

| Indicador | Cifras comparadas | Mayor diferencia en valor | Error estándar propio / INEGI |
|---|---|---|---|
| Analfabetismo, 15 años y más (total y por sexo) | 99 | 0.000000 | 1.0000 a 1.0003 |
| Asistencia escolar por edad individual, 3 a 19 años (total y por sexo) | 1,683 | 0.000000 | 1.0000 a 1.0014 |
| Grado promedio de escolaridad, 15 años y más (total y por sexo) | 99 | 0.000000 | 1.0000 a 1.0002 |
| Población de 15 años y más sin escolaridad (total y por sexo) | 99 | 0.000000 | 1.0000 a 1.0001 |

| Indicador | Geografía | Valor INEGI | Valor propio | EE INEGI | EE propio |
|---|---|---|---|---|---|
| Analfabetismo, 15 años y más | Nacional | 3.6924 | 3.6924 | 0.0154 | 0.0154 |
| Analfabetismo, 15 años y más | Guanajuato | 4.1017 | 4.1017 | 0.0895 | 0.0895 |
| Grado promedio de escolaridad, 15 años y más | Nacional | 10.2650 | 10.2650 | 0.0120 | 0.0120 |
| Grado promedio de escolaridad, 15 años y más | Guanajuato | 9.5778 | 9.5778 | 0.0627 | 0.0627 |
| Población de 15 años y más sin escolaridad | Nacional | 3.9000 | 3.9000 | 0.0165 | 0.0165 |
| Población de 15 años y más sin escolaridad | Guanajuato | 4.9085 | 4.9085 | 0.1079 | 0.1079 |

## Lo que se corrigió a raíz de la revisión

1. **Municipios censados.** El estimador ponía en cero la varianza de los 750 municipios censados. INEGI no lo
   hace en sus tabulados, y por eso el error estándar propio salía hasta 16 % menor en entidades con muchos
   municipios censados (Nayarit, Oaxaca, Chiapas). Ahora se tratan igual que los muestreados y los errores
   coinciden. Guanajuato no tiene municipios censados: sus cifras no cambiaron.
2. **Estudiantes en otro municipio.** El "no especificado" del lugar de la escuela se contaba como "otro
   municipio". Corregido: Guanajuato pasa de 3.08 % a 3.04 %.
3. **Jóvenes que no estudian ni trabajan.** El "no especificado" de condición de actividad se contaba como
   "no trabaja". Corregido: Guanajuato pasa de 21.98 % a 21.86 %.

## Lo que este contraste confirma y lo que no

- Confirma el factor de expansión, el universo, las definiciones de asistencia, alfabetismo, escolaridad
  acumulada y sin escolaridad, y el cálculo de errores estándar (Taylor con estrato y UPM, sin corrección por
  población finita, igual que INEGI).
- No hay tabulado publicado para contrastar los indicadores propios del tablero: sin básica completa, media
  superior completa de 20 a 24 años, no estudia ni trabaja, traslado e indicadores de hogar. Usan las mismas
  variables y el mismo estimador ya verificados, pero su definición es de este proyecto.
- El nivel municipal no se contrastó: el tabulado de Educación solo trae nacional y entidad.
