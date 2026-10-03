import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
conf = c.semaforo_config()
datos = c.indicadores()
cat = c.catalogo()
ref = c.referente(ctx, conf)
anio, anio_base = conf["anio_actual"], conf["anio_base"]
hay_base = anio_base is not None and bool((datos.anio == anio_base).any())

st.title(f"Resumen ejecutivo · {ctx['nombre']}")
partes = [f"Nivel frente a **{ref['nombre']}**" if ref else "Sin referente disponible para el nivel"]
if anio_base is not None:
    partes.append(f"tendencia frente a **{anio_base}**" if hay_base else f"sin datos de {anio_base} para la tendencia")
st.markdown(" · ".join(partes))
if anio_base is not None and not hay_base:
    st.info(f"El semáforo combina nivel y tendencia, pero no hay estimaciones de {anio_base} en "
            "`data/output/indicadores.parquet`; el color depende solo del nivel.")

ETIQUETA_NIVEL = {"mejor": "Mejor que el referente", "similar": "Similar al referente", "peor": "Peor que el referente",
                  "sin_dato": "Sin referente"}
ETIQUETA_TEND = {"mejora": f"Mejora vs {anio_base}", "estable": f"Estable vs {anio_base}",
                 "empeora": f"Empeora vs {anio_base}", "sin_dato": f"Sin dato {anio_base}" if anio_base else ""}

def fila(indicador: str, nivel: str, geo_id: str, anio_: int) -> pd.Series | None:
    s = c.serie(datos, indicador, "total", nivel, geo_id, anio_)
    return s.iloc[0] if len(s) else None


resultados = []
for regla in conf["indicadores"]:
    clave = regla["clave"]
    actual = fila(clave, ctx["nivel"], ctx["id"], anio)
    if actual is None:
        continue
    r_ref = fila(clave, ref["nivel"], ref["id"], anio) if ref else None
    r_base = fila(clave, ctx["nivel"], ctx["id"], anio_base) if hay_base else None
    tipo = cat.tipo.get(clave, "porcentaje")
    ev = c.evaluar(actual, r_ref, r_base, regla, conf, tipo)
    if actual.oculto:
        ev["color"] = "gris"
    resultados.append({"clave": clave, "actual": actual, "ref": r_ref, "base": r_base, **ev})

conteo = pd.Series([r["color"] for r in resultados]).value_counts()
cols = st.columns(len(conf["colores"]))
for col, (color, estilo) in zip(cols, conf["colores"].items()):
    col.markdown(
        f"<div style='border-left:6px solid {estilo['hex']};padding:2px 12px'>"
        f"<div style='font-size:2rem;font-weight:600;color:{c.TEXTO}'>{conteo.get(color, 0)}</div>"
        f"<div style='color:{c.TEXTO_2}'>{estilo['icono']} {estilo['etiqueta']}</div></div>", unsafe_allow_html=True)
st.write("")

for i in range(0, len(resultados), 3):
    for col, r in zip(st.columns(3), resultados[i:i + 3]):
        estilo = conf["colores"][r["color"]]
        a = r["actual"]
        with col.container(border=True):
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;gap:8px'>"
                f"<span style='color:{c.TEXTO_2};font-size:0.9rem'>{c.nombre(r['clave'])}</span>"
                f"<span style='white-space:nowrap;color:{c.TEXTO};font-size:0.85rem'>"
                f"<span style='color:{estilo['hex']}'>{estilo['icono']}</span> {estilo['etiqueta']}</span></div>"
                f"<div style='font-size:2rem;font-weight:600;color:{c.TEXTO};border-left:6px solid {estilo['hex']};"
                f"padding-left:10px;margin:6px 0'>{c.fmt(a.valor, r['clave'], a.aviso, a.oculto)}</div>",
                unsafe_allow_html=True)
            if a.oculto:
                st.caption("Estimación de calidad baja (CV > 30 %): no se publica.")
                continue
            if r["ref"] is not None:
                st.caption(f"{ref['nombre']}: {c.fmt(r['ref'].valor, r['clave'], r['ref'].aviso, r['ref'].oculto)} · "
                           f"diferencia {c.fmt(r['dif_nivel'], r['clave'], signo=True)}")
            st.caption(" · ".join(x for x in (ETIQUETA_NIVEL[r['nivel']], ETIQUETA_TEND[r['tendencia']]) if x))

c.leyenda_calidad()

with st.expander("Tabla y reglas del semáforo"):
    st.dataframe(pd.DataFrame([{
        "Indicador": c.nombre(r["clave"]),
        ctx["nombre"]: c.fmt(r["actual"].valor, r["clave"], r["actual"].aviso, r["actual"].oculto),
        (ref["nombre"] if ref else "Referente"): c.fmt(r["ref"].valor, r["clave"], r["ref"].aviso, r["ref"].oculto) if r["ref"] is not None else "—",
        "Diferencia": c.fmt(r["dif_nivel"], r["clave"], signo=True) if not pd.isna(r["dif_nivel"]) else "—",
        "Nivel": ETIQUETA_NIVEL[r["nivel"]], **({"Tendencia": ETIQUETA_TEND[r["tendencia"]]} if anio_base else {}),
        "Semáforo": f"{conf['colores'][r['color']]['icono']} {conf['colores'][r['color']]['etiqueta']}",
        "CV (%)": round(r["actual"].cv, 1), "n muestral": int(r["actual"].n_muestral),
    } for r in resultados]), hide_index=True, use_container_width=True)
    st.markdown(
        f"Las reglas viven en `config/semaforo.yaml`. Una diferencia cuenta solo si supera la tolerancia "
        f"({conf['tolerancia']['porcentaje']} puntos porcentuales; {conf['tolerancia']['media']} en promedios)"
        + (" y es estadísticamente significativa al 90 %." if conf.get("exigir_significancia") else "."))
    st.dataframe(pd.DataFrame(conf["reglas"]).rename(columns={"nivel": "Nivel", "tendencia": "Tendencia", "color": "Color"}),
                 hide_index=True)

c.nota_universo()
