import numpy as np
import pandas as pd
import streamlit as st

import comun as c

ctx = c.contexto()
conf = c.semaforo_config()
datos = c.indicadores()
cat = c.catalogo()
TEMAS = ["Asistencia escolar", "Escolaridad y rezago", "Acceso y traslado"]  # solo educación

st.title("Ficha educativa · consulta rápida")
st.markdown("Todos los indicadores educativos de un territorio en una sola vista. Elige el territorio y, si quieres, "
            "filtra por palabra.")

sub = datos[(datos.geo_nivel == ctx["sub_nivel"]) & datos.geo_id.str.startswith(ctx["sub_prefijo"])]
opciones = {ctx["id"]: f"{ctx['nombre']} (total)"} | dict(sub[["geo_id", "geo_nombre"]].drop_duplicates().sort_values("geo_nombre").values)
izq, der = st.columns([2, 1])
geo_id = izq.selectbox("Territorio", list(opciones), format_func=opciones.get)
buscar = der.text_input("Buscar indicador", placeholder="por ejemplo: asistencia, secundaria, traslado")

es_total = geo_id == ctx["id"]
nivel = ctx["nivel"] if es_total else ctx["sub_nivel"]
# Referente: el total del ámbito para sus partes; la nación para una entidad; ninguno para la nación
if not es_total:
    ref = {"nivel": ctx["nivel"], "id": ctx["id"], "nombre": ctx["nombre"]}
else:
    ref = c.referente(ctx, conf)
hermanos_nivel = nivel if nivel != "nacional" else None

propios = datos[(datos.geo_nivel == nivel) & (datos.geo_id == geo_id) & (datos.desagregacion == "total")]
claves = [k for k in cat.index if cat.tema[k] in TEMAS and k in set(propios.indicador)]
if buscar:
    claves = [k for k in claves if buscar.lower() in c.nombre(k).lower()]

filas = []
for k in claves:
    a = c.serie(datos, k, "total", nivel, geo_id).iloc[0]
    r = c.serie(datos, k, "total", ref["nivel"], ref["id"]) if ref else pd.DataFrame()
    r = r.iloc[0] if len(r) else None
    sentido = c.sentido_de(k, conf)
    posicion = "—"
    if hermanos_nivel and sentido and not a.oculto and cat.tipo[k] != "total":
        h = c.serie(datos, k, "total", hermanos_nivel)
        h = h[h.geo_id.str.startswith(ctx["sub_prefijo"] if nivel == "municipio" else "") & ~h.oculto]
        mejores = (h.valor > a.valor).sum() if sentido == "mayor_es_mejor" else (h.valor < a.valor).sum()
        posicion = f"{int(mejores) + 1} de {len(h)}"
    dif, frente = np.nan, "—"
    if r is not None and not a.oculto and not r.oculto and cat.tipo[k] != "total":
        dif = a.valor - r.valor
        if abs(dif) <= 1.645 * float(np.hypot(a.ee, r.ee)):
            frente = "Similar"
        elif sentido:
            frente = "Mejor" if (dif > 0) == (sentido == "mayor_es_mejor") else "Peor"
        else:
            frente = "Mayor" if dif > 0 else "Menor"
    filas.append({
        "tema": cat.tema[k], "tipo": cat.tipo[k], "Indicador": c.nombre(k),
        "Valor": c.fmt(a.valor, k, a.aviso, a.oculto),
        (ref["nombre"] if ref else "Referente"): c.fmt(r.valor, k, r.aviso, r.oculto) if r is not None and cat.tipo[k] != "total" else "—",
        "Diferencia": c.fmt(dif, k, signo=True) if not pd.isna(dif) else "—",
        "Frente al referente": frente, "Posición": posicion,
        "Error estándar": None if a.oculto else round(a.ee, 2), "CV (%)": round(a.cv, 1) if not pd.isna(a.cv) else None,
        "n muestral": int(a.n_muestral), "Calidad": a.calidad if isinstance(a.calidad, str) else "—",
    })
ficha = pd.DataFrame(filas)

st.subheader(opciones[geo_id])
if ficha.empty:
    st.info("Ningún indicador coincide con la búsqueda.")
else:
    magnitudes = ficha[ficha.tipo == "total"]
    if len(magnitudes):
        st.markdown("**Magnitudes (número de personas)**")
        st.dataframe(magnitudes[["Indicador", "Valor", "Calidad"]], hide_index=True, use_container_width=True)
    visibles = ["Indicador", "Valor"] + ([ref["nombre"], "Diferencia", "Frente al referente"] if ref else []) + ["Posición", "Calidad"]
    for tema in TEMAS:
        t = ficha[(ficha.tema == tema) & (ficha.tipo != "total")]
        if len(t):
            st.markdown(f"**{tema}**")
            st.dataframe(t[visibles], hide_index=True, use_container_width=True)
    st.download_button("Descargar esta ficha (CSV)", ficha.drop(columns=["tipo"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"ficha_educativa_{geo_id}.csv", mime="text/csv")
    st.caption("«Similar» significa que la diferencia con el referente no es estadísticamente significativa al 90 %. "
               "La posición ordena del resultado más favorable (1) al menos favorable entre los territorios del mismo nivel. "
               "La descarga incluye error estándar, CV y n muestral de cada cifra.")
c.leyenda_calidad()
c.nota_universo()
