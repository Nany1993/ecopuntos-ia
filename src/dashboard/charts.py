"""Gráficos y secciones analíticas del dashboard."""

from __future__ import annotations

import importlib

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import src.dashboard.queries as queries
from src.config import settings
from src.dashboard.common import AXIS_STYLE, RESULTADO_COLORS, layout

importlib.reload(queries)


def _color_for_caneca(color: str) -> str:
    return queries.COLOR_MAP.get(color, "#6B7280")


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
        **layout(
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
        **layout(
            title="Tasa de exito por caneca",
            yaxis_title="% acierto",
            yaxis={**AXIS_STYLE, "range": [0, 105]},
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_caneca_alternable(df) -> None:
    """Muestra clasificaciones apiladas o tasa de acierto en el mismo espacio."""
    if df.empty:
        st.info("Sin datos de canecas aún.")
        return
    vista = st.segmented_control(
        "Vista de canecas",
        options=["Clasificaciones", "Tasa de acierto"],
        default="Clasificaciones",
        label_visibility="collapsed",
    )
    if vista == "Tasa de acierto":
        chart_tasa_caneca(df)
    else:
        chart_exito_caneca(df)


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
        **layout(
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
    df = df.copy()
    df["resultado_label"] = df["resultado"].replace(
        {"correcto": "Correcto", "incorrecto": "Incorrecto", "error": "Error"}
    )
    fig = px.pie(
        df,
        values="cantidad",
        names="resultado_label",
        color="resultado",
        color_discrete_map=RESULTADO_COLORS,
        hole=0.45,
    )
    fig.update_traces(textfont=dict(color="#F8FAFC"))
    fig.update_layout(
        **layout(
            title=dict(
                text="Distribución de resultados",
                x=0.0,
                xanchor="left",
                y=0.97,
                yanchor="top",
            ),
            height=400,
            margin=dict(l=10, r=10, t=40, b=55),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.06,
                xanchor="center",
                x=0.5,
                font=dict(color="#E2E8F0"),
            ),
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_timeline(df, titulo: str = "Actividad diaria"):
    if df.empty:
        st.info("Sin actividad registrada para los filtros seleccionados.")
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
        **layout(
            title=titulo,
            xaxis_title="Fecha",
            yaxis_title="Clasificaciones",
            height=380,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_aciertos_caneca_horizontal(df) -> None:
    """Barras horizontales apiladas: aciertos y desaciertos por color de caneca."""
    if df.empty:
        st.info("Sin datos para los filtros seleccionados.")
        return
    df = df.copy()
    df["etiqueta"] = df["caneca_qr"].astype(str).str.capitalize()
    df["total"] = df["aciertos"] + df["desaciertos"]
    df["pct_aciertos"] = (100 * df["aciertos"] / df["total"].replace(0, 1)).round(1)
    df["pct_desaciertos"] = (100 * df["desaciertos"] / df["total"].replace(0, 1)).round(1)

    texto_aciertos = df.apply(
        lambda r: f"{int(r['aciertos'])} ({r['pct_aciertos']:.1f}%)", axis=1
    )
    texto_desaciertos = df.apply(
        lambda r: f"{int(r['desaciertos'])} ({r['pct_desaciertos']:.1f}%)", axis=1
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Aciertos",
            y=df["etiqueta"],
            x=df["aciertos"],
            orientation="h",
            marker_color="#22C55E",
            text=texto_aciertos,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#F8FAFC", size=12),
            customdata=list(zip(df["pct_aciertos"], df["total"])),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Aciertos: %{x}<br>"
                "Porcentaje: %{customdata[0]:.1f}%<br>"
                "Total: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Bar(
            name="Desaciertos",
            y=df["etiqueta"],
            x=df["desaciertos"],
            orientation="h",
            marker_color="#EF4444",
            text=texto_desaciertos,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#F8FAFC", size=12),
            customdata=list(zip(df["pct_desaciertos"], df["total"])),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Desaciertos: %{x}<br>"
                "Porcentaje: %{customdata[0]:.1f}%<br>"
                "Total: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        **layout(
            title=dict(
                text="Desempeño por color de caneca",
                x=0.0,
                xanchor="left",
            ),
            barmode="stack",
            xaxis_title="Clasificaciones",
            height=260,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
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
        **layout(
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
    m1.metric("Personas participando", len(detalle))
    m2.metric("EcoPuntos en total", int(detalle["puntos_totales"].sum()))
    m3.metric("Aciertos a la 1.ª vez", int(detalle["aciertos_primera"].sum()))
    m4.metric("Líder del ranking", str(top.iloc[0]["colaborador"]))

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
    d2.metric("Aciertos a la 1.ª vez", int(fila["aciertos_primera"]))
    d3.metric("Depósitos confirmados", int(fila["sesiones_completadas"]))
    d4.metric("Clasificaciones hechas", int(fila["total_intentos"]))
    d5.metric("Porcentaje de aciertos", f"{fila['tasa_exito_pct'] or 0:.1f}%")
    d6.metric("Puntos en historial", int(fila["puntos_otorgados_historial"]))

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
