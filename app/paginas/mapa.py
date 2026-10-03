import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import comun as c

ctx = c.contexto()
conf = c.semaforo_config()
datos = c.indicadores()
cat = c.catalogo()

st.title(f"Mapa y ranking por {ctx['sub_nombre']} · {ctx['nombre']}")

sub_todo = datos[(datos.geo_nivel == ctx["sub_nivel"]) & datos.geo_id.str.startswith(ctx["sub_prefijo"])
                 & (datos.desagregacion == "total")]
opciones = [k for k in cat.index if k in set(sub_todo.indicador)]
ind = st.selectbox("Indicador", opciones, format_func=c.nombre,
                   index=opciones.index("asistencia_15_17") if "asistencia_15_17" in opciones else 0)
sentido = c.sentido_de(ind, conf)
d = c.serie(datos, ind, "total", ctx["sub_nivel"])
d = d[d.geo_id.str.startswith(ctx["sub_prefijo"])]
foco = c.serie(datos, ind, "total", ctx["nivel"], ctx["id"])
valor_foco, ee_foco = (foco.valor.iloc[0], foco.ee.iloc[0]) if len(foco) else (np.nan, np.nan)
sufijo = {"%": " %", "grados": " grados"}.get(c.unidad(ind), "")

col_mapa, col_rank = st.columns([1, 1])
with col_mapa:
    visibles = d[~d.oculto]
    fig = go.Figure()
    capa = c.geojson(ctx["capa"])
    if d.oculto.any():
        ocultos = d[d.oculto]
        fig.add_choropleth(geojson=capa, featureidkey="properties.CVEGEO", locations=ocultos.geo_id, z=[0] * len(ocultos),
                           colorscale=[[0, c.NEUTRO_CLARO], [1, c.NEUTRO_CLARO]], showscale=False,
                           marker_line=dict(color="white", width=1), text=ocultos.geo_nombre,
                           hovertemplate="<b>%{text}</b><br>No publicable (CV > 30 %)<extra></extra>")
    fig.add_choropleth(
        geojson=capa, featureidkey="properties.CVEGEO", locations=visibles.geo_id, z=visibles.valor,
        colorscale=[[i / (len(c.SECUENCIAL) - 1), h] for i, h in enumerate(c.SECUENCIAL)],
        marker_line=dict(color="white", width=1), colorbar=dict(thickness=12, len=0.7, ticksuffix=sufijo, title=None),
        text=visibles.geo_nombre + np.where(visibles.aviso, f" {c.AVISO}", ""),
        customdata=np.stack([visibles.ee, visibles.cv], axis=-1),
        hovertemplate="<b>%{text}</b><br>%{z:,.1f}" + sufijo + "<br>EE %{customdata[0]:.2f} · CV %{customdata[1]:.1f} %<extra></extra>")
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      geo_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(bgcolor="white", font_color=c.TEXTO))
    c.mostrar(fig)
    st.caption("Tono más oscuro = valor más alto. Gris: estimación no publicable. "
               + ("En este indicador un valor alto es favorable." if sentido == "mayor_es_mejor" else
                  "En este indicador un valor alto es desfavorable." if sentido == "menor_es_mejor" else ""))

with col_rank:
    asc = sentido == "menor_es_mejor"
    orden = d.sort_values("valor", ascending=asc, na_position="last")
    fig_r = c.barras_h(orden, "geo_nombre", ind, c.AZUL, alto=max(620, 20 * len(orden) + 80),
                       linea_ref=(valor_foco, ctx["nombre"]))
    fig_r.update_layout(bargap=0.25)
    fig_r.update_yaxes(tickfont=dict(size=11, color=c.TEXTO))
    c.mostrar(fig_r)

if d.oculto.any():
    st.warning(f"{int(d.oculto.sum())} {ctx['sub_nombre']}(s) sin dato publicable (CV > 30 %): "
               + ", ".join(sorted(d[d.oculto].geo_nombre)))


def frente_al_total(fila: pd.Series) -> str:
    if fila.oculto or pd.isna(valor_foco) or sentido is None:
        return "—"
    dif = fila.valor - valor_foco
    if abs(dif) <= 1.645 * float(np.hypot(fila.ee, ee_foco)):
        return "Similar"
    return "Mejor" if (dif > 0) == (sentido == "mayor_es_mejor") else "Peor"


with st.expander("Tabla de datos", expanded=False):
    t = c.tabla_calidad(orden, ind, {"geo_nombre": ctx["sub_nombre"].capitalize()})
    t.insert(2, f"Frente a {ctx['nombre']}", [frente_al_total(f) for _, f in orden.iterrows()])
    t.insert(0, "Posición", range(1, len(t) + 1))
    st.dataframe(t, hide_index=True, use_container_width=True)
    st.caption(f"«Frente a {ctx['nombre']}» compara con el total; «Similar» significa que la diferencia no es "
               "significativa al 90 %. El orden pone primero el resultado más favorable cuando el indicador tiene sentido definido.")
c.leyenda_calidad()
c.nota_universo()
