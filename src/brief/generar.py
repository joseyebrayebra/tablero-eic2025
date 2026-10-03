"""Brief educativo de Guanajuato con frases de perspectiva (matemática social).

Uso: python -m src.brief.generar   (requiere indicadores.parquet y factores.parquet)
Escribe data/output/brief_guanajuato.json (lo lee el tablero) y brief_guanajuato.md.

Cada frase traduce una estimación de la EIC 2025 a un referente cotidiano y conserva
su respaldo: valor, error estándar, CV, n muestral y calidad. Las frases cuyo respaldo
tiene calidad baja no se generan; las de calidad media llevan advertencia. Los
referentes son internos a la propia encuesta (población de municipios, promedio
nacional, otras generaciones), salvo el tamaño de grupo escolar, que es una convención.
"""

from __future__ import annotations

import json

import polars as pl

from src.datos import ENTIDAD_FOCO, SALIDA, escanear
from src.indicadores.catalogo import ASISTE, NO_ASISTE, NO_OCUPADO, edad
from src.indicadores.varianza import estimar, upm_por_estrato

from . import frases as f

GRUPO = 40  # estudiantes por grupo: convención para dimensionar, no es un dato de la encuesta
CONOCIDOS = ["León", "Irapuato", "Celaya", "Salamanca", "Guanajuato"]
ALFABET_NO = pl.col("ALFABET") == "3"


def _fila(tabla: pl.DataFrame, indicador: str, nivel: str, geo_id: str, desag: str = "total", cat: str = "total") -> dict:
    r = tabla.filter((pl.col("indicador") == indicador) & (pl.col("geo_nivel") == nivel) & (pl.col("geo_id") == geo_id)
                     & (pl.col("desagregacion") == desag) & (pl.col("categoria") == cat))
    return r.row(0, named=True)


def _respaldo(concepto: str, r: dict, unidad: str = "%") -> dict:
    return {"concepto": concepto, "valor": r["valor"], "unidad": unidad, "ee": r["ee"], "cv": r["cv"],
            "n_muestral": r["n_muestral"], "calidad": r["calidad"], "tipo": "estimación"}


def _derivado(concepto: str, valor: float, unidad: str, nota: str) -> dict:
    return {"concepto": concepto, "valor": valor, "unidad": unidad, "ee": None, "cv": None, "n_muestral": None,
            "calidad": None, "tipo": "cálculo derivado", "nota": nota}


def extras() -> dict:
    """Estimaciones que no están en la tabla de indicadores: totales de población de Guanajuato."""
    lf = escanear("personas").filter(pl.col("CVE_ENT") == ENTIDAD_FOCO).select(
        "CVEGEO", "CVE_ENT", "ESTRATO", "UPM", "FACTOR", "EDAD", "ASISTEN", "ALFABET", "CONACT").collect().lazy()
    n_upm = upm_por_estrato(lf)

    def total(cond: pl.Expr) -> dict:
        return estimar(lf, cond.fill_null(False).cast(pl.Float64), None, ["CVE_ENT"], n_upm).row(0, named=True)

    def pct(universo: pl.Expr, cond: pl.Expr) -> dict:
        u = universo.fill_null(False)
        r = estimar(lf, (u & cond.fill_null(False)).cast(pl.Float64), u.cast(pl.Float64), ["CVE_ENT"], n_upm)
        r = r.with_columns(pl.col("valor", "ee") * 100)
        return r.row(0, named=True)

    municipios = estimar(lf, pl.lit(1.0), None, ["CVEGEO"], n_upm)
    return {
        "pob_15_17": total(edad(15, 17)),
        "no_asiste_15_17": total(edad(15, 17) & NO_ASISTE),
        "pct_no_asiste_15_17": pct(edad(15, 17), NO_ASISTE),
        "no_asiste_3_5": total(edad(3, 5) & NO_ASISTE),
        "pct_no_asiste_3_5": pct(edad(3, 5), NO_ASISTE),
        "pob_20_24": total(edad(20, 24)),
        "pob_25mas": total(edad(25)),
        "nini": total(edad(15, 24) & NO_ASISTE & NO_OCUPADO),
        "analf_15_29": pct(edad(15, 29), ALFABET_NO),
        "analf_65mas": pct(edad(65), ALFABET_NO),
        "asiste_18_24": total(edad(18, 24) & ASISTE),
        "municipios": dict(zip(municipios["CVEGEO"], municipios["valor"])),
    }


def construir() -> dict:
    ind = pl.read_parquet(SALIDA / "indicadores.parquet")
    fac = pl.read_parquet(SALIDA / "factores.parquet")
    x = extras()
    gto = lambda k, d="total", c="total": _fila(ind, k, "entidad", ENTIDAD_FOCO, d, c)  # noqa: E731
    nac = lambda k, d="total", c="total": _fila(ind, k, "nacional", "00", d, c)  # noqa: E731
    nombres = dict(ind.filter(pl.col("geo_nivel") == "municipio").select("geo_id", "geo_nombre").unique().iter_rows())
    poblaciones = {nombres[k]: v for k, v in x["municipios"].items()}
    equivale = lambda n: f.equivalencia_municipal(n, poblaciones, CONOCIDOS)  # noqa: E731

    def posicion(indicador: str, mayor_es_mejor: bool) -> tuple[int, int]:
        e = ind.filter((pl.col("indicador") == indicador) & (pl.col("geo_nivel") == "entidad")
                       & (pl.col("desagregacion") == "total") & (pl.col("calidad") != "baja"))
        v = gto(indicador)["valor"]
        mejores = e.filter(pl.col("valor") > v if mayor_es_mejor else pl.col("valor") < v).height
        return mejores + 1, e.height

    items = []

    def agregar(id_: str, tema: str, titular: str, frase: str, respaldo: list[dict]) -> None:
        calidades = [r["calidad"] for r in respaldo if r["tipo"] == "estimación"]
        if "baja" in calidades:
            return  # regla de calidad: lo no publicable no se convierte en frase
        items.append({"id": id_, "tema": tema, "titular": titular, "frase": frase,
                      "aviso": "media" in calidades, "respaldo": respaldo})

    # --- 1. Jóvenes de 15 a 17 fuera de la escuela
    p, n = x["pct_no_asiste_15_17"], x["no_asiste_15_17"]
    agregar("fuera_15_17", "Asistencia",
            f"{f.de_cada_10(p['valor']).capitalize()} jóvenes de 15 a 17 años ya no van a la escuela",
            f"Son cerca de {f.cantidad(n['valor'])} jóvenes en edad de bachillerato: {equivale(n['valor'])}.",
            [_respaldo("Población de 15 a 17 años que no asiste a la escuela", p),
             _respaldo("Personas de 15 a 17 años que no asisten", n, "personas")])

    # --- 2. La caída entre los 14 y los 18 años
    e14, e15, e18 = (gto("asistencia_edad", "edad", e) for e in ("14", "15", "18"))
    agregar("caida_14_18", "Asistencia",
            f"A los 14 años van a la escuela {f.de_cada_10(e14['valor'])}; a los 18, solo {f.de_cada_10(e18['valor'])}",
            f"En cuatro años de edad, la asistencia cae de {e14['valor']:.0f} % a {e18['valor']:.0f} %. "
            f"La primera pérdida visible llega al terminar la secundaria: a los 15 años ya solo asisten {f.de_cada_100(e15['valor'])}.",
            [_respaldo("Asistencia a los 14 años", e14), _respaldo("Asistencia a los 15 años", e15),
             _respaldo("Asistencia a los 18 años", e18)])

    # --- 3. Lo que significaría alcanzar el promedio nacional
    a_g, a_n, pob = gto("asistencia_15_17"), nac("asistencia_15_17"), x["pob_15_17"]
    faltan = (a_n["valor"] - a_g["valor"]) / 100 * pob["valor"]
    lugar, de = posicion("asistencia_15_17", True)
    agregar("brecha_nacional", "Asistencia",
            f"Alcanzar el promedio nacional sería tener {f.cantidad(faltan)} jóvenes más en el bachillerato",
            f"En Guanajuato asisten {a_g['valor']:.1f} de cada 100 jóvenes de 15 a 17 años; en el país, {a_n['valor']:.1f}. "
            f"Cerrar esa distancia equivale a llenar unos {round(faltan / GRUPO, -1):,.0f} grupos de {GRUPO} estudiantes. "
            f"Hoy el estado ocupa el lugar {lugar} de {de} entidades.",
            [_respaldo("Asistencia de 15 a 17 años, Guanajuato", a_g), _respaldo("Asistencia de 15 a 17 años, nacional", a_n),
             _respaldo("Población de 15 a 17 años, Guanajuato", pob, "personas"),
             _derivado("Jóvenes adicionales para igualar el promedio nacional", faltan, "personas",
                       "Diferencia de porcentajes por la población de 15 a 17 años")])

    # --- 4. Hombres y mujeres
    m, h = gto("asistencia_15_17", "sexo", "Mujeres"), gto("asistencia_15_17", "sexo", "Hombres")
    agregar("sexo_15_17", "Brechas",
            f"Entre los 15 y los 17 años estudian {f.de_cada_100(m['valor'])} mujeres, pero solo {f.de_cada_100(h['valor'])} hombres",
            f"La distancia es de {m['valor'] - h['valor']:.0f} puntos: la salida temprana de la escuela es sobre todo masculina.",
            [_respaldo("Asistencia de 15 a 17 años, mujeres", m), _respaldo("Asistencia de 15 a 17 años, hombres", h)])

    # --- 5. El peso del hogar
    hogar = fac.filter((pl.col("indicador") == "asistencia_15_17") & (pl.col("geo_nivel") == "entidad")
                       & (pl.col("geo_id") == ENTIDAD_FOCO) & (pl.col("desagregacion") == "escolaridad_max_hogar"))
    bajo = hogar.filter(pl.col("categoria").str.starts_with("2")).row(0, named=True)
    alto = hogar.filter(pl.col("categoria").str.starts_with("5")).row(0, named=True)
    agregar("hogar", "Brechas",
            f"Con estudios universitarios en casa asisten {f.de_cada_10(alto['valor'])}; con solo primaria, {f.de_cada_10(bajo['valor'])}",
            f"La asistencia de los jóvenes de 15 a 17 años en hogares donde algún adulto llegó a la universidad es "
            f"{f.veces(alto['valor'] / bajo['valor'])} la de quienes viven en hogares donde los adultos solo terminaron la primaria. "
            f"Es una asociación: no prueba que la escolaridad del hogar sea la causa.",
            [_respaldo("Asistencia 15-17, hogar con educación superior", alto),
             _respaldo("Asistencia 15-17, hogar con primaria completa como máximo", bajo)])

    # --- 6. Dentro del mismo estado
    mun = ind.filter((pl.col("indicador") == "asistencia_15_17") & (pl.col("geo_nivel") == "municipio")
                     & (pl.col("desagregacion") == "total") & (pl.col("calidad") == "alta")).sort("valor")
    peor, mejor = mun.row(0, named=True), mun.row(-1, named=True)
    agregar("territorio", "Brechas",
            f"En {mejor['geo_nombre']} estudian {f.de_cada_10(mejor['valor'])} jóvenes de 15 a 17 años; en {peor['geo_nombre']}, {f.de_cada_10(peor['valor'])}",
            f"Entre el municipio con mayor asistencia ({mejor['valor']:.0f} %) y el de menor ({peor['valor']:.0f} %) hay "
            f"{mejor['valor'] - peor['valor']:.0f} puntos de diferencia dentro del mismo estado.",
            [_respaldo(f"Asistencia de 15 a 17 años, {mejor['geo_nombre']}", mejor),
             _respaldo(f"Asistencia de 15 a 17 años, {peor['geo_nombre']}", peor)])

    # --- 7. Bachillerato terminado
    ms_g, ms_n, p2024 = gto("media_superior_completa_20_24"), nac("media_superior_completa_20_24"), x["pob_20_24"]
    sin_ms = (100 - ms_g["valor"]) / 100 * p2024["valor"]
    lugar, de = posicion("media_superior_completa_20_24", True)
    agregar("bachillerato", "Logro",
            f"De cada 10 jóvenes de 20 a 24 años, {round((100 - ms_g['valor']) / 10)} no terminaron el bachillerato",
            f"Lo concluyeron {f.de_cada_100(ms_g['valor'])}, frente a {f.de_cada_100(ms_n['valor'])} en el país "
            f"(lugar {lugar} de {de}). Son alrededor de {f.cantidad(sin_ms)} jóvenes sin bachillerato: {equivale(sin_ms)}.",
            [_respaldo("Media superior completa, 20 a 24 años, Guanajuato", ms_g),
             _respaldo("Media superior completa, 20 a 24 años, nacional", ms_n),
             _respaldo("Población de 20 a 24 años, Guanajuato", p2024, "personas"),
             _derivado("Jóvenes de 20 a 24 sin media superior completa", sin_ms, "personas",
                       "Complemento del porcentaje por la población de 20 a 24 años; incluye no especificado")])

    # --- 8. Universidad
    s_g, s_n = gto("superior_25mas"), nac("superior_25mas")
    a1824 = gto("asistencia_18_24")
    agregar("superior", "Logro",
            f"{f.uno_de_cada(s_g['valor']).capitalize()} adultos tiene estudios superiores; en el país, {f.uno_de_cada(s_n['valor'])}",
            f"Entre la población de 25 años y más, {s_g['valor']:.1f} % cursó algún grado de educación superior "
            f"({s_n['valor']:.1f} % nacional). Y la generación que hoy está en edad universitaria tampoco cierra la distancia: "
            f"estudian {f.de_cada_10(a1824['valor'])} jóvenes de 18 a 24 años.",
            [_respaldo("Educación superior, 25 años y más, Guanajuato", s_g), _respaldo("Educación superior, 25 años y más, nacional", s_n),
             _respaldo("Asistencia de 18 a 24 años, Guanajuato", a1824)])

    # --- 9. Escolaridad promedio
    g_g, g_n = gto("escolaridad_promedio_15mas"), nac("escolaridad_promedio_15mas")
    lugar, de = posicion("escolaridad_promedio_15mas", True)
    agregar("escolaridad", "Logro",
            f"En promedio, un guanajuatense estudió {g_g['valor']:.1f} años: {f.escolaridad_en_palabras(g_g['valor'])}",
            f"El promedio nacional es de {g_n['valor']:.1f} años ({f.escolaridad_en_palabras(g_n['valor'])}). "
            f"La diferencia es de {g_n['valor'] - g_g['valor']:.1f} grados por persona, unas dos terceras partes de un ciclo escolar; "
            f"lugar {lugar} de {de}.",
            [_respaldo("Grado promedio de escolaridad, 15 años y más, Guanajuato", g_g, "grados"),
             _respaldo("Grado promedio de escolaridad, 15 años y más, nacional", g_n, "grados")])

    # --- 10. El avance entre generaciones
    b_viejos, b_jovenes = gto("logro_basica_completa", "cohorte", "65+"), gto("logro_basica_completa", "cohorte", "25-34")
    agregar("generaciones", "Logro",
            f"Entre los mayores de 65 años terminaron la secundaria {f.de_cada_10(b_viejos['valor'])}; entre quienes tienen 25 a 34, {f.de_cada_10(b_jovenes['valor'])}",
            f"En dos generaciones la secundaria terminada pasó de {b_viejos['valor']:.0f} % a {b_jovenes['valor']:.0f} %. "
            f"El reto ya no está en la educación básica sino en lo que sigue.",
            [_respaldo("Básica completa, 65 años y más", b_viejos), _respaldo("Básica completa, 25 a 34 años", b_jovenes)])

    # --- 11. Sin secundaria terminada
    sb, sb_t = gto("sin_basica_completa_15mas"), gto("sin_basica_completa_15mas_total")
    agregar("sin_secundaria", "Rezago",
            f"{f.de_cada_10(sb['valor']).capitalize()} personas de 15 años o más no terminaron la secundaria",
            f"Son {f.cantidad(sb_t['valor'])} personas: {equivale(sb_t['valor'])}.",
            [_respaldo("Población de 15 años y más sin básica completa", sb),
             _respaldo("Personas de 15 años y más sin básica completa", sb_t, "personas")])

    # --- 12. Analfabetismo
    an, an_t = gto("analfabetismo_15mas"), gto("analfabetismo_15mas_total")
    agregar("analfabetismo", "Rezago",
            f"{f.uno_de_cada(an['valor']).capitalize()} personas de 15 años o más no sabe leer ni escribir",
            f"Son cerca de {f.cantidad(an_t['valor'])} personas: {equivale(an_t['valor'])}. Es un rezago de generaciones "
            f"anteriores: entre quienes tienen 65 años o más no lee ni escribe {f.uno_de_cada(x['analf_65mas']['valor'])}; "
            f"entre los jóvenes de 15 a 29, {f.uno_de_cada(x['analf_15_29']['valor'])}.",
            [_respaldo("Analfabetismo, 15 años y más", an), _respaldo("Personas analfabetas de 15 años y más", an_t, "personas"),
             _respaldo("Analfabetismo, 65 años y más", x["analf_65mas"]), _respaldo("Analfabetismo, 15 a 29 años", x["analf_15_29"])])

    # --- 13. Ni estudian ni trabajan
    ni, ni_t = gto("no_estudia_no_trabaja_15_24"), x["nini"]
    agregar("nini", "Asistencia",
            f"{f.de_cada_10(ni['valor']).capitalize()} jóvenes de 15 a 24 años no estudian ni tienen trabajo",
            f"Son alrededor de {f.cantidad(ni_t['valor'])} jóvenes: {equivale(ni_t['valor'])}. "
            f"Incluye a quienes buscan trabajo y a quienes se dedican al hogar.",
            [_respaldo("Jóvenes de 15 a 24 que no asisten ni están ocupados", ni),
             _respaldo("Personas de 15 a 24 que no asisten ni están ocupadas", ni_t, "personas")])

    # --- 14. Preescolar
    pr, pr_t = x["pct_no_asiste_3_5"], x["no_asiste_3_5"]
    agregar("preescolar", "Asistencia",
            f"{f.de_cada_10(pr['valor']).capitalize()} niñas y niños de 3 a 5 años no van a preescolar",
            f"Son cerca de {f.cantidad(pr_t['valor'])}: llenarían unos {round(pr_t['valor'] / GRUPO, -1):,.0f} grupos de {GRUPO}.",
            [_respaldo("Población de 3 a 5 años que no asiste", pr), _respaldo("Niñas y niños de 3 a 5 que no asisten", pr_t, "personas")])

    # --- 15. Internet en casa
    it = gto("hogares_escolar_sin_internet")
    co = gto("hogares_escolar_sin_computadora")
    agregar("internet", "Condiciones para estudiar",
            f"{f.uno_de_cada(it['valor']).capitalize()} hogares con niñas, niños o adolescentes no tiene internet",
            f"Y {f.de_cada_10(co['valor'])} no tienen computadora, laptop ni tablet. Se cuentan hogares, no personas.",
            [_respaldo("Hogares con población de 3 a 17 años sin internet", it),
             _respaldo("Hogares con población de 3 a 17 años sin computadora", co)])

    return {
        "geografia": "Guanajuato",
        "titulo": "Educación en Guanajuato: las cifras en perspectiva",
        "fuente": "INEGI, Encuesta Intercensal 2025, microdatos. Universo: viviendas particulares habitadas y sus residentes.",
        "notas": [
            "Cada frase redondea una estimación; el dato exacto con su error estándar está en las cifras de respaldo.",
            "Las equivalencias con municipios usan la población total del municipio estimada con la misma encuesta.",
            f"Los «grupos de {GRUPO}» son una convención para dimensionar, no un dato de la encuesta.",
            "Los cálculos derivados combinan dos estimaciones y no tienen error estándar propio: son órdenes de magnitud.",
            "Las frases sobre el hogar y el territorio describen asociaciones, no causas.",
        ],
        "frases": items,
    }


def a_markdown(brief: dict) -> str:
    lineas = [f"# {brief['titulo']}", "", brief["fuente"], ""]
    for tema in dict.fromkeys(i["tema"] for i in brief["frases"]):
        lineas += [f"## {tema}", ""]
        for i in (i for i in brief["frases"] if i["tema"] == tema):
            lineas += [f"**{i['titular']}.**" + (" ⚠" if i["aviso"] else ""), "", i["frase"], ""]
    lineas += ["## Cómo leer este brief", ""] + [f"- {n}" for n in brief["notas"]] + ["", "## Cifras de respaldo", "",
               "| Concepto | Valor | Error estándar | CV (%) | n muestral | Calidad |", "|---|---|---|---|---|---|"]
    for i in brief["frases"]:
        for r in i["respaldo"]:
            valor = f"{r['valor']:,.0f}" if r["unidad"] == "personas" else f"{r['valor']:.2f} {r['unidad']}"
            if r["tipo"] == "estimación":
                ee = f"{r['ee']:,.0f}" if r["unidad"] == "personas" else f"{r['ee']:.2f}"
                lineas.append(f"| {r['concepto']} | {valor} | {ee} | {r['cv']:.1f} | {r['n_muestral']:,} | {r['calidad']} |")
            else:
                lineas.append(f"| {r['concepto']} | {valor} | — | — | — | cálculo derivado |")
    return "\n".join(lineas) + "\n"


def main() -> None:
    brief = construir()
    (SALIDA / "brief_guanajuato.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
    (SALIDA / "brief_guanajuato.md").write_text(a_markdown(brief), encoding="utf-8")
    for i in brief["frases"]:
        print(f"- [{i['tema']}] {i['titular']}.{' ⚠' if i['aviso'] else ''}\n    {i['frase']}")


if __name__ == "__main__":
    main()
