import pandas as pd
import streamlit as st

import comun as c

b = c.brief()
st.title(b["titulo"])
st.markdown("Brief para comunicar: cada cifra de la Encuesta Intercensal 2025 traducida a un referente cotidiano "
            "(uno de cada tantos, la población de un municipio, el promedio del país, otra generación).")
if st.session_state.get("geografia") == "Nación":
    st.info("Este brief se elaboró solo para Guanajuato.")
st.download_button("Descargar el brief (texto)", (c.SALIDA / "brief_guanajuato.md").read_bytes(),
                   file_name="brief_educacion_guanajuato.md", mime="text/markdown")


def valor_txt(r: dict) -> str:
    if r["unidad"] == "personas":
        return f"{r['valor']:,.0f}"
    return f"{r['valor']:.2f} grados" if r["unidad"] == "grados" else f"{r['valor']:.1f} %"


for tema in dict.fromkeys(i["tema"] for i in b["frases"]):
    st.subheader(tema)
    for i in (i for i in b["frases"] if i["tema"] == tema):
        with st.container(border=True):
            st.markdown(f"<div style='font-size:1.35rem;font-weight:600;color:{c.TEXTO};border-left:6px solid {c.AZUL};"
                        f"padding-left:12px;line-height:1.3'>{i['titular']}{' ' + c.AVISO if i['aviso'] else ''}</div>",
                        unsafe_allow_html=True)
            st.markdown(i["frase"])
            with st.expander("Cifras de respaldo"):
                st.dataframe(pd.DataFrame([{
                    "Concepto": r["concepto"], "Valor": valor_txt(r),
                    "Error estándar": None if r["ee"] is None else round(r["ee"], 2),
                    "CV (%)": None if r["cv"] is None else round(r["cv"], 1),
                    "n muestral": r["n_muestral"], "Calidad": r["calidad"] or r["tipo"],
                } for r in i["respaldo"]]), hide_index=True, use_container_width=True)
                for r in i["respaldo"]:
                    if r.get("nota"):
                        st.caption(f"{r['concepto']}: {r['nota']}.")

st.subheader("Cómo leer este brief")
st.markdown("\n".join(f"- {n}" for n in b["notas"]))
st.caption(f"{c.AVISO} indica que alguna cifra de respaldo tiene calidad media (CV de 15 a 30 %). "
           "Las frases cuyo respaldo es de calidad baja no se generan.")
st.caption(b["fuente"])
