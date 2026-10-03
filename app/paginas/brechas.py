import numpy as np
import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
datos = c.indicadores()
cat = c.catalogo()
ref = c.referente(ctx)
DESAG = {"sexo": "Sexo", "tam_localidad": "Tamaño de localidad", "lengua_indigena": "Habla de lengua indígena",
         "autoadscripcion_indigena": "Autoadscripción indígena", "discapacidad": "Discapacidad"}

st.title(f"Brechas · {ctx['nombre']}")
st.markdown("Compara un mismo indicador entre grupos de población. Una brecha solo se señala cuando la diferencia "
            "es estadísticamente significativa al 90 %.")

propios = datos[(datos.geo_nivel == ctx["nivel"]) & (datos.geo_id == ctx["id"]) & datos.desagregacion.isin(DESAG)]
opciones = [k for k in cat.index if k in set(propios.indicador) and cat.tipo[k] != "total"]
izq, der = st.columns(2)
ind = izq.selectbox("Indicador", opciones, format_func=c.nombre,
                    index=opciones.index("asistencia_15_17") if "asistencia_15_17" in opciones else 0)
disponibles = [d for d in DESAG if d in set(propios[propios.indicador == ind].desagregacion)]
desag = der.selectbox("Grupos", disponibles, format_func=DESAG.get)

d = c.serie(datos, ind, desag, ctx["nivel"], ctx["id"]).sort_values("categoria")
d["grupo"] = d.categoria.str.replace(r"^\d ", "", regex=True)
total = c.serie(datos, ind, "total", ctx["nivel"], ctx["id"])
linea = (total.valor.iloc[0], f"Total {ctx['nombre']}") if len(total) else None
fig = c.barras_h(d, "grupo", ind, c.AZUL, linea_ref=linea)
if ref:
    r = c.serie(datos, ind, desag, ref["nivel"], ref["id"]).sort_values("categoria")
    r["grupo"] = r.categoria.str.replace(r"^\d ", "", regex=True)
    r = r[~r.oculto]
    fig.add_scatter(y=r.grupo, x=r.valor, mode="markers", name=ref["nombre"],
                    marker=dict(symbol="diamond", size=11, color=c.NARANJA, line=dict(color="white", width=2)),
                    hovertemplate=ref["nombre"] + ": <b>%{x:.1f}</b><extra>%{y}</extra>")
    fig.update_layout(showlegend=True)
c.mostrar(fig)
st.caption(f"Barras: {ctx['nombre']}." + (f" Rombos: {ref['nombre']}." if ref else "") + " Línea punteada: total.")

v = d[~d.oculto]
if len(v) >= 2:
    alto, bajo = v.loc[v.valor.idxmax()], v.loc[v.valor.idxmin()]
    brecha, ee_b = alto.valor - bajo.valor, float(np.hypot(alto.ee, bajo.ee))
    signif = abs(brecha) > 1.645 * ee_b
    k1, k2 = st.columns(2)
    k1.metric(f"Brecha entre «{alto.grupo}» y «{bajo.grupo}»", c.fmt(brecha, ind, signo=True).lstrip("+"))
    k2.metric("¿Es significativa al 90 %?", "Sí" if signif else "No",
              f"margen de error ±{1.645 * ee_b:.1f}", delta_color="off", delta_arrow="off")
if d.oculto.any():
    st.warning("Grupos sin dato publicable (CV > 30 %): " + ", ".join(d[d.oculto].grupo))

with st.expander("Tabla de datos"):
    st.dataframe(c.tabla_calidad(d, ind, {"grupo": "Grupo"}), hide_index=True, use_container_width=True)
c.leyenda_calidad()
c.nota_universo()
