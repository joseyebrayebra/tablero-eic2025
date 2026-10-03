import numpy as np
import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
datos = c.indicadores()
ref = c.referente(ctx)
IND = "asistencia_edad"
ETAPAS = [(3, 5, "Preescolar"), (6, 11, "Primaria"), (12, 14, "Secundaria"), (15, 17, "Media superior"), (18, 24, "Superior")]

st.title(f"Trayectoria por edad · {ctx['nombre']}")
st.markdown("Porcentaje de la población de cada edad que asiste a la escuela. La curva muestra en qué edad se sale del sistema.")

sub = c.serie(datos, IND, "edad", ctx["sub_nivel"])
sub = sub[sub.geo_id.str.startswith(ctx["sub_prefijo"])]
izq, der = st.columns([2, 1])
por_sexo = der.toggle("Separar por sexo", value=False)
extra = izq.multiselect("Agregar " + ctx["sub_nombre"] + " a la comparación", sorted(sub.geo_nombre.unique()),
                        max_selections=1 if ref else 2, disabled=por_sexo)


def curva(nivel: str, geo_id: str, sexo: str | None = None) -> pd.DataFrame:
    d = c.serie(datos, IND, "edad_sexo" if sexo else "edad", nivel, geo_id)
    if sexo:
        d = d[d.categoria.str.endswith(sexo)]
    return d.assign(edad=d.categoria.str[:2].astype(int)).sort_values("edad")


series = []  # (nombre, datos, color, guion)
if por_sexo:
    series = [("Mujeres", curva(ctx["nivel"], ctx["id"], "Mujeres"), c.AZUL, "solid"),
              ("Hombres", curva(ctx["nivel"], ctx["id"], "Hombres"), c.NARANJA, "solid")]
else:
    series.append((ctx["nombre"], curva(ctx["nivel"], ctx["id"]), c.AZUL, "solid"))
    if ref:
        series.append((ref["nombre"], curva(ref["nivel"], ref["id"]), c.NARANJA, "dash"))
    for nombre_, color in zip(extra, [c.AGUA, c.NARANJA]):
        gid = sub[sub.geo_nombre == nombre_].geo_id.iloc[0]
        series.append((nombre_, curva(ctx["sub_nivel"], gid), color, "dot"))

fig = c.base_fig(460, "Asiste a la escuela", "Edad (años cumplidos)")
for i, (ini, fin, etiqueta) in enumerate(ETAPAS):
    if i % 2 == 0:
        fig.add_vrect(x0=ini - 0.5, x1=fin + 0.5, fillcolor=c.REJILLA, opacity=0.45, line_width=0, layer="below")
    fig.add_annotation(x=(ini + fin) / 2, y=104, text=etiqueta, showarrow=False, font=dict(size=11, color=c.TEXTO_2))

principal = series[0][1]
fig.add_scatter(x=np.r_[principal.edad, principal.edad[::-1]], y=np.r_[principal.ls, principal.li[::-1]], fill="toself",
                fillcolor="rgba(42,120,214,0.15)", line=dict(width=0), hoverinfo="skip", showlegend=False)
for nombre_, d, color, guion in series:
    fig.add_scatter(
        x=d.edad, y=d.valor, name=nombre_, mode="lines+markers", connectgaps=False,
        line=dict(color=color, width=2, dash=guion),
        marker=dict(size=8, color=["white" if a else color for a in d.aviso], line=dict(color=color, width=2)),
        customdata=np.stack([d.ee, d.cv, np.where(d.aviso, f" {c.AVISO} calidad media", "")], axis=-1),
        hovertemplate=nombre_ + ": <b>%{y:.1f} %</b>%{customdata[2]} (EE %{customdata[0]:.1f})<extra></extra>")
fig.update_layout(hovermode="x unified")
fig.update_yaxes(range=[0, 108], ticksuffix=" %")
fig.update_xaxes(dtick=1, showgrid=False)
c.mostrar(fig)
st.caption("Banda azul: intervalo al 90 % de la primera serie. Marcador hueco: calidad media. "
           "Los puntos de calidad baja no se dibujan.")

p = principal.dropna(subset=["valor"]).set_index("edad").valor
if len(p) > 2:
    caida = p.diff().dropna()
    edad_caida = int(caida.idxmin())
    bajo_90 = p[(p.index >= 6) & (p < 90)]
    k1, k2, k3 = st.columns(3)
    k1.metric("Mayor caída entre edades consecutivas", f"{edad_caida - 1} → {edad_caida} años", f"{caida.min():.1f} pp")
    k2.metric("Primera edad con asistencia menor a 90 %", f"{int(bajo_90.index.min())} años" if len(bajo_90) else "—")
    k3.metric(f"Asistencia a los 17 años ({series[0][0]})", f"{p.get(17, float('nan')):.1f} %")

with st.expander("Tabla de datos"):
    tabla = pd.concat([c.tabla_calidad(d, IND, {"edad": "Edad"}).assign(Serie=n) for n, d, _, _ in series])
    st.dataframe(tabla[["Serie", "Edad", "Valor", "Error estándar", "CV (%)", "n muestral", "Calidad"]],
                 hide_index=True, use_container_width=True)
c.leyenda_calidad()
c.nota_universo()
