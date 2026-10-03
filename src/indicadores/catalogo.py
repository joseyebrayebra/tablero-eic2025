"""Catálogo de indicadores educativos de la EIC 2025 (BORRADOR, pendiente de aprobación).

Cada indicador se define con variables y códigos verificados en el descriptor de
INEGI (docs/diccionario_eic2025.csv). La explicación de cada definición está en
docs/fase1_catalogo_indicadores.md.

Convención de denominadores (la de los tabulados de INEGI): los porcentajes se
calculan sobre toda la población del universo, incluido el "no especificado" de
la variable. Las medias excluyen el "no especificado".
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

EDAD = pl.col("EDAD")
ESCOACUM = pl.col("ESCOACUM").cast(pl.Int32, strict=False)


def edad(desde: int, hasta: int = 130) -> pl.Expr:
    """Edad cumplida en el rango; 999 (no especificado) queda fuera."""
    return EDAD.is_between(desde, hasta)


ASISTE = pl.col("ASISTEN") == "1"
NO_ASISTE = pl.col("ASISTEN") == "3"
OCUPADO = pl.col("CONACT").is_in(["10", "13", "14", "15", "16", "17", "18", "19", "20"])
# Buscó trabajo, pensionado, estudiante, quehaceres, limitación permanente o no trabaja (sin el 99 = no especificado)
NO_OCUPADO = pl.col("CONACT").is_in(["30", "40", "50", "60", "70", "80"])

# Nivel de escolaridad según NIVACAD (agrupación de los tabulados de INEGI)
NIVEL_BASICA = pl.col("NIVACAD").is_in(["01", "02", "03", "06"])
NIVEL_MEDIA_SUPERIOR = pl.col("NIVACAD").is_in(["04", "05", "07", "09"])
NIVEL_SUPERIOR = pl.col("NIVACAD").is_in(["08", "10", "11", "12", "13", "14"])

# Lugar de la escuela: 997, 998 y 999 son "no especificado" y no cuentan como otro lugar
MISMA_ENTIDAD = pl.col("ENT_PAIS_ASI") == ("0" + pl.col("CVE_ENT"))
OTRA_ENTIDAD_O_PAIS = ~MISMA_ENTIDAD & ~pl.col("ENT_PAIS_ASI").is_in(["997", "998", "999"])

SE_TRASLADA = ASISTE & pl.col("TIE_TRASLADO_ESCU").is_in(["1", "2", "3", "4", "5"])
MEDIOS_ESC = ["MED_TRASLADO_ESC1", "MED_TRASLADO_ESC2", "MED_TRASLADO_ESC3"]


def usa_medio(codigos: list[str]) -> pl.Expr:
    return pl.any_horizontal([pl.col(c).is_in(codigos).fill_null(False) for c in MEDIOS_ESC])


@dataclass(frozen=True)
class Indicador:
    clave: str
    nombre: str
    tema: str
    tabla: str  # "personas" o "viviendas"
    tipo: str  # "porcentaje", "media" o "total"
    universo: pl.Expr  # booleano: quién entra al denominador
    condicion: pl.Expr | None = None  # booleano: numerador (porcentaje y total)
    variable: pl.Expr | None = None  # numérico: valor a promediar (media)
    unidad: str = "%"

    def num(self) -> pl.Expr:
        dentro = self.universo.fill_null(False)
        if self.tipo == "media":
            return pl.when(dentro).then(self.variable.cast(pl.Float64)).otherwise(0.0).fill_null(0.0)
        return (dentro & self.condicion.fill_null(False)).cast(pl.Float64)

    def den(self) -> pl.Expr | None:
        if self.tipo == "total":
            return None
        return self.universo.fill_null(False).cast(pl.Float64)


def _asistencia(desde: int, hasta: int) -> Indicador:
    return Indicador(
        f"asistencia_{desde}_{hasta}",
        f"Población de {desde} a {hasta} años que asiste a la escuela",
        "Asistencia escolar",
        "personas",
        "porcentaje",
        edad(desde, hasta),
        ASISTE,
    )


PERSONAS = [
    # --- Asistencia escolar
    _asistencia(3, 5),
    _asistencia(6, 11),
    _asistencia(12, 14),
    _asistencia(15, 17),
    _asistencia(18, 24),
    Indicador("no_asiste_3_17", "Población de 3 a 17 años que no asiste a la escuela",
              "Asistencia escolar", "personas", "porcentaje", edad(3, 17), NO_ASISTE),
    Indicador("no_asiste_3_17_total", "Niñas, niños y adolescentes de 3 a 17 años que no asisten a la escuela",
              "Asistencia escolar", "personas", "total", edad(3, 17), NO_ASISTE, unidad="personas"),
    Indicador("no_estudia_no_trabaja_15_24", "Jóvenes de 15 a 24 años que no asisten a la escuela ni están ocupados",
              "Asistencia escolar", "personas", "porcentaje", edad(15, 24), NO_ASISTE & NO_OCUPADO),
    # --- Escolaridad y rezago
    Indicador("escolaridad_promedio_15mas", "Grado promedio de escolaridad de la población de 15 años y más",
              "Escolaridad y rezago", "personas", "media", edad(15) & (ESCOACUM <= 24), variable=ESCOACUM, unidad="grados"),
    Indicador("analfabetismo_15mas", "Población de 15 años y más analfabeta",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), pl.col("ALFABET") == "3"),
    Indicador("analfabetismo_15mas_total", "Personas de 15 años y más analfabetas",
              "Escolaridad y rezago", "personas", "total", edad(15), pl.col("ALFABET") == "3", unidad="personas"),
    Indicador("sin_basica_completa_15mas", "Población de 15 años y más sin educación básica completa",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), ESCOACUM < 9),
    Indicador("sin_basica_completa_15mas_total", "Personas de 15 años y más sin educación básica completa",
              "Escolaridad y rezago", "personas", "total", edad(15), ESCOACUM < 9, unidad="personas"),
    Indicador("nivel_sin_escolaridad_15mas", "Población de 15 años y más sin escolaridad",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), pl.col("NIVACAD") == "00"),
    Indicador("nivel_basica_15mas", "Población de 15 años y más con educación básica como último nivel",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), NIVEL_BASICA),
    Indicador("nivel_media_superior_15mas", "Población de 15 años y más con educación media superior como último nivel",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), NIVEL_MEDIA_SUPERIOR),
    Indicador("nivel_superior_15mas", "Población de 15 años y más con educación superior",
              "Escolaridad y rezago", "personas", "porcentaje", edad(15), NIVEL_SUPERIOR),
    Indicador("media_superior_completa_20_24", "Jóvenes de 20 a 24 años con educación media superior completa",
              "Escolaridad y rezago", "personas", "porcentaje", edad(20, 24), ESCOACUM.is_between(12, 24)),
    Indicador("superior_25mas", "Población de 25 años y más con educación superior",
              "Escolaridad y rezago", "personas", "porcentaje", edad(25), NIVEL_SUPERIOR),
    # --- Acceso y traslado a la escuela (universo: quienes asisten)
    Indicador("estudia_otro_municipio", "Estudiantes cuya escuela está en otro municipio, estado o país",
              "Acceso y traslado", "personas", "porcentaje", edad(3) & ASISTE,
              OTRA_ENTIDAD_O_PAIS | (MISMA_ENTIDAD & (pl.col("MUN_ASI") != "999") & (pl.col("MUN_ASI") != pl.col("CVE_MUN")))),
    Indicador("traslado_mas_30min", "Estudiantes que tardan más de 30 minutos en llegar a la escuela",
              "Acceso y traslado", "personas", "porcentaje", edad(3) & SE_TRASLADA,
              pl.col("TIE_TRASLADO_ESCU").is_in(["3", "4", "5"])),
    Indicador("traslado_caminando", "Estudiantes que van caminando a la escuela",
              "Acceso y traslado", "personas", "porcentaje", edad(3) & SE_TRASLADA, usa_medio(["01"])),
    Indicador("traslado_transporte_publico", "Estudiantes que usan transporte público para ir a la escuela",
              "Acceso y traslado", "personas", "porcentaje", edad(3) & SE_TRASLADA, usa_medio(["03", "04", "05", "06"])),
    Indicador("traslado_vehiculo_particular", "Estudiantes que van a la escuela en automóvil o motocicleta",
              "Acceso y traslado", "personas", "porcentaje", edad(3) & SE_TRASLADA, usa_medio(["10", "11"])),
]

# Indicadores de hogar: la unidad es la vivienda (una fila = un hogar).
# CON_EDAD_ESCOLAR es una columna derivada: la vivienda tiene residentes de 3 a 17 años.
CON_EDAD_ESCOLAR = pl.col("CON_EDAD_ESCOLAR")

VIVIENDAS = [
    Indicador("hogares_escolar_sin_internet", "Hogares con población de 3 a 17 años sin internet",
              "Condiciones del hogar", "viviendas", "porcentaje", CON_EDAD_ESCOLAR, pl.col("INTERNET") == "8"),
    Indicador("hogares_escolar_sin_computadora", "Hogares con población de 3 a 17 años sin computadora, laptop o tablet",
              "Condiciones del hogar", "viviendas", "porcentaje", CON_EDAD_ESCOLAR, pl.col("COMPUTADORA") == "2"),
    Indicador("hogares_escolar_programas_gobierno", "Hogares con población de 3 a 17 años que reciben ingresos de programas de gobierno",
              "Condiciones del hogar", "viviendas", "porcentaje", CON_EDAD_ESCOLAR, pl.col("INGR_AYUGOB") == "5"),
    Indicador("hogares_escolar_sin_comida", "Hogares con población de 3 a 17 años que se quedaron sin comida por falta de recursos",
              "Condiciones del hogar", "viviendas", "porcentaje", CON_EDAD_ESCOLAR, pl.col("ALIMENTACION") == "1"),
]

CATALOGO = PERSONAS + VIVIENDAS

# --- Series para las páginas de trayectoria y logro (se desagregan por edad o cohorte)
TRAYECTORIA = [
    Indicador("asistencia_edad", "Población que asiste a la escuela, por edad", "Trayectoria", "personas",
              "porcentaje", edad(3, 24), ASISTE),
]
LOGRO = [
    Indicador("logro_basica_completa", "Población con educación básica completa", "Logro", "personas",
              "porcentaje", edad(15), ESCOACUM.is_between(9, 24)),
    Indicador("logro_media_superior_completa", "Población con educación media superior completa", "Logro",
              "personas", "porcentaje", edad(15), ESCOACUM.is_between(12, 24)),
    Indicador("logro_superior", "Población con educación superior", "Logro", "personas", "porcentaje",
              edad(15), NIVEL_SUPERIOR),
]
