"""Página — Inventario de canecas."""

from __future__ import annotations

import importlib
from pathlib import Path

import streamlit as st

import src.dashboard.common as common
import src.dashboard.queries as queries
from src.config import settings
from src.database import get_database
from src.services.caneca_catalog import registrar_caneca, sugerir_id_caneca

importlib.reload(common)
importlib.reload(queries)

from src.dashboard.common import render_header, render_sidebar_base

QR_DIR = Path(__file__).resolve().parents[3] / "output" / "qr"

_COLOR_ES = {"blanca": "Blanca", "verde": "Verde", "negra": "Negra"}
_COLORES = ["blanca", "verde", "negra"]


def _filtrar_inventario(df, color: str, area: str):
    out = df.copy()
    if color != "Todos":
        out = out[out["color_caneca"] == color]
    if area != "Todas":
        out = out[out["area"] == area]
    return out


def _render_formulario_nueva_caneca(areas_sugeridas: list[str]) -> None:
    with st.expander("Registrar nueva caneca", expanded=False):
        st.caption(
            "Crea una caneca en el catálogo y genera su código QR para Telegram. "
            "El ID se sugiere automáticamente según el color."
        )

        col1, col2 = st.columns(2)
        with col1:
            color_nuevo = st.selectbox(
                "Color",
                _COLORES,
                format_func=lambda c: _COLOR_ES[c],
                key="nueva_caneca_color",
            )
        with col2:
            area_nuevo = st.text_input(
                "Área",
                placeholder="Ej. Cafetería, Recepción…",
                key="nueva_caneca_area",
            )
            if areas_sugeridas:
                st.caption("Áreas existentes: " + ", ".join(areas_sugeridas))

        ids = get_database().listar_ids_canecas()
        id_sugerido = sugerir_id_caneca(color_nuevo, ids)
        prev_color_key = "_prev_color_nueva_caneca"
        if st.session_state.get(prev_color_key) != color_nuevo:
            st.session_state["nueva_caneca_id"] = id_sugerido
            st.session_state[prev_color_key] = color_nuevo
        elif "nueva_caneca_id" not in st.session_state:
            st.session_state["nueva_caneca_id"] = id_sugerido

        id_personalizado = st.text_input(
            "ID de caneca",
            help="Formato CAN-BLANCA-01, CAN-VERDE-02 o CAN-NEGRA-03.",
            key="nueva_caneca_id",
        )

        if st.button("Crear caneca y generar QR", type="primary", key="btn_crear_caneca"):
            try:
                resultado = registrar_caneca(
                    area=area_nuevo,
                    color=color_nuevo,
                    id_caneca=id_personalizado.strip() or None,
                    output_dir=QR_DIR,
                )
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"No se pudo registrar la caneca: {exc}")
            else:
                st.success(
                    f"Caneca `{resultado.caneca.id_caneca}` registrada en "
                    f"{resultado.caneca.area}."
                )
                st.image(
                    str(resultado.qr_path),
                    caption=f"QR {resultado.caneca.id_caneca}",
                    use_container_width=True,
                )
                st.markdown(
                    f"**Enlace Telegram:** "
                    f"[{settings.telegram_deep_link_base}?start={resultado.caneca.id_caneca}]"
                    f"({settings.telegram_deep_link_base}?start={resultado.caneca.id_caneca})"
                )
                st.rerun()


def render() -> None:
    render_header("Inventario de canecas — Ecopuntos IA")

    with st.sidebar:
        render_sidebar_base()

    try:
        inventario = queries.inventario_canecas()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.info("Ejecuta `python -m scripts.init_db` para crear la base de datos.")
        return

    areas_sugeridas = (
        sorted(inventario["area"].unique().tolist()) if not inventario.empty else []
    )
    _render_formulario_nueva_caneca(areas_sugeridas)

    if inventario.empty:
        st.info(
            "No hay canecas registradas. Usa el formulario de arriba para crear la primera."
        )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Canecas en total", len(inventario))
    c2.metric("Canecas blancas", int((inventario["color_caneca"] == "blanca").sum()))
    c3.metric("Canecas verdes", int((inventario["color_caneca"] == "verde").sum()))
    c4.metric("Canecas negras", int((inventario["color_caneca"] == "negra").sum()))

    st.caption(
        "Catálogo del piloto según Resolución 2184 — código blanco, verde y negro. "
        "Los QR están en `output/qr/`."
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        colores = ["Todos", "blanca", "verde", "negra"]
        color_sel = st.selectbox(
            "Color de caneca",
            colores,
            format_func=lambda c: "Todos" if c == "Todos" else _COLOR_ES.get(c, c),
        )
    with col_f2:
        areas = ["Todas"] + sorted(inventario["area"].unique().tolist())
        area_sel = st.selectbox("Área", areas)

    filtrado = _filtrar_inventario(inventario, color_sel, area_sel)
    tabla = filtrado.copy()
    tabla["color_caneca"] = tabla["color_caneca"].map(_COLOR_ES)
    tabla["estado_caneca"] = tabla["estado_caneca"].str.capitalize()
    tabla["enlace_telegram"] = tabla["id_caneca"].apply(
        lambda cid: f"{settings.telegram_deep_link_base}?start={cid}"
    )

    st.subheader("Listado de canecas")
    if filtrado.empty:
        st.info("No hay canecas con los filtros seleccionados.")
        return

    st.dataframe(
        tabla.rename(
            columns={
                "id_caneca": "ID caneca",
                "area": "Área",
                "color_caneca": "Color",
                "estado_caneca": "Estado",
                "enlace_telegram": "Enlace Telegram",
            }
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Enlace Telegram": st.column_config.LinkColumn(display_text="Abrir bot"),
        },
    )

    st.divider()
    st.subheader("Códigos QR")
    etiquetas_qr = {
        row["id_caneca"]: (
            f"{row['id_caneca']} — {_COLOR_ES.get(row['color_caneca'], row['color_caneca'])} "
            f"({row['area']})"
        )
        for _, row in filtrado.iterrows()
    }
    id_sel = st.selectbox(
        "Selecciona una caneca para ver su QR",
        list(etiquetas_qr.keys()),
        format_func=lambda cid: etiquetas_qr[cid],
    )
    qr_path = QR_DIR / f"qr_{id_sel}.png"
    col_qr, col_info = st.columns([1, 2])
    with col_qr:
        if qr_path.exists():
            st.image(str(qr_path), caption=f"QR {id_sel}", use_container_width=True)
        else:
            st.warning(
                f"No se encontró `{qr_path.name}`. "
                "Genera los QR con: `python -m scripts.generate_qr`"
            )
    with col_info:
        fila = filtrado[filtrado["id_caneca"] == id_sel].iloc[0]
        st.markdown(f"**ID:** `{fila['id_caneca']}`")
        st.markdown(f"**Color:** {_COLOR_ES.get(fila['color_caneca'], fila['color_caneca'])}")
        st.markdown(f"**Área:** {fila['area']}")
        st.markdown(f"**Estado:** {str(fila['estado_caneca']).capitalize()}")
        st.markdown(
            f"**Enlace:** [{settings.telegram_deep_link_base}?start={id_sel}]"
            f"({settings.telegram_deep_link_base}?start={id_sel})"
        )
