"""Dashboard SmartSort — Streamlit + Plotly."""

from __future__ import annotations

import importlib

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import src.dashboard.queries as queries
from src.config import settings

importlib.reload(queries)

st.set_page_config(
    page_title="Ecopuntos IA - Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        font-size: 0.72rem !important;
        white-space: normal !important;
        line-height: 1.2 !important;
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


def _color_for_caneca(color: str) -> str:
    return queries.COLOR_MAP.get(color, "#6B7280")


def _layout(**extra) -> dict:
    layout = {**PLOTLY_LAYOUT, **extra}
    return layout


def render_header():
    st.markdown(
        """
        <div class="main-header">
            <h1>Ecopuntos IA - Dashboard</h1>
            <p>Indicadores ambientales - Ecopuntos IA</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(kpi: dict):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Intentos", kpi["total_intentos"])
    c2.metric("Tasa de exito", f"{kpi['tasa_exito']:.1f}%")
    c3.metric("First Time Right", f"{kpi['first_time_right']:.1f}%")
    c4.metric("EcoPuntos", kpi["puntos_totales"])
    c5.metric("Confianza IA", f"{kpi['confianza_promedio']:.1f}%")
    c6.metric("SLA <= 5s", f"{kpi['cumplimiento_sla']:.1f}%")


def chart_exito_caneca(df):
    if df.empty:
        st.info("Sin datos de canecas aun.")
        return
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Correctos",
            x=df["caneca_qr"],
            y=df["correctos"],
            marker_color="#22C55E",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Incorrectos",
            x=df["caneca_qr"],
            y=df["incorrectos"],
            marker_color="#EF4444",
        )
    )
    fig.update_layout(
        **_layout(
            title="Clasificaciones por color de caneca",
            barmode="stack",
            xaxis_title="Caneca (codigo de colores)",
            yaxis_title="Intentos",
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_tasa_caneca(df):
    if df.empty:
        return
    df = df.copy()
    df["color_barra"] = df["caneca_qr"].map(_color_for_caneca)
    fig = go.Figure(
        data=[
            go.Bar(
                x=df["caneca_qr"],
                y=df["tasa_exito"],
                text=df["tasa_exito"].map(lambda v: f"{v:.1f}%"),
                textposition="outside",
                marker=dict(
                    color=df["color_barra"],
                    line=dict(color="#E2E8F0", width=1),
                ),
            )
        ]
    )
    fig.update_layout(
        **_layout(
            title="Tasa de exito por caneca",
            yaxis_title="% acierto",
            yaxis={**AXIS_STYLE, "range": [0, 105]},
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_area(df):
    if df.empty:
        st.info("Sin datos por area.")
        return
    fig = px.bar(
        df,
        x="area",
        y="tasa_exito",
        color="tasa_exito",
        color_continuous_scale=["#FCA5A5", "#FDE047", "#22C55E"],
        range_color=[0, 100],
        text="tasa_exito",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        **_layout(
            title="Desempeno por area",
            yaxis_title="% acierto",
            yaxis={**AXIS_STYLE, "range": [0, 105]},
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_resultados(df):
    if df.empty:
        return
    fig = px.pie(
        df,
        values="cantidad",
        names="resultado",
        color="resultado",
        color_discrete_map=RESULTADO_COLORS,
        hole=0.45,
    )
    fig.update_traces(textfont=dict(color="#F8FAFC"))
    fig.update_layout(**_layout(title="Distribucion de resultados", height=380))
    st.plotly_chart(fig, use_container_width=True)


def chart_timeline(df):
    if df.empty:
        st.info("Sin actividad registrada en el tiempo.")
        return
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["correctos"],
            name="Correctos",
            mode="lines+markers",
            line=dict(color="#22C55E", width=3),
            marker=dict(size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["incorrectos"],
            name="Incorrectos",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
            marker=dict(size=8),
        )
    )
    fig.update_layout(
        **_layout(
            title="Actividad diaria",
            xaxis_title="Fecha",
            yaxis_title="Intentos",
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_ranking(df):
    if df.empty:
        st.info("Aun no hay EcoPuntos registrados.")
        return
    df = df.copy()
    if "nombre" not in df.columns:
        if "colaborador" in df.columns:
            df["nombre"] = df["colaborador"]
        elif "id_colaborador" in df.columns:
            df["nombre"] = df["id_colaborador"].astype(str)
    df["label"] = df["nombre"].astype(str)
    if "username_telegram" in df.columns:
        mask = df["username_telegram"].notna() & (df["username_telegram"] != "")
        df.loc[mask, "label"] = (
            df.loc[mask, "nombre"] + " (@" + df.loc[mask, "username_telegram"] + ")"
        )
    fig = px.bar(
        df.sort_values("puntos_totales"),
        x="puntos_totales",
        y="label",
        orientation="h",
        color="puntos_totales",
        color_continuous_scale=["#065F46", "#10B981"],
        text="puntos_totales",
    )
    fig.update_traces(textposition="outside", textfont=dict(color="#E2E8F0"))
    fig.update_layout(
        **_layout(
            title="Ranking EcoPuntos",
            xaxis_title="Puntos",
            yaxis_title="Colaborador",
            height=max(280, len(df) * 45),
            showlegend=False,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def render_ranking_ecopuntos():
    st.subheader("Ranking EcoPuntos")
    st.caption(
        f"Cada colaborador se identifica por su **ID unico de Telegram**. "
        f"Se otorgan **+{settings.puntos_acierto_primera} EcoPuntos** al acertar "
        f"a la 1ra clasificacion y confirmar el deposito."
    )

    detalle = queries.ranking_ecopuntos_detalle()
    if detalle.empty:
        st.info("Aun no hay colaboradores con puntos o intentos registrados.")
        return

    top = detalle.head(10)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colaboradores activos", len(detalle))
    m2.metric("EcoPuntos totales", int(detalle["puntos_totales"].sum()))
    m3.metric("Aciertos 1ra (total)", int(detalle["aciertos_primera"].sum()))
    m4.metric("Lider", str(top.iloc[0]["colaborador"]))

    col_graf, col_tab = st.columns([2, 3])
    with col_graf:
        chart_ranking(top)
    with col_tab:
        tabla = detalle[
            [
                "posicion", "colaborador", "id_colaborador", "username_telegram",
                "puntos_totales", "aciertos_primera", "sesiones_completadas",
                "total_intentos", "tasa_exito_pct", "puntos_otorgados_historial",
            ]
        ].rename(
            columns={
                "posicion": "#",
                "colaborador": "Colaborador",
                "id_colaborador": "ID Telegram",
                "username_telegram": "Usuario TG",
                "puntos_totales": "EcoPuntos",
                "aciertos_primera": "Aciertos 1ra",
                "sesiones_completadas": "Sesiones OK",
                "total_intentos": "Intentos",
                "tasa_exito_pct": "Tasa exito %",
                "puntos_otorgados_historial": "Pts historial",
            }
        )
        st.markdown("**Tabla de ranking**")
        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "EcoPuntos": st.column_config.NumberColumn(format="%d pts"),
                "Tasa exito %": st.column_config.ProgressColumn(
                    min_value=0, max_value=100, format="%.1f%%"
                ),
            },
        )

    st.divider()
    st.markdown("**Detalle por usuario**")

    opciones = {
        f"{row['colaborador']} — {row['puntos_totales']} pts (ID {row['id_colaborador']})": row["id_colaborador"]
        for _, row in detalle.iterrows()
    }
    elegido = st.selectbox("Selecciona colaborador", list(opciones.keys()))
    id_sel = opciones[elegido]
    fila = detalle[detalle["id_colaborador"] == id_sel].iloc[0]

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("EcoPuntos", int(fila["puntos_totales"]))
    d2.metric("Aciertos 1ra", int(fila["aciertos_primera"]))
    d3.metric("Sesiones completadas", int(fila["sesiones_completadas"]))
    d4.metric("Total intentos", int(fila["total_intentos"]))
    d5.metric("Tasa de exito", f"{fila['tasa_exito_pct'] or 0:.1f}%")
    d6.metric("Pts en historial", int(fila["puntos_otorgados_historial"]))

    user_intentos = queries.intentos_de_colaborador(id_sel, limit=20)
    if user_intentos.empty:
        st.caption("Sin intentos registrados para este usuario.")
    else:
        st.dataframe(
            user_intentos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "confianza_pct": st.column_config.ProgressColumn(
                    "Confianza IA", format="%.1f%%", min_value=0, max_value=100
                ),
                "puntos": st.column_config.NumberColumn("EcoPuntos", format="%d"),
                "acierto_1ra": st.column_config.CheckboxColumn("Acierto 1ra"),
            },
        )


def main():
    render_header()

    with st.sidebar:
        st.markdown("### Panel")
        st.caption(f"Base de datos: `{settings.sqlite_path}`")
        if st.button("Actualizar datos", use_container_width=True):
            st.rerun()
        st.divider()
        st.markdown("**Codigo de colores**")
        st.markdown("- **Blanca** — papel, carton")
        st.markdown("- **Verde** — plastico, vidrio, metal")
        st.markdown("- **Negra** — no aprovechables")
        st.divider()
        st.code(".\\scripts\\start.ps1", language="powershell")

    try:
        kpi = queries.kpi_resumen()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info("Ejecuta `python -m scripts.init_db` para crear la base de datos.")
        return

    render_kpis(kpi)
    st.divider()

    por_caneca = queries.intentos_por_caneca()
    col_a, col_b = st.columns(2)
    with col_a:
        chart_exito_caneca(por_caneca)
    with col_b:
        chart_tasa_caneca(por_caneca)

    col_c, col_d = st.columns(2)
    with col_c:
        chart_area(queries.intentos_por_area())
    with col_d:
        chart_resultados(queries.distribucion_resultados())

    chart_timeline(queries.intentos_en_el_tiempo())

    st.divider()
    render_ranking_ecopuntos()

    st.divider()
    st.subheader("Ultimos intentos")
    ultimos = queries.ultimos_intentos()
    if ultimos.empty:
        st.info("No hay intentos registrados. Prueba el bot en Telegram.")
    else:
        columnas = [
            "fecha", "colaborador", "id_caneca", "caneca_qr",
            "prediccion_ia", "confianza_pct", "resultado", "puntos", "latencia_ms",
        ]
        cols_visibles = [c for c in columnas if c in ultimos.columns]
        st.dataframe(
            ultimos[cols_visibles],
            use_container_width=True,
            hide_index=True,
            column_config={
                "confianza_pct": st.column_config.ProgressColumn(
                    "Confianza IA",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )

    with st.expander("Inventario de canecas"):
        st.dataframe(queries.inventario_canecas(), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
