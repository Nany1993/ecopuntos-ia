"""Dashboard Ecopuntos IA — navegación multipágina."""

from __future__ import annotations

import streamlit as st

from src.dashboard.common import apply_styles
from src.dashboard.pages import (
    pagina_indicadores,
    pagina_inventario,
    pagina_ranking,
)

st.set_page_config(
    page_title="Ecopuntos IA - Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()

pg = st.navigation(
    [
        st.Page(
            pagina_indicadores.render,
            title="Indicadores globales",
            icon="📊",
            url_path="indicadores",
            default=True,
        ),
        st.Page(
            pagina_ranking.render,
            title="Ranking EcoPuntos",
            icon="🏆",
            url_path="ranking",
        ),
        st.Page(
            pagina_inventario.render,
            title="Inventario de canecas",
            icon="🗑️",
            url_path="inventario",
        ),
    ]
)

pg.run()
