"""Utilidades compartidas del tablero. Solo se lee data/output/ y config/semaforo.yaml."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "output"
CONFIG = RAIZ / "config" / "semaforo.yaml"

ENTIDAD_FOCO, NOMBRE_FOCO = "11", "Guanajuato"
PARES = ["01", "14", "16", "22", "24"]
COMPARADAS = [ENTIDAD_FOCO, *PARES]

# Paleta: el foco siempre en azul, el referente en naranja, el resto neutro
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
NEUTRO, NEUTRO_CLARO, TEXTO, TEXTO_2, REJILLA = "#8a8985", "#c9c8c2", "#0b0b0b", "#52514e", "#e6e5e1"
SECUENCIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORDINAL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
BUENO, CRITICO = "#0ca30c", "#d03b3b"

AVISO = "⚠"
NO_PUBLICABLE = "n.p."


# ------------------------------------------------------------------ carga
@st.cache_data
def indicadores() -> pd.DataFrame:
    return pd.read_parquet(SALIDA / "indicadores.parquet")


@st.cache_data
def factores(sufijo: str = "") -> pd.DataFrame:
    return pd.read_parquet(SALIDA / f"factores{sufijo}.parquet")


@st.cache_data
def brief() -> dict:
    return json.loads((SALIDA / "brief_guanajuato.json").read_text(encoding="utf-8"))


@st.cache_data
def catalogo() -> pd.DataFrame:
    partes = [pd.read_csv(SALIDA / "catalogo.csv")]
    if (SALIDA / "factores_catalogo.csv").exists():
        partes.append(pd.read_csv(SALIDA / "factores_catalogo.csv"))
    return pd.concat(partes).drop_duplicates("clave").set_index("clave")


@st.cache_data
def tabla_csv(nombre: str) -> pd.DataFrame:
    return pd.read_csv(SALIDA / nombre, dtype={"geo_id": str})


@st.cache_data
def geojson(nombre: str) -> dict:
    return json.loads((SALIDA / "geo" / f"{nombre}.geojson").read_text())


def semaforo_config() -> dict:
    # sin caché: el archivo se edita a mano y debe releerse al recargar
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ contexto geográfico
def contexto() -> dict:
    """Geografía elegida en la barra lateral. Detiene la página si no hay datos."""
    eleccion = st.session_state.get("geografia", NOMBRE_FOCO)
    datos = indicadores()
    if eleccion == "Nación":
        if not (datos.geo_nivel == "nacional").any():
            st.warning(
                "No hay datos nacionales en `data/output/indicadores.parquet`. Falta procesar el archivo "
                "nacional de microdatos de la EIC 2025; al agregarlo y volver a correr el motor, esta vista "
                "se activa sola. Mientras tanto usa la vista de Guanajuato.")
            st.stop()
        return {"nivel": "nacional", "id": "00", "nombre": "Nacional", "sub_nivel": "entidad",
                "sub_prefijo": "", "capa": "entidades", "sub_nombre": "entidad"}
    return {"nivel": "entidad", "id": ENTIDAD_FOCO, "nombre": NOMBRE_FOCO, "sub_nivel": "municipio",
            "sub_prefijo": ENTIDAD_FOCO, "capa": f"municipios_{ENTIDAD_FOCO}", "sub_nombre": "municipio"}


def referente(ctx: dict, conf: dict | None = None) -> dict | None:
    """Primer referente con datos para la geografía en foco, según config/semaforo.yaml."""
    conf = conf or semaforo_config()
    datos = indicadores()
    for nivel in conf["referente"].get(ctx["nivel"], []):
        filas = datos[datos.geo_nivel == nivel]
        if nivel == "entidad":
            filas = filas[filas.geo_id == ctx["id"][:2]]
        if len(filas):
            return {"nivel": nivel, "id": filas.geo_id.iloc[0], "nombre": filas.geo_nombre.iloc[0]}
    return None


# ------------------------------------------------------------------ selección y calidad
def serie(datos: pd.DataFrame, indicador: str, desagregacion: str = "total", nivel: str | None = None,
          geo_id: str | None = None, anio: int | None = None) -> pd.DataFrame:
    m = (datos.indicador == indicador) & (datos.desagregacion == desagregacion)
    if nivel is not None:
        m &= datos.geo_nivel == nivel
    if geo_id is not None:
        m &= datos.geo_id == geo_id
    m &= datos.anio == (anio if anio is not None else datos.anio.max())
    return publicable(datos[m])


def publicable(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica la regla de calidad: baja (CV > 30 %) no se muestra; media lleva advertencia."""
    df = df.copy()
    df["oculto"] = df.calidad == "baja"
    df["aviso"] = (df.calidad == "media") | (df.calidad.isna() & (df.ee > 0))
    df.loc[df.oculto, ["valor", "ee"]] = np.nan
    df["li"] = df.valor - 1.645 * df.ee
    df["ls"] = df.valor + 1.645 * df.ee
    return df


def unidad(indicador: str) -> str:
    cat = catalogo()
    return cat.unidad.get(indicador, "%") if indicador in cat.index else "%"


def nombre(indicador: str) -> str:
    cat = catalogo()
    return cat.nombre.get(indicador, indicador) if indicador in cat.index else indicador


def fmt(valor: float, indicador: str | None = None, aviso: bool = False, oculto: bool = False, signo: bool = False) -> str:
    if oculto or valor is None or pd.isna(valor):
        return NO_PUBLICABLE
    u = unidad(indicador) if indicador else "%"
    if u == "personas":
        txt = f"{valor:+,.0f}" if signo else f"{valor:,.0f}"
    elif u == "grados":
        txt = (f"{valor:+.2f}" if signo else f"{valor:.2f}") + " grados"
    else:
        txt = (f"{valor:+.1f}" if signo else f"{valor:.1f}") + (" pp" if signo else " %")
    return f"{txt} {AVISO}" if aviso else txt


def tabla_calidad(df: pd.DataFrame, indicador: str, columnas: dict[str, str]) -> pd.DataFrame:
    """Tabla de consulta: valor formateado, EE, CV, n y calidad; lo no publicable va como n.p."""
    t = df[list(columnas)].rename(columns=columnas)
    t["Valor"] = [fmt(v, indicador, a, o) for v, a, o in zip(df.valor, df.aviso, df.oculto)]
    t["Error estándar"] = df.ee.round(2).values
    t["CV (%)"] = df.cv.round(1).values
    t["n muestral"] = df.n_muestral.values
    t["Calidad"] = df.calidad.fillna("—").values
    t.loc[df.oculto.values, ["Error estándar"]] = np.nan
    return t.reset_index(drop=True)


def leyenda_calidad() -> None:
    st.caption(
        f"Calidad según el coeficiente de variación (CV): alta, menor a 15 %. Media, de 15 a 30 %: se muestra "
        f"con {AVISO} y trama rayada. Baja, mayor a 30 %: no se publica ({NO_PUBLICABLE}). "
        "Barras de error e intervalos al 90 % de confianza.")


def nota_universo() -> None:
    st.caption(
        "Fuente: INEGI, Encuesta Intercensal 2025, microdatos. Universo: viviendas particulares habitadas y sus "
        "residentes habituales. Estimaciones con factor de expansión; errores estándar por linealización de Taylor "
        "con estrato y UPM. Los indicadores de hogar se calculan sobre hogares, no sobre personas.")


# ------------------------------------------------------------------ semáforo
def _clase(dif: float, ee_dif: float, tol: float, conf: dict, sentido: str, etiquetas: tuple[str, str, str]) -> str:
    """Clasifica una diferencia orientada (positiva = favorable)."""
    if pd.isna(dif):
        return "sin_dato"
    favorable = dif if sentido == "mayor_es_mejor" else -dif
    significativa = (not conf.get("exigir_significancia", True)) or pd.isna(ee_dif) or (
        abs(dif) > conf.get("confianza_z", 1.645) * ee_dif)
    if abs(dif) <= tol or not significativa:
        return etiquetas[1]
    return etiquetas[0] if favorable > 0 else etiquetas[2]


def evaluar(actual: pd.Series | None, ref: pd.Series | None, base: pd.Series | None, regla: dict, conf: dict,
            tipo: str) -> dict:
    """Combina nivel (vs referente) y tendencia (vs año base) en un color, según el YAML."""
    tol = regla.get("tolerancia", conf["tolerancia"].get("media" if tipo == "media" else "porcentaje", 1.0))
    sentido = regla["sentido"]

    def diferencia(a, b):
        if a is None or b is None or pd.isna(a.valor) or pd.isna(b.valor):
            return np.nan, np.nan
        return a.valor - b.valor, float(np.hypot(a.ee, b.ee))

    d_nivel, ee_nivel = diferencia(actual, ref)
    d_tend, ee_tend = diferencia(actual, base)
    nivel = _clase(d_nivel, ee_nivel, tol, conf, sentido, ("mejor", "similar", "peor"))
    tendencia = _clase(d_tend, ee_tend, tol, conf, sentido, ("mejora", "estable", "empeora"))
    color = "gris"
    for r in conf["reglas"]:
        if r["nivel"] in ("*", nivel) and r["tendencia"] in ("*", tendencia):
            color = r["color"]
            break
    return {"nivel": nivel, "tendencia": tendencia, "color": color, "dif_nivel": d_nivel, "dif_tendencia": d_tend}


def sentido_de(indicador: str, conf: dict) -> str | None:
    for r in conf["indicadores"]:
        if r["clave"] == indicador:
            return r["sentido"]
    return conf.get("sentido_otros", {}).get(indicador)


# ------------------------------------------------------------------ gráficas
def base_fig(alto: int = 420, titulo_y: str = "", titulo_x: str = "") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=alto, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO_2, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=TEXTO)),
        hoverlabel=dict(bgcolor="white", font_color=TEXTO), bargap=0.35,
    )
    fig.update_xaxes(title=titulo_x, gridcolor=REJILLA, zeroline=False, linecolor=REJILLA)
    fig.update_yaxes(title=titulo_y, gridcolor=REJILLA, zeroline=False, linecolor=REJILLA)
    return fig


def barras_h(df: pd.DataFrame, etiqueta: str, indicador: str, color: str | list[str] = AZUL, alto: int | None = None,
             linea_ref: tuple[float, str] | None = None, extra: str | None = None) -> go.Figure:
    """Barras horizontales con intervalo al 90 %. Calidad media con trama; baja no se dibuja.
    extra: nombre de una columna de df con texto adicional para el hover."""
    d = df[~df.oculto]
    texto_extra = d[extra].astype(str) if extra else pd.Series([""] * len(d), index=d.index)
    u = "" if unidad(indicador) == "personas" else (" %" if unidad(indicador) == "%" else " grados")
    fig = base_fig(alto or max(260, 26 * len(d) + 90))
    fig.add_bar(
        y=d[etiqueta], x=d.valor, orientation="h", marker_color=color, marker_line_width=0,
        marker_pattern_shape=["/" if a else "" for a in d.aviso], marker_pattern_fgcolor="white",
        error_x=dict(type="data", symmetric=False, array=d.ls - d.valor, arrayminus=d.valor - d.li,
                     color=TEXTO_2, thickness=1.2, width=3),
        customdata=np.stack([d.ee, d.cv, d.n_muestral, np.where(d.aviso, f" {AVISO} calidad media", ""), texto_extra], axis=-1),
        hovertemplate="<b>%{y}</b><br>%{x:,.1f}" + u + "%{customdata[3]}<br>EE %{customdata[0]:.2f} · CV %{customdata[1]:.1f} %"
                      "<br>n = %{customdata[2]:,}" + ("<br>%{customdata[4]}" if extra else "") + "<extra></extra>",
        showlegend=False,
    )
    if linea_ref is not None and not pd.isna(linea_ref[0]):
        fig.add_vline(x=linea_ref[0], line_color=NARANJA, line_width=2, line_dash="dot",
                      annotation_text=linea_ref[1], annotation_font_color=TEXTO, annotation_position="top")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=TEXTO))
    fig.update_xaxes(ticksuffix=u)
    return fig


def mostrar(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
