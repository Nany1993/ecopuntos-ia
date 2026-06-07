"""Página 1 — Indicadores globales y análisis de segregación."""

from __future__ import annotations

import importlib

import streamlit as st

import src.dashboard.common as common
import src.dashboard.queries as queries
from src.dashboard import charts

importlib.reload(common)
importlib.reload(charts)
importlib.reload(queries)

from src.dashboard.charts import chart_caneca_alternable, chart_resultados, chart_timeline
from src.dashboard.common import render_header, render_kpis, render_sidebar_base


def _render_filtros_actividad() -> tuple[str | None, str | None, str | None]:
    opciones = queries.opciones_filtro_actividad()

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        areas = ["Todas"] + opciones["areas"]["area"].tolist()
        area_sel = st.selectbox("Área", areas, key="filtro_area_actividad")

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
            key="filtro_usuario_actividad",
        )

    with col_f3:
        caneca_df = opciones["canecas"]
        caneca_opciones: dict[str, str | None] = {"Todas": None}
        if not caneca_df.empty:
            for _, row in caneca_df.iterrows():
                etiqueta = f"{row['id_caneca']} ({row['caneca_qr']})"
                caneca_opciones[etiqueta] = row["id_caneca"]
        caneca_etiqueta = st.selectbox(
            "Caneca",
            list(caneca_opciones.keys()),
            key="filtro_caneca_actividad",
        )

    area = None if area_sel == "Todas" else area_sel
    id_colaborador = colab_opciones[colab_etiqueta]
    id_caneca = caneca_opciones[caneca_etiqueta]
    return area, id_colaborador, id_caneca


def render() -> None:
    render_header("Indicadores globales — Ecopuntos IA")

    with st.sidebar:
        render_sidebar_base()

    try:
        kpi = queries.kpi_resumen()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info("Ejecuta `python -m scripts.init_db` para crear la base de datos.")
        return

    render_kpis(kpi)
    st.divider()

    por_caneca = queries.intentos_por_caneca()
    col_graf, col_dona = st.columns([3, 2])
    with col_graf:
        chart_caneca_alternable(por_caneca)
    with col_dona:
        chart_resultados(queries.distribucion_resultados())

    st.divider()
    st.subheader("Actividad diaria")
    st.caption("Segmenta la tendencia por área, usuario o caneca.")

    area, id_colaborador, id_caneca = _render_filtros_actividad()
    timeline = queries.intentos_en_el_tiempo(
        area=area,
        id_colaborador=id_colaborador,
        id_caneca=id_caneca,
    )
    chart_timeline(timeline)
