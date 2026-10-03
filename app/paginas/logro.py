import numpy as np
import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
datos = c.indicadores()
ref = c.referente(ctx)
COHORTES = ["65+", "55-64", "45-54", "35-44", "25-34", "20-24", "15-19"]  # de la generación mayor a la más joven
LOGROS = {  # indicador: (etiqueta, cohortes que ya tuvieron edad para alcanzarlo, color)
    "logro_basica_completa": ("Básica completa", COHORTES, c.AZUL),
    "logro_media_superior_completa": ("Media superior completa", COHORTES[:-1], c.NARANJA),
    "logro_superior": ("Educación superior", COHORTES[:-2], c.AGUA),
}
NIVELES = {"nivel_sin_escolaridad_15mas": "Sin escolaridad", "nivel_basica_15mas": "Básica",
           "nivel_media_superior_15mas": "Media superior", "nivel_superior_15mas": "Superior"}

st.title(f"Logro por nivel y cohorte · {ctx['nombre']}")
st.markdown("Cada cohorte de edad muestra hasta dónde llegó su generación. Leer de izquierda (mayores) a derecha "
            "(jóvenes) muestra el avance entre generaciones.")


def por_cohorte(indicador: str, nivel: str, geo_id: str, sexo: str | None = None) -> pd.DataFrame:
    d = c.serie(datos, indicador, "cohorte_sexo" if sexo else "cohorte", nivel, geo_id)
    if sexo:
        d = d[d.categoria.str.endswith(sexo)].assign(categoria=lambda x: x.categoria.str.split("|").str[0])
    validas = LOGROS[indicador][1]
    return d[d.categoria.isin(validas)].set_index("categoria").reindex(validas).reset_index()


def trazo(fig, d: pd.DataFrame, nombre_: str, color: str, guion: str = "solid") -> None:
    fig.add_scatter(
        x=d.categoria, y=d.valor, name=nombre_, mode="lines+markers", line=dict(color=color, width=2, dash=guion),
        marker=dict(size=9, color=["white" if a else color for a in d.aviso.fillna(False)], line=dict(color=color, width=2)),
        error_y=dict(type="data", array=1.645 * d.ee, color=color, thickness=1, width=0),
        customdata=np.stack([d.ee, d.n_muestral], axis=-1),
        hovertemplate=nombre_ + ": <b>%{y:.1f} %</b> (EE %{customdata[0]:.1f}, n = %{customdata[1]:,})<extra></extra>")


modo = st.radio("Comparar", ["Los tres niveles", "Hombres y mujeres", f"Con {ref['nombre']}" if ref else "Con referente"],
                horizontal=True, label_visibility="collapsed")
fig = c.base_fig(440, "Población de la cohorte", "Cohorte de edad en 2025")
tablas = []
if modo == "Los tres niveles":
    for ind, (etiqueta, _, color) in LOGROS.items():
        d = por_cohorte(ind, ctx["nivel"], ctx["id"])
        trazo(fig, d, etiqueta, color)
        tablas.append(c.tabla_calidad(d, ind, {"categoria": "Cohorte"}).assign(Serie=etiqueta))
else:
    ind = st.selectbox("Nivel de logro", list(LOGROS), format_func=lambda k: LOGROS[k][0], index=1)
    if modo == "Hombres y mujeres":
        pares_ = [("Mujeres", por_cohorte(ind, ctx["nivel"], ctx["id"], "Mujeres"), c.AZUL, "solid"),
                  ("Hombres", por_cohorte(ind, ctx["nivel"], ctx["id"], "Hombres"), c.NARANJA, "solid")]
    else:
        pares_ = [(ctx["nombre"], por_cohorte(ind, ctx["nivel"], ctx["id"]), c.AZUL, "solid")]
        if ref:
            pares_.append((ref["nombre"], por_cohorte(ind, ref["nivel"], ref["id"]), c.NARANJA, "dash"))
    for nombre_, d, color, guion in pares_:
        trazo(fig, d, nombre_, color, guion)
        tablas.append(c.tabla_calidad(d, ind, {"categoria": "Cohorte"}).assign(Serie=nombre_))
fig.update_layout(hovermode="x unified")
fig.update_yaxes(range=[0, 100], ticksuffix=" %")
fig.update_xaxes(showgrid=False, categoryorder="array", categoryarray=COHORTES)
c.mostrar(fig)
st.caption("Media superior completa se muestra desde los 20 años y educación superior desde los 25, cuando la "
           "cohorte ya tuvo edad para alcanzarlas. Las personas se miden donde viven hoy, no donde estudiaron.")

st.subheader("Último nivel de escolaridad de la población de 15 años y más")
geos = [(ctx["nivel"], ctx["id"], ctx["nombre"])] + ([(ref["nivel"], ref["id"], ref["nombre"])] if ref else [])
fig2 = c.base_fig(120 + 60 * len(geos))
filas_nivel = []
for (ind, etiqueta), color in zip(NIVELES.items(), c.ORDINAL):
    vals = [c.serie(datos, ind, "total", n, g) for n, g, _ in geos]
    x = [v.valor.iloc[0] if len(v) else np.nan for v in vals]
    fig2.add_bar(y=[n for *_, n in geos], x=x, name=etiqueta, orientation="h", marker_color=color,
                 marker_line=dict(color="white", width=2), text=[f"{v:.0f} %" for v in x], textposition="inside",
                 insidetextfont=dict(color="white" if color != c.ORDINAL[0] else c.TEXTO),
                 hovertemplate=etiqueta + ": <b>%{x:.1f} %</b><extra>%{y}</extra>")
    for (_, _, nombre_geo), v in zip(geos, vals):
        if len(v):
            filas_nivel.append(c.tabla_calidad(v, ind, {}).assign(Geografía=nombre_geo, Nivel=etiqueta))
fig2.update_layout(barmode="stack", bargap=0.4, legend_traceorder="normal")
fig2.update_xaxes(range=[0, 100], ticksuffix=" %", showgrid=False)
fig2.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=c.TEXTO))
c.mostrar(fig2)
st.caption("Agrupación de INEGI: básica incluye preescolar, primaria, secundaria y técnicos con primaria; media superior "
           "incluye bachillerato, técnicos con secundaria y normal básica. La diferencia a 100 % es no especificado.")

with st.expander("Tablas de datos"):
    st.dataframe(pd.concat(tablas)[["Serie", "Cohorte", "Valor", "Error estándar", "CV (%)", "n muestral", "Calidad"]],
                 hide_index=True, use_container_width=True)
    if filas_nivel:
        st.dataframe(pd.concat(filas_nivel)[["Geografía", "Nivel", "Valor", "Error estándar", "CV (%)", "n muestral", "Calidad"]],
                     hide_index=True, use_container_width=True)
c.leyenda_calidad()
c.nota_universo()
