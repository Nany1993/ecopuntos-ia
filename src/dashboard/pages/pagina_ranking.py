"""Página — Ranking EcoPuntos."""

from __future__ import annotations

import importlib

import streamlit as st

import src.dashboard.common as common
import src.dashboard.queries as queries
from src.dashboard import charts

importlib.reload(common)
importlib.reload(charts)
importlib.reload(queries)

from src.dashboard.charts import chart_aciertos_caneca_horizontal
from src.dashboard.common import render_header, render_sidebar_base


def _filtros_area_usuario(key_prefix: str) -> tuple[str | None, str | None]:
    opciones = queries.opciones_filtro_actividad()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        areas = ["Todas"] + opciones["areas"]["area"].tolist()
        area_sel = st.selectbox("Área", areas, key=f"{key_prefix}_area")

    with col_f2:
        colab_df = opciones["colaboradores"]
        colab_opciones: dict[str, str | None] = {"Todos": None}
        if not colab_df.empty:
            for _, row in colab_df.iterrows():
                etiqueta = str(row["colaborador"])
                if row.get("username_telegram"):
                    etiqueta += f" (@{row['username_telegram']})"
                colab_opciones[etiqueta] = row["id_colaborador"]
        colab_etiqueta = st.selectbox(
            "Usuario",
            list(colab_opciones.keys()),
            key=f"{key_prefix}_usuario",
        )

    area = None if area_sel == "Todas" else area_sel
    id_colaborador = colab_opciones[colab_etiqueta]
    return area, id_colaborador


def render() -> None:
    render_header("Ranking EcoPuntos — Ecopuntos IA")

    with st.sidebar:
        render_sidebar_base()

    try:
        resumen = queries.ranking_resumen()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info("Ejecuta `python -m scripts.init_db` para crear la base de datos.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Personas participando", resumen["personas"])
    c2.metric("EcoPuntos asignados", resumen["ecopuntos"])
    c3.metric("Aciertos", resumen["aciertos"])
    c4.metric("Desaciertos", resumen["desaciertos"])

    st.divider()
    st.subheader("Desempeño por caneca")
    area, id_colaborador = _filtros_area_usuario("ranking_caneca")
    por_caneca = queries.aciertos_desaciertos_por_caneca(area, id_colaborador)
    chart_aciertos_caneca_horizontal(por_caneca)

    st.divider()
    st.subheader("Tabla de ranking")
    tabla = queries.ranking_tabla()
    if tabla.empty:
        st.info("Aún no hay colaboradores con clasificaciones registradas.")
    else:
        st.dataframe(
            tabla.rename(
                columns={
                    "usuario": "Usuario",
                    "intentos": "Intentos",
                    "aciertos": "Aciertos",
                    "desaciertos": "Desaciertos",
                    "puntos": "Puntos",
                }
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Puntos": st.column_config.NumberColumn(format="%d pts"),
            },
        )
