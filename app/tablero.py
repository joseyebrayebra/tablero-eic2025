"""Tablero educativo – Encuesta Intercensal 2025.

Uso: streamlit run app/tablero.py
Solo lee data/output/ (generado por src/) y config/semaforo.yaml.
"""

from pathlib import Path

import streamlit as st

PAGINAS = Path(__file__).parent / "paginas"

st.set_page_config(page_title="Tablero educativo EIC 2025", page_icon="📊", layout="wide")

paginas = {
    "Educación": [
        st.Page(PAGINAS / "resumen.py", title="Resumen ejecutivo", icon="🚦", default=True),
        st.Page(PAGINAS / "ficha.py", title="Ficha educativa", icon="📋"),
        st.Page(PAGINAS / "trayectoria.py", title="Trayectoria por edad", icon="📈"),
        st.Page(PAGINAS / "logro.py", title="Logro por nivel y cohorte", icon="🎓"),
        st.Page(PAGINAS / "brechas.py", title="Brechas", icon="⚖️"),
        st.Page(PAGINAS / "mapa.py", title="Mapa y ranking", icon="🗺️"),
        st.Page(PAGINAS / "comparativo.py", title="Comparativo", icon="🆚"),
    ],
    "Para comunicar": [
        st.Page(PAGINAS / "brief.py", title="Brief: cifras en perspectiva", icon="💬"),
    ],
    "Factores asociados": [
        st.Page(PAGINAS / "factores.py", title="Modelo con estados pares", icon="🔗"),
        st.Page(PAGINAS / "factores_nacional.py", title="Modelo nacional", icon="🌎"),
    ],
}
navegacion = st.navigation(paginas)

with st.sidebar:
    st.radio("Geografía", ["Nación", "Guanajuato"], index=1, key="geografia", horizontal=True)
    st.caption("Encuesta Intercensal 2025, INEGI. Viviendas particulares habitadas.")

navegacion.run()
