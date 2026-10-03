"""Redacción de frases de perspectiva (matemática social) a partir de estimaciones.

Reglas de redondeo, para que la frase nunca diga más de lo que el dato permite:
- "N de cada 10": se usa el múltiplo de 10 más cercano; si el dato se aleja más de
  1.5 puntos se antepone "casi" o "más de".
- "1 de cada N": N = 100 / porcentaje, redondeado al entero.
- Cantidades: a miles ("209 mil") o millones con dos decimales ("1.39 millones de").
"""

from __future__ import annotations


def de_cada_10(p: float) -> str:
    k = round(p / 10)
    if k == 0:
        return uno_de_cada(p)
    d = p - 10 * k
    prefijo = "" if abs(d) <= 1.5 else ("casi " if d < 0 else "más de ")
    return f"{prefijo}{k} de cada 10"


def uno_de_cada(p: float) -> str:
    return f"1 de cada {round(100 / p)}"


def de_cada_100(p: float) -> str:
    return f"{round(p)} de cada 100"


def cantidad(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} millones de"
    if n >= 10_000:
        return f"{round(n / 1000):,} mil"
    return f"{round(n, -2):,.0f}"


def veces(r: float) -> str:
    return f"{r:.1f} veces" if abs(r - round(r)) > 0.15 else f"{round(r)} veces"


def equivalencia_municipal(n: float, poblaciones: dict[str, float], conocidos: list[str]) -> str:
    """Compara una cantidad de personas con la población total de un municipio (EIC 2025)."""
    cercano = min(poblaciones, key=lambda m: abs(poblaciones[m] / n - 1))
    r = n / poblaciones[cercano]
    if 0.93 <= r <= 1.07:
        return f"prácticamente toda la población del municipio de {cercano}"
    if 0.85 <= r < 0.93:
        return f"casi toda la población del municipio de {cercano}"
    if 1.07 < r <= 1.2:
        return f"más que toda la población del municipio de {cercano}"
    mejor = min(conocidos, key=lambda m: abs(n / poblaciones[m] - round(n / poblaciones[m])) if n / poblaciones[m] >= 1.5 else 9)
    k = round(n / poblaciones[mejor])
    return f"unas {k} veces la población del municipio de {mejor}"


_FRACCION = [(0.15, "apenas el inicio"), (0.35, "una cuarta parte"), (0.45, "poco menos de la mitad"),
             (0.55, "la mitad"), (0.70, "poco más de la mitad"), (0.85, "tres cuartas partes"), (1.01, "casi todo")]
_TERMINADO = {6: "la primaria terminada", 7: "el primer año de secundaria", 8: "el segundo año de secundaria",
              9: "la secundaria terminada", 10: "el primer año de bachillerato", 11: "el segundo año de bachillerato",
              12: "el bachillerato terminado"}
_SIGUIENTE = {6: "primer año de secundaria", 7: "segundo", 8: "tercero", 9: "primer año de bachillerato",
              10: "segundo", 11: "tercero", 12: "primer año de universidad"}


def escolaridad_en_palabras(grados: float) -> str:
    base = int(grados)
    fraccion = next(txt for limite, txt in _FRACCION if grados - base < limite)
    return f"{_TERMINADO[base]} y {fraccion} del {_SIGUIENTE[base]}"
