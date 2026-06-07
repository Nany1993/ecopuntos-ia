"""Consultas KPI para el dashboard SmartSort."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import settings

COLOR_MAP = {
    "blanca": "#9CA3AF",  # gris visible (caneca blanca — no usar blanco puro)
    "verde": "#22C55E",
    "negra": "#475569",
}


def _ensure_colaborador_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "nombre" not in df.columns:
        if "colaborador" in df.columns:
            df["nombre"] = df["colaborador"]
        elif "id_colaborador" in df.columns:
            df["nombre"] = df["id_colaborador"].astype(str)
    if "colaborador" not in df.columns:
        if "nombre" in df.columns:
            df["colaborador"] = df["nombre"]
        elif "id_colaborador" in df.columns:
            df["colaborador"] = df["id_colaborador"].astype(str)
    return df


def _connect() -> sqlite3.Connection:
    path = Path(settings.sqlite_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe la base de datos: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def kpi_resumen() -> dict:
    df = _query(
        """
        SELECT
            (SELECT COUNT(*) FROM registro_intentos) AS total_intentos,
            (SELECT COUNT(DISTINCT id_sesion) FROM sesiones) AS total_sesiones,
            (SELECT COUNT(*) FROM sesiones WHERE estado_sesion = 'CERRADA_EXITOSA') AS sesiones_exitosas,
            (SELECT COALESCE(SUM(puntos_totales), 0) FROM puntos_colaborador) AS puntos_totales,
            (SELECT COUNT(*) FROM puntos_colaborador) AS colaboradores_activos
        """
    )
    row = df.iloc[0]

    tasa = _query(
        """
        SELECT
            ROUND(100.0 * SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN resultado_intento IN ('correcto', 'incorrecto') THEN 1 ELSE 0 END), 0), 1)
            AS tasa_exito
        FROM registro_intentos
        """
    )
    ftr = _query(
        """
        SELECT
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN numero_intento = 1 AND resultado_intento = 'correcto'
                THEN id_sesion END)
                / NULLIF(COUNT(DISTINCT id_sesion), 0), 1) AS first_time_right
        FROM registro_intentos
        """
    )
    sla = _query(
        """
        SELECT
            ROUND(100.0 * SUM(CASE WHEN tiempo_respuesta_ms <= 5000 THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0), 1) AS cumplimiento_sla
        FROM registro_intentos
        """
    )
    conf = _query(
        """
        SELECT ROUND(AVG(nivel_confianza) * 100, 1) AS confianza_promedio
        FROM registro_intentos
        WHERE nivel_confianza IS NOT NULL
        """
    )

    return {
        "total_intentos": int(row["total_intentos"] or 0),
        "total_sesiones": int(row["total_sesiones"] or 0),
        "sesiones_exitosas": int(row["sesiones_exitosas"] or 0),
        "puntos_totales": int(row["puntos_totales"] or 0),
        "colaboradores_activos": int(row["colaboradores_activos"] or 0),
        "tasa_exito": float(tasa.iloc[0]["tasa_exito"] or 0),
        "first_time_right": float(ftr.iloc[0]["first_time_right"] or 0),
        "cumplimiento_sla": float(sla.iloc[0]["cumplimiento_sla"] or 0),
        "confianza_promedio": float(conf.iloc[0]["confianza_promedio"] or 0),
    }


def intentos_por_caneca() -> pd.DataFrame:
    return _query(
        """
        SELECT
            caneca_qr,
            SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS correctos,
            SUM(CASE WHEN resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS incorrectos,
            ROUND(100.0 * SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN resultado_intento IN ('correcto', 'incorrecto') THEN 1 ELSE 0 END), 0), 1)
            AS tasa_exito
        FROM registro_intentos
        GROUP BY caneca_qr
        ORDER BY caneca_qr
        """
    )


def intentos_por_area() -> pd.DataFrame:
    return _query(
        """
        SELECT
            area,
            COUNT(*) AS intentos,
            ROUND(100.0 * SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN resultado_intento IN ('correcto', 'incorrecto') THEN 1 ELSE 0 END), 0), 1)
            AS tasa_exito
        FROM registro_intentos
        GROUP BY area
        ORDER BY intentos DESC
        """
    )


def distribucion_resultados() -> pd.DataFrame:
    return _query(
        """
        SELECT resultado_intento AS resultado, COUNT(*) AS cantidad
        FROM registro_intentos
        GROUP BY resultado_intento
        ORDER BY cantidad DESC
        """
    )


def _where_filtros(
    area: str | None = None,
    id_colaborador: str | None = None,
    prefijo: str = "",
) -> tuple[str, list]:
    p = f"{prefijo}." if prefijo else ""
    conditions: list[str] = []
    params: list[str] = []
    if area:
        conditions.append(f"{p}area = ?")
        params.append(area)
    if id_colaborador:
        conditions.append(f"{p}id_colaborador = ?")
        params.append(id_colaborador)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def ranking_resumen() -> dict:
    df = _query(
        """
        SELECT
            (SELECT COUNT(DISTINCT id_colaborador) FROM registro_intentos) AS personas,
            (SELECT COALESCE(SUM(puntos_totales), 0) FROM puntos_colaborador) AS ecopuntos,
            SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS aciertos,
            SUM(CASE WHEN resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS desaciertos
        FROM registro_intentos
        """
    )
    row = df.iloc[0]
    return {
        "personas": int(row["personas"] or 0),
        "ecopuntos": int(row["ecopuntos"] or 0),
        "aciertos": int(row["aciertos"] or 0),
        "desaciertos": int(row["desaciertos"] or 0),
    }


def aciertos_desaciertos_por_caneca(
    area: str | None = None,
    id_colaborador: str | None = None,
) -> pd.DataFrame:
    where, params = _where_filtros(area, id_colaborador)
    return _query(
        f"""
        SELECT
            caneca_qr,
            SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS aciertos,
            SUM(CASE WHEN resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS desaciertos
        FROM registro_intentos
        {where}
        GROUP BY caneca_qr
        ORDER BY CASE caneca_qr
            WHEN 'blanca' THEN 1
            WHEN 'verde' THEN 2
            WHEN 'negra' THEN 3
            ELSE 4
        END
        """,
        tuple(params),
    )


def ranking_tabla() -> pd.DataFrame:
    """Tabla de ranking: usuario, intentos, aciertos, desaciertos, puntos."""
    df = _query(
        """
        SELECT
            COALESCE(c.nombre, r.id_colaborador) AS usuario,
            c.username_telegram,
            COUNT(r.id) AS intentos,
            SUM(CASE WHEN r.resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS aciertos,
            SUM(CASE WHEN r.resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS desaciertos,
            COALESCE(p.puntos_totales, 0) AS puntos
        FROM registro_intentos r
        LEFT JOIN colaboradores c ON c.id_colaborador = r.id_colaborador
        LEFT JOIN puntos_colaborador p ON p.id_colaborador = r.id_colaborador
        GROUP BY r.id_colaborador, c.nombre, c.username_telegram, p.puntos_totales
        ORDER BY puntos DESC, aciertos DESC, intentos DESC
        """
    )
    if not df.empty and "username_telegram" in df.columns:
        mask = df["username_telegram"].notna() & (df["username_telegram"] != "")
        df.loc[mask, "usuario"] = (
            df.loc[mask, "usuario"] + " (@" + df.loc[mask, "username_telegram"] + ")"
        )
    return df.drop(columns=["username_telegram"], errors="ignore")


def ranking_ecopuntos(limit: int = 10) -> pd.DataFrame:
    df = ranking_ecopuntos_detalle()
    if limit and len(df) > limit:
        return df.head(limit)
    return df


def ranking_ecopuntos_detalle() -> pd.DataFrame:
    """Ranking completo con metricas de EcoPuntos e intentos por colaborador (ID Telegram)."""
    df = _query(
        """
        SELECT
            c.id_colaborador,
            COALESCE(c.nombre, c.id_colaborador) AS colaborador,
            c.username_telegram,
            c.es_semilla,
            COALESCE(p.puntos_totales, 0) AS puntos_totales,
            COALESCE(p.aciertos_primera, 0) AS aciertos_primera,
            COALESCE(p.sesiones_completadas, 0) AS sesiones_completadas,
            COUNT(r.id) AS total_intentos,
            SUM(CASE WHEN r.resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS intentos_correctos,
            SUM(CASE WHEN r.resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS intentos_incorrectos,
            ROUND(100.0 * SUM(CASE WHEN r.resultado_intento = 'correcto' THEN 1 ELSE 0 END)
                / NULLIF(SUM(CASE WHEN r.resultado_intento IN ('correcto', 'incorrecto') THEN 1 ELSE 0 END), 0), 1)
            AS tasa_exito_pct,
            COALESCE(SUM(r.puntos_otorgados), 0) AS puntos_otorgados_historial,
            MAX(r.fecha_hora_evento) AS ultima_actividad
        FROM colaboradores c
        LEFT JOIN puntos_colaborador p ON p.id_colaborador = c.id_colaborador
        LEFT JOIN registro_intentos r ON r.id_colaborador = c.id_colaborador
        GROUP BY c.id_colaborador, c.nombre, c.username_telegram, c.es_semilla,
                 p.puntos_totales, p.aciertos_primera, p.sesiones_completadas
        HAVING COUNT(r.id) > 0 OR COALESCE(p.puntos_totales, 0) > 0
        ORDER BY puntos_totales DESC, aciertos_primera DESC, total_intentos DESC
        """
    )
    df = _ensure_colaborador_cols(df)
    if not df.empty:
        df = df.copy()
        df.insert(0, "posicion", range(1, len(df) + 1))
        if "nombre" not in df.columns:
            df["nombre"] = df["colaborador"]
    return df


def intentos_de_colaborador(id_colaborador: str, limit: int = 15) -> pd.DataFrame:
    df = _query(
        """
        SELECT
            datetime(r.fecha_hora_evento) AS fecha,
            r.id_sesion,
            r.numero_intento,
            r.id_caneca,
            r.caneca_qr,
            r.prediccion_ia,
            ROUND(r.nivel_confianza * 100, 1) AS confianza_pct,
            r.resultado_intento AS resultado,
            r.puntos_otorgados AS puntos,
            r.acierto_primera AS acierto_1ra
        FROM registro_intentos r
        WHERE r.id_colaborador = ?
        ORDER BY r.fecha_hora_evento DESC
        LIMIT ?
        """,
        (id_colaborador, limit),
    )
    return df


def intentos_en_el_tiempo(
    area: str | None = None,
    id_colaborador: str | None = None,
    id_caneca: str | None = None,
) -> pd.DataFrame:
    conditions: list[str] = []
    params: list[str] = []
    if area:
        conditions.append("area = ?")
        params.append(area)
    if id_colaborador:
        conditions.append("id_colaborador = ?")
        params.append(id_colaborador)
    if id_caneca:
        conditions.append("id_caneca = ?")
        params.append(id_caneca)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return _query(
        f"""
        SELECT
            date(fecha_hora_evento) AS fecha,
            SUM(CASE WHEN resultado_intento = 'correcto' THEN 1 ELSE 0 END) AS correctos,
            SUM(CASE WHEN resultado_intento = 'incorrecto' THEN 1 ELSE 0 END) AS incorrectos,
            COUNT(*) AS total
        FROM registro_intentos
        {where}
        GROUP BY date(fecha_hora_evento)
        ORDER BY fecha
        """,
        tuple(params),
    )


def opciones_filtro_actividad() -> dict[str, pd.DataFrame]:
    """Listas para segmentar la actividad diaria por área, usuario y caneca."""
    return {
        "areas": _query(
            """
            SELECT DISTINCT area
            FROM registro_intentos
            WHERE area IS NOT NULL AND area != ''
            ORDER BY area
            """
        ),
        "colaboradores": _query(
            """
            SELECT DISTINCT
                r.id_colaborador,
                COALESCE(c.nombre, r.id_colaborador) AS colaborador,
                c.username_telegram
            FROM registro_intentos r
            LEFT JOIN colaboradores c ON c.id_colaborador = r.id_colaborador
            ORDER BY colaborador
            """
        ),
        "canecas": _query(
            """
            SELECT DISTINCT id_caneca, caneca_qr, area
            FROM registro_intentos
            WHERE id_caneca IS NOT NULL AND id_caneca != ''
            ORDER BY id_caneca
            """
        ),
    }


def ultimos_intentos(limit: int = 20) -> pd.DataFrame:
    df = _query(
        """
        SELECT
            datetime(r.fecha_hora_evento) AS fecha,
            r.id_colaborador,
            COALESCE(c.nombre, r.id_colaborador) AS colaborador,
            c.username_telegram,
            r.id_caneca,
            r.caneca_qr,
            r.prediccion_ia,
            ROUND(r.nivel_confianza * 100, 1) AS confianza_pct,
            r.resultado_intento AS resultado,
            r.puntos_otorgados AS puntos,
            r.tiempo_respuesta_ms AS latencia_ms
        FROM registro_intentos r
        LEFT JOIN colaboradores c ON c.id_colaborador = r.id_colaborador
        ORDER BY r.fecha_hora_evento DESC
        LIMIT ?
        """,
        (limit,),
    )
    return _ensure_colaborador_cols(df)


def inventario_canecas() -> pd.DataFrame:
    return _query(
        """
        SELECT id_caneca, area, color_caneca, estado_caneca
        FROM catalogo_canecas
        ORDER BY color_caneca, id_caneca
        """
    )
