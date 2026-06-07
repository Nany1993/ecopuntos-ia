"""Estilos y componentes compartidos del dashboard Ecopuntos IA."""

from __future__ import annotations

import streamlit as st

from src.config import settings

AXIS_STYLE = dict(
    gridcolor="rgba(148, 163, 184, 0.15)",
    linecolor="rgba(148, 163, 184, 0.4)",
    tickfont=dict(color="#CBD5E1"),
    title_font=dict(color="#E2E8F0"),
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15, 23, 42, 0.35)",
    font=dict(family="DM Sans, sans-serif", color="#E2E8F0"),
    title=dict(font=dict(color="#F8FAFC", size=16)),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(color="#E2E8F0"),
    ),
    xaxis=AXIS_STYLE,
    yaxis=AXIS_STYLE,
)

RESULTADO_COLORS = {
    "correcto": "#22C55E",
    "incorrecto": "#EF4444",
    "error": "#F59E0B",
}


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }

        .stApp {
            background: linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #0f172a 100%);
        }

        .main-header {
            background: linear-gradient(135deg, #0f766e 0%, #059669 50%, #10b981 100%);
            padding: 1.5rem 2rem;
            border-radius: 16px;
            color: #ffffff !important;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.25);
        }
        .main-header h1, .main-header p {
            color: #ffffff !important;
        }
        .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
        .main-header p { margin: 0.4rem 0 0 0; opacity: 0.95; font-size: 1rem; }

        div[data-testid="stMetric"] {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.78rem !important;
            white-space: normal !important;
            line-height: 1.25 !important;
            min-height: 2.4em;
            overflow: visible !important;
            text-overflow: unset !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #f1f5f9 !important;
            font-size: 1.35rem !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
            overflow: visible !important;
            text-overflow: unset !important;
        }

        section[data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid #334155;
        }
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] .stCaption {
            color: #94a3b8 !important;
        }

        h1, h2, h3, h4, .stSubheader {
            color: #f1f5f9 !important;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #334155;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def layout(**extra) -> dict:
    return {**PLOTLY_LAYOUT, **extra}


def render_header(subtitulo: str = "Indicadores ambientales - Ecopuntos IA") -> None:
    st.markdown(
        f"""
        <div class="main-header">
            <h1>Ecopuntos IA - Dashboard</h1>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(kpi: dict) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(
        "Clasificaciones totales",
        kpi["total_intentos"],
        help="Cantidad de fotos de residuos enviadas y evaluadas por el bot.",
    )
    c2.metric(
        "Porcentaje de aciertos",
        f"{kpi['tasa_exito']:.1f}%",
        help="Veces que la caneca escaneada coincidió con lo que indicó el agente IA.",
    )
    c3.metric(
        "Correctas a la 1.ª vez",
        f"{kpi['first_time_right']:.1f}%",
        help="Clasificaciones acertadas en el primer intento, sin necesidad de reintento.",
    )
    c4.metric(
        "EcoPuntos otorgados",
        kpi["puntos_totales"],
        help="Puntos de reciclaje ganados por acertar a la primera y confirmar el depósito.",
    )
    c5.metric(
        "Confianza del agente",
        f"{kpi['confianza_promedio']:.1f}%",
        help="Qué tan seguro está el agente IA de sus clasificaciones (promedio).",
    )
    c6.metric(
        "Respuesta rápida",
        f"{kpi['cumplimiento_sla']:.1f}%",
        help="Porcentaje de clasificaciones respondidas en menos de 5 segundos.",
    )


def render_sidebar_base() -> None:
    st.markdown("### Panel")
    st.caption(f"Base de datos: `{settings.sqlite_path}`")
    if st.button("Actualizar datos", use_container_width=True):
        st.rerun()
    st.divider()
    st.markdown("**Clasificación IA**")
    st.caption(
        "El agente clasifica residuos según la Resolución 2184 de 2019 "
        "(Código de Colores Colombia)."
    )
