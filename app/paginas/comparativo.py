import numpy as np
import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
conf = c.semaforo_config()
datos = c.indicadores()
cat = c.catalogo()

st.title("Comparativo · Guanajuato, nación y estados pares")
hay_nacional = (datos.geo_nivel == "nacional").any()
if not hay_nacional:
    st.info("Aún no hay dato nacional (falta procesar el archivo nacional de microdatos). La comparación es con los "
            "estados pares: Aguascalientes, Jalisco, Michoacán, Querétaro y San Luis Potosí.")

base = datos[datos.geo_nivel.isin(["entidad", "grupo", "nacional"]) & (datos.desagregacion == "total")]
opciones = [k for k in cat.index if k in set(base.indicador) and cat.tipo[k] != "total"]
ind = st.selectbox("Indicador", opciones, format_func=c.nombre,
                   index=opciones.index("asistencia_15_17") if "asistencia_15_17" in opciones else 0)
sentido = c.sentido_de(ind, conf)

todas = st.toggle("Mostrar las 32 entidades", value=False, disabled=not hay_nacional)
d = c.serie(datos, ind, "total")
d = d[d.geo_nivel.isin(["entidad", "grupo", "nacional"])].copy()
ranking = d[(d.geo_nivel == "entidad") & ~d.oculto]
if not todas:
    d = d[(d.geo_nivel != "entidad") | d.geo_id.isin(c.COMPARADAS)]
d["etiqueta"] = np.where(d.geo_nivel == "grupo", "Estados pares (conjunto)", d.geo_nombre)
d = d.sort_values("valor", ascending=(sentido == "menor_es_mejor"), na_position="last")
colores = [c.AZUL if g == c.ENTIDAD_FOCO else c.TEXTO_2 if n in ("grupo", "nacional") else c.NEUTRO_CLARO
           for g, n in zip(d.geo_id, d.geo_nivel)]
c.mostrar(c.barras_h(d, "etiqueta", ind, colores))
st.caption("Azul: Guanajuato. Gris oscuro: agregados (nación, estados pares en conjunto). Gris claro: cada entidad. "
           + ("Ordenado del resultado más favorable al menos favorable." if sentido else ""))

gto = d[d.geo_id == c.ENTIDAD_FOCO]
ents = ranking
if len(gto) and not gto.oculto.iloc[0]:
    g = gto.iloc[0]
    cols = st.columns(3)
    cols[0].metric("Guanajuato", c.fmt(g.valor, ind, g.aviso))
    if sentido:
        pos = int((ents.valor > g.valor).sum() + 1) if sentido == "mayor_es_mejor" else int((ents.valor < g.valor).sum() + 1)
        cols[1].metric(f"Posición entre {len(ents)} entidades", f"{pos} de {len(ents)}")
    for nivel, nombre_ in [("nacional", "nación"), ("grupo", "estados pares")]:
        r = d[d.geo_nivel == nivel]
        if len(r):
            dif, ee_d = g.valor - r.valor.iloc[0], float(np.hypot(g.ee, r.ee.iloc[0]))
            cols[2].metric(f"Diferencia con {nombre_}", c.fmt(dif, ind, signo=True),
                           "significativa al 90 %" if abs(dif) > 1.645 * ee_d else "no significativa", delta_color="off", delta_arrow="off")
            break

st.subheader("Todos los indicadores del resumen")
filas = []
for regla in conf["indicadores"]:
    clave = regla["clave"]
    s = c.serie(datos, clave, "total")
    s = s[s.geo_nivel.isin(["entidad", "grupo", "nacional"])]
    if s.empty:
        continue
    fila = {"Indicador": c.nombre(clave)}
    e = s[(s.geo_nivel == "entidad") & ~s.oculto]
    for _, r in s[(s.geo_nivel != "entidad") | s.geo_id.isin(c.COMPARADAS)].sort_values(["geo_nivel", "geo_nombre"]).iterrows():
        col = "Estados pares (conjunto)" if r.geo_nivel == "grupo" else r.geo_nombre
        fila[col] = c.fmt(r.valor, clave, r.aviso, r.oculto)
    g = e[e.geo_id == c.ENTIDAD_FOCO]
    if len(g):
        mejor = (e.valor > g.valor.iloc[0]).sum() if regla["sentido"] == "mayor_es_mejor" else (e.valor < g.valor.iloc[0]).sum()
        fila["Posición de Guanajuato"] = f"{int(mejor) + 1} de {len(e)}"
    filas.append(fila)
tabla = pd.DataFrame(filas)
primeras = ["Indicador", "Guanajuato", "Posición de Guanajuato", "Nacional", "Estados pares (conjunto)"]
st.dataframe(tabla[[x for x in primeras if x in tabla] + [x for x in tabla if x not in primeras]],
             hide_index=True, use_container_width=True)
st.caption("Posición 1 = resultado más favorable entre todas las entidades con dato. Diferencias pequeñas entre entidades "
           "pueden no ser estadísticamente significativas.")

with st.expander("Tabla de datos del indicador seleccionado"):
    st.dataframe(c.tabla_calidad(d, ind, {"etiqueta": "Geografía"}), hide_index=True, use_container_width=True)
c.leyenda_calidad()
c.nota_universo()
