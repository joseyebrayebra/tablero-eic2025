"""Página de factores asociados, compartida por el modelo de estados pares y el nacional."""

import textwrap

import numpy as np
import pandas as pd
import streamlit as st

import comun as c



def render(sufijo: str, titulo: str, ambito: str) -> None:
    ctx = c.contexto()
    fac = c.factores(sufijo)
    cat = c.catalogo()
    reg = c.tabla_csv(f"factores_regresiones{sufijo}.csv")
    desv = c.tabla_csv(f"factores_desviacion_positiva{sufijo}.csv")
    FACTORES = [k for k in cat.index[cat.tema == "Factores asociados"]]
    RESULTADOS = {"asistencia_15_17": "Asistencia de 15 a 17 años", "media_superior_completa_20_24": "Media superior completa, 20 a 24 años"}

    st.title(titulo)
    st.caption(f"Ámbito de comparación: {ambito}.")
    st.warning("**Asociaciones, no causalidad.** Esta página describe qué condiciones aparecen junto a mejores o peores "
               "resultados en 2025. No demuestra que cambiar un factor cambie el resultado: hay variables no observadas, "
               "la relación puede ir en sentido inverso y los modelos municipales no describen a las personas.", icon="⚠️")
    if ctx["nivel"] == "nacional":
        st.info("Esta página muestra siempre los municipios de Guanajuato; el ámbito define contra quién se comparan.")

    t1, t2, t3, t4 = st.tabs(["Factores por municipio", "Escolaridad del hogar", "Relación con resultados", "Desviación positiva"])

    with t1:
        ind = st.selectbox("Factor", FACTORES, format_func=c.nombre)
        d = c.serie(fac, ind, "total", "municipio")
        d = d[d.geo_id.str.startswith(c.ENTIDAD_FOCO)].sort_values("valor", ascending=False, na_position="last")
        est = c.serie(fac, ind, "total", "entidad", c.ENTIDAD_FOCO)
        c.mostrar(c.barras_h(d, "geo_nombre", ind, c.AZUL, alto=max(520, 20 * len(d) + 80),
                             linea_ref=(est.valor.iloc[0], c.NOMBRE_FOCO) if len(est) else None))
        if d.oculto.any():
            st.warning(f"{int(d.oculto.sum())} municipio(s) sin dato publicable (CV > 30 %): " + ", ".join(sorted(d[d.oculto].geo_nombre)))
        st.caption(f"Unidad de análisis: {cat.unidad_analisis[ind]}. Los factores de hogar se estiman sobre hogares.")
        with st.expander("Tabla de datos"):
            st.dataframe(c.tabla_calidad(d, ind, {"geo_nombre": "Municipio"}), hide_index=True, use_container_width=True)

    with t2:
        st.markdown("Asistencia a la escuela de jóvenes de 15 a 17 años según la escolaridad más alta entre las personas "
                    "de 18 años y más de su hogar.")
        ents = c.serie(fac, "asistencia_15_17", "escolaridad_max_hogar", "entidad")
        ents = ents[~ents.categoria.str.startswith("9")]
        ents["grupo"] = ents.categoria.str[2:]
        g = ents[ents.geo_id == c.ENTIDAD_FOCO].sort_values("categoria")
        fig = c.barras_h(g, "grupo", "asistencia_15_17", c.AZUL)
        otros = ents[(ents.geo_id != c.ENTIDAD_FOCO) & ~ents.oculto]
        fig.add_scatter(y=otros.grupo, x=otros.valor, mode="markers", name="Otras entidades (cada una)",
                        marker=dict(symbol="line-ns", size=14, line=dict(color=c.NARANJA, width=2)),
                        text=otros.geo_nombre, hovertemplate="%{text}: <b>%{x:.1f} %</b><extra></extra>")
        fig.update_layout(showlegend=True)
        fig.update_xaxes(range=[0, 100])
        c.mostrar(fig)
        m = reg[(reg.analisis == "microdatos_asistencia_15_17") & (reg.ambito == c.NOMBRE_FOCO)]
        st.markdown("**Diferencia frente a hogares con secundaria completa** (puntos porcentuales, microdatos de Guanajuato)")
        piv = m.pivot(index="termino", columns="modelo", values="coef").round(1)
        piv.index = piv.index.str[2:]
        st.dataframe(piv.rename_axis("Escolaridad máxima del hogar"), use_container_width=True)
        st.caption(f"Modelo lineal de probabilidad ponderado, errores agrupados por UPM, n = {int(m.n.max()):,}. "
                   "La brecha casi no cambia al controlar por tamaño de localidad, sexo y edad.")
        with st.expander("Tabla de datos"):
            st.dataframe(c.tabla_calidad(ents.sort_values(["geo_nombre", "categoria"]), "asistencia_15_17",
                                         {"geo_nombre": "Entidad", "grupo": "Escolaridad máxima del hogar"}),
                         hide_index=True, use_container_width=True)

    with t3:
        res = st.radio("Resultado educativo", list(RESULTADOS), format_func=RESULTADOS.get, horizontal=True)
        m = reg[(reg.analisis == "municipal_por_factor") & (reg.resultado == res)].copy()
        m["factor"] = m.termino.map(lambda k: "<br>".join(textwrap.wrap(c.nombre(k), 34)))
        orden = m[m.modelo == "con tamaño de localidad"].sort_values("coef").factor.tolist()
        fig = c.base_fig(60 * len(orden) + 110, "", "Cambio en el resultado por cada desviación estándar del factor (pp)")
        for modelo, color, simbolo in [("sin control", c.NEUTRO, "circle-open"), ("con tamaño de localidad", c.AZUL, "circle")]:
            s = m[m.modelo == modelo].set_index("factor").loc[orden].reset_index()
            fig.add_scatter(
                y=s.factor, x=s.coef, mode="markers", name=modelo.capitalize(),
                marker=dict(symbol=simbolo, size=11, color=color, line=dict(color=color, width=2)),
                error_x=dict(type="data", symmetric=False, array=s.ls90 - s.coef, arrayminus=s.coef - s.li90, color=color, thickness=1.5, width=0),
                customdata=np.stack([s.p, s.n], axis=-1),
                hovertemplate=modelo.capitalize() + ": <b>%{x:+.1f} pp</b> (p = %{customdata[0]:.3f}, %{customdata[1]} municipios)<extra>%{y}</extra>")
        fig.add_vline(x=0, line_color=c.TEXTO_2, line_width=1)
        fig.update_yaxes(showgrid=False, tickfont=dict(color=c.TEXTO, size=12))
        c.mostrar(fig)
        st.caption(f"Un modelo por factor ({ambito.lower()}), con efectos fijos de entidad y "
                   "errores robustos. Barras: intervalo al 90 %; si cruza el cero, no hay asociación distinguible. El control por "
                   "tamaño de localidad compara municipios con la misma distribución de población por tamaño de localidad.")
        with st.expander("Tabla de datos"):
            st.dataframe(m[["factor", "modelo", "coef", "ee", "li90", "ls90", "p", "n", "r2"]].round(3)
                         .rename(columns={"factor": "Factor", "modelo": "Modelo", "coef": "Coeficiente (pp)", "ee": "EE",
                                          "li90": "LI 90 %", "ls90": "LS 90 %", "n": "Municipios", "r2": "R²"}),
                         hide_index=True, use_container_width=True)

    with t4:
        res = st.radio("Resultado educativo ", list(RESULTADOS), format_func=RESULTADOS.get, horizontal=True)
        st.markdown("Diferencia entre el resultado observado y el esperado por las condiciones del municipio (internet, "
                    "computadora, hacinamiento, leña, remesas, programas de gobierno, inseguridad alimentaria y tamaño de localidad).")
        g = desv[desv.resultado == res].sort_values("residuo_base", ascending=False)
        negativa = g.negativa_base & g.negativa_ampliado
        estado = np.where(g.desviacion_positiva_robusta, "▲ Desviación positiva robusta",
                          np.where(negativa, "▼ Por debajo de lo esperado", "Dentro de lo esperado"))
        fig = c.base_fig(20 * len(g) + 110, "", "Observado menos esperado (puntos porcentuales)")
        for etiqueta, color in [("▲ Desviación positiva robusta", c.BUENO), ("Dentro de lo esperado", c.NEUTRO_CLARO),
                                ("▼ Por debajo de lo esperado", c.CRITICO)]:
            s = g[estado == etiqueta]
            fig.add_bar(y=s.geo_nombre, x=s.residuo_base, orientation="h", name=etiqueta, marker_color=color, marker_line_width=0,
                        customdata=np.stack([s.observado, s.esperado_base, s.residuo_ampliado], axis=-1),
                        hovertemplate="<b>%{y}</b><br>Observado %{customdata[0]:.1f} % · esperado %{customdata[1]:.1f} %"
                                      "<br>Diferencia %{x:+.1f} pp (con escolaridad adulta: %{customdata[2]:+.1f})<extra></extra>")
        fig.add_vline(x=0, line_color=c.TEXTO_2, line_width=1)
        fig.update_layout(bargap=0.25)
        fig.update_yaxes(autorange="reversed", showgrid=False, categoryorder="array", categoryarray=g.geo_nombre.tolist(),
                         tickfont=dict(size=11, color=c.TEXTO))
        c.mostrar(fig)
        st.caption("Desviación positiva robusta: residuo estandarizado de 1 o más y mayor que el margen de error muestral, tanto en "
                   "el modelo base como al agregar la escolaridad promedio de los adultos. Es un punto de partida para revisar qué "
                   "se hace distinto en esos municipios, no un ranking de desempeño.")
        with st.expander("Tabla de datos"):
            st.dataframe(g.assign(Clasificación=estado)[["geo_nombre", "observado", "ee_observado", "esperado_base", "residuo_base",
                                                         "residuo_ampliado", "Clasificación"]].round(1)
                         .rename(columns={"geo_nombre": "Municipio", "observado": "Observado (%)", "ee_observado": "EE observado",
                                          "esperado_base": "Esperado (%)", "residuo_base": "Diferencia (pp)",
                                          "residuo_ampliado": "Diferencia con escolaridad adulta (pp)"}),
                         hide_index=True, use_container_width=True)

    c.leyenda_calidad()
    c.nota_universo()
