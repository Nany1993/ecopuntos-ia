"""Capa de acceso a datos — SQLite (piloto local) y Supabase (escalamiento)."""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from src.config import settings
from src.models import Caneca, Colaborador, PuntosColaborador, RegistroIntento, ReglaResiduo, Sesion


class Database(ABC):
    @abstractmethod
    def init_schema(self) -> None: ...

    @abstractmethod
    def get_caneca(self, id_caneca: str) -> Caneca | None: ...

    @abstractmethod
    def list_canecas(self, color: str | None = None) -> list[Caneca]: ...

    @abstractmethod
    def get_regla_residuo(self, tipo_residuo: str) -> ReglaResiduo | None: ...

    @abstractmethod
    def save_sesion(self, sesion: Sesion) -> None: ...

    @abstractmethod
    def get_sesion(self, id_sesion: str) -> Sesion | None: ...

    @abstractmethod
    def get_sesion_activa_colaborador(self, id_colaborador: str) -> Sesion | None: ...

    @abstractmethod
    def save_intento(self, intento: RegistroIntento) -> None: ...

    @abstractmethod
    def get_puntos_colaborador(self, id_colaborador: str) -> "PuntosColaborador": ...

    @abstractmethod
    def registrar_puntos_sesion(
        self,
        id_colaborador: str,
        id_sesion: str,
        puntos: int,
        acierto_primera: bool,
    ) -> "PuntosColaborador": ...

    @abstractmethod
    def get_ranking_puntos(self, limit: int = 10) -> list["PuntosColaborador"]: ...

    @abstractmethod
    def upsert_colaborador(
        self,
        id_colaborador: str,
        nombre: str,
        username_telegram: str | None = None,
        es_semilla: bool = False,
    ) -> Colaborador: ...

    @abstractmethod
    def get_colaborador(self, id_colaborador: str) -> Colaborador | None: ...

    @abstractmethod
    def seed_if_empty(self) -> None: ...


def _parse_tipos(value: str | list) -> list[str]:
    if isinstance(value, list):
        return value
    return json.loads(value)


class SQLiteDatabase(Database):
    def __init__(self, path: str | None = None):
        self.path = Path(path or settings.sqlite_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "sql" / "schema_sqlite.sql"
        with self._connect() as conn, schema_path.open(encoding="utf-8") as f:
            conn.executescript(f.read())
            conn.commit()
        self._migrate_schema()

    def _migrate_schema(self) -> None:
        with self._connect() as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(registro_intentos)")}
            if "acierto_primera" not in cols:
                conn.execute("ALTER TABLE registro_intentos ADD COLUMN acierto_primera INTEGER NOT NULL DEFAULT 0")
            if "puntos_otorgados" not in cols:
                conn.execute("ALTER TABLE registro_intentos ADD COLUMN puntos_otorgados INTEGER NOT NULL DEFAULT 0")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS puntos_colaborador (
                    id_colaborador TEXT PRIMARY KEY,
                    puntos_totales INTEGER NOT NULL DEFAULT 0,
                    aciertos_primera INTEGER NOT NULL DEFAULT 0,
                    sesiones_completadas INTEGER NOT NULL DEFAULT 0,
                    ultima_actualizacion TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS colaboradores (
                    id_colaborador TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    username_telegram TEXT,
                    es_semilla INTEGER NOT NULL DEFAULT 0,
                    registrado_en TEXT NOT NULL,
                    ultima_actividad TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_caneca(self, id_caneca: str) -> Caneca | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM catalogo_canecas WHERE id_caneca = ? AND estado_caneca = 'activa'",
                (id_caneca,),
            ).fetchone()
        if not row:
            return None
        return Caneca(
            id_caneca=row["id_caneca"],
            area=row["area"],
            color_caneca=row["color_caneca"],
            tipos_residuo_permitidos=_parse_tipos(row["tipos_residuo_permitidos"]),
            estado_caneca=row["estado_caneca"],
            latitud=row["latitud"],
            longitud=row["longitud"],
        )

    def list_canecas(self, color: str | None = None) -> list[Caneca]:
        query = "SELECT * FROM catalogo_canecas WHERE estado_caneca = 'activa'"
        params: tuple = ()
        if color:
            query += " AND color_caneca = ?"
            params = (color,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            Caneca(
                id_caneca=r["id_caneca"],
                area=r["area"],
                color_caneca=r["color_caneca"],
                tipos_residuo_permitidos=_parse_tipos(r["tipos_residuo_permitidos"]),
                estado_caneca=r["estado_caneca"],
                latitud=r["latitud"],
                longitud=r["longitud"],
            )
            for r in rows
        ]

    def get_regla_residuo(self, tipo_residuo: str) -> ReglaResiduo | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reglas_residuos WHERE LOWER(tipo_residuo) = LOWER(?)",
                (tipo_residuo,),
            ).fetchone()
        if not row:
            return None
        return ReglaResiduo(
            tipo_residuo=row["tipo_residuo"],
            caneca_recomendada=row["caneca_recomendada"],
            mensaje_educativo=row["mensaje_educativo"],
        )

    def save_sesion(self, sesion: Sesion) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sesiones (
                    id_sesion, id_colaborador, id_caneca_inicial, id_caneca_actual,
                    estado_sesion, numero_intento_actual, creada_en, actualizada_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_sesion) DO UPDATE SET
                    id_caneca_actual = excluded.id_caneca_actual,
                    estado_sesion = excluded.estado_sesion,
                    numero_intento_actual = excluded.numero_intento_actual,
                    actualizada_en = excluded.actualizada_en
                """,
                (
                    sesion.id_sesion,
                    sesion.id_colaborador,
                    sesion.id_caneca_inicial,
                    sesion.id_caneca_actual,
                    sesion.estado_sesion.value,
                    sesion.numero_intento_actual,
                    sesion.creada_en.isoformat(),
                    sesion.actualizada_en.isoformat(),
                ),
            )
            conn.commit()

    def get_sesion(self, id_sesion: str) -> Sesion | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sesiones WHERE id_sesion = ?", (id_sesion,)).fetchone()
        return self._row_to_sesion(row) if row else None

    def get_sesion_activa_colaborador(self, id_colaborador: str) -> Sesion | None:
        estados_cerrados = (
            "CERRADA_EXITOSA",
            "CERRADA_POR_INACTIVIDAD",
            "CERRADA_POR_MAXIMO_INTENTOS",
            "CERRADA_POR_ERROR_TECNICO",
        )
        placeholders = ",".join("?" * len(estados_cerrados))
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT * FROM sesiones
                WHERE id_colaborador = ?
                  AND estado_sesion NOT IN ({placeholders})
                ORDER BY actualizada_en DESC
                LIMIT 1
                """,
                (id_colaborador, *estados_cerrados),
            ).fetchone()
        return self._row_to_sesion(row) if row else None

    def save_intento(self, intento: RegistroIntento) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO registro_intentos (
                    id_sesion, numero_intento, fecha_hora_evento, id_colaborador,
                    id_caneca, caneca_qr, area, tipos_residuo_permitidos,
                    prediccion_ia, nivel_confianza, explicacion_breve,
                    resultado_intento, mensaje_enviado, confirmacion_deposito,
                    tiempo_respuesta_ms, estado_sesion, proveedor_ia,
                    respaldo_activado, codigo_error, acierto_primera, puntos_otorgados
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intento.id_sesion,
                    intento.numero_intento,
                    intento.fecha_hora_evento.isoformat(),
                    intento.id_colaborador,
                    intento.id_caneca,
                    intento.caneca_qr,
                    intento.area,
                    json.dumps(intento.tipos_residuo_permitidos, ensure_ascii=False),
                    intento.prediccion_ia,
                    intento.nivel_confianza,
                    intento.explicacion_breve,
                    intento.resultado_intento,
                    intento.mensaje_enviado,
                    intento.confirmacion_deposito,
                    intento.tiempo_respuesta_ms,
                    intento.estado_sesion.value,
                    intento.proveedor_ia,
                    intento.respaldo_activado,
                    intento.codigo_error,
                    int(intento.acierto_primera),
                    intento.puntos_otorgados,
                ),
            )
            conn.commit()

    def get_puntos_colaborador(self, id_colaborador: str) -> PuntosColaborador:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM puntos_colaborador WHERE id_colaborador = ?",
                (id_colaborador,),
            ).fetchone()
        if not row:
            return PuntosColaborador(id_colaborador=id_colaborador)
        return PuntosColaborador(
            id_colaborador=row["id_colaborador"],
            puntos_totales=row["puntos_totales"],
            aciertos_primera=row["aciertos_primera"],
            sesiones_completadas=row["sesiones_completadas"],
            ultima_actualizacion=datetime.fromisoformat(row["ultima_actualizacion"]),
        )

    def registrar_puntos_sesion(
        self,
        id_colaborador: str,
        id_sesion: str,
        puntos: int,
        acierto_primera: bool,
    ) -> PuntosColaborador:
        ahora = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE registro_intentos
                SET confirmacion_deposito = 1,
                    acierto_primera = ?,
                    puntos_otorgados = ?
                WHERE id_sesion = ? AND numero_intento = (
                    SELECT MAX(numero_intento) FROM registro_intentos WHERE id_sesion = ?
                )
                """,
                (int(acierto_primera), puntos, id_sesion, id_sesion),
            )
            conn.execute(
                """
                INSERT INTO puntos_colaborador (
                    id_colaborador, puntos_totales, aciertos_primera,
                    sesiones_completadas, ultima_actualizacion
                ) VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(id_colaborador) DO UPDATE SET
                    puntos_totales = puntos_totales + excluded.puntos_totales,
                    aciertos_primera = aciertos_primera + excluded.aciertos_primera,
                    sesiones_completadas = sesiones_completadas + 1,
                    ultima_actualizacion = excluded.ultima_actualizacion
                """,
                (
                    id_colaborador,
                    puntos,
                    1 if acierto_primera else 0,
                    ahora,
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM puntos_colaborador WHERE id_colaborador = ?",
                (id_colaborador,),
            ).fetchone()
        return PuntosColaborador(
            id_colaborador=row["id_colaborador"],
            puntos_totales=row["puntos_totales"],
            aciertos_primera=row["aciertos_primera"],
            sesiones_completadas=row["sesiones_completadas"],
            ultima_actualizacion=datetime.fromisoformat(row["ultima_actualizacion"]),
        )

    def get_ranking_puntos(self, limit: int = 10) -> list[PuntosColaborador]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    p.*,
                    c.nombre,
                    c.username_telegram
                FROM puntos_colaborador p
                LEFT JOIN colaboradores c ON c.id_colaborador = p.id_colaborador
                ORDER BY p.puntos_totales DESC, p.aciertos_primera DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            PuntosColaborador(
                id_colaborador=r["id_colaborador"],
                puntos_totales=r["puntos_totales"],
                aciertos_primera=r["aciertos_primera"],
                sesiones_completadas=r["sesiones_completadas"],
                ultima_actualizacion=datetime.fromisoformat(r["ultima_actualizacion"]),
                nombre=r["nombre"],
                username_telegram=r["username_telegram"],
            )
            for r in rows
        ]

    def upsert_colaborador(
        self,
        id_colaborador: str,
        nombre: str,
        username_telegram: str | None = None,
        es_semilla: bool = False,
    ) -> Colaborador:
        ahora = datetime.utcnow().isoformat()
        with self._connect() as conn:
            existente = conn.execute(
                "SELECT es_semilla FROM colaboradores WHERE id_colaborador = ?",
                (id_colaborador,),
            ).fetchone()
            if existente and existente["es_semilla"]:
                conn.execute(
                    """
                    UPDATE colaboradores
                    SET ultima_actividad = ?
                    WHERE id_colaborador = ?
                    """,
                    (ahora, id_colaborador),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO colaboradores (
                        id_colaborador, nombre, username_telegram,
                        es_semilla, registrado_en, ultima_actividad
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_colaborador) DO UPDATE SET
                        nombre = excluded.nombre,
                        username_telegram = COALESCE(excluded.username_telegram, colaboradores.username_telegram),
                        es_semilla = excluded.es_semilla,
                        ultima_actividad = excluded.ultima_actividad
                    """,
                    (
                        id_colaborador,
                        nombre,
                        username_telegram,
                        int(es_semilla),
                        ahora,
                        ahora,
                    ),
                )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM colaboradores WHERE id_colaborador = ?",
                (id_colaborador,),
            ).fetchone()
        return Colaborador(
            id_colaborador=row["id_colaborador"],
            nombre=row["nombre"],
            username_telegram=row["username_telegram"],
            es_semilla=bool(row["es_semilla"]),
            registrado_en=datetime.fromisoformat(row["registrado_en"]),
            ultima_actividad=datetime.fromisoformat(row["ultima_actividad"]),
        )

    def get_colaborador(self, id_colaborador: str) -> Colaborador | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM colaboradores WHERE id_colaborador = ?",
                (id_colaborador,),
            ).fetchone()
        if not row:
            return None
        return Colaborador(
            id_colaborador=row["id_colaborador"],
            nombre=row["nombre"],
            username_telegram=row["username_telegram"],
            es_semilla=bool(row["es_semilla"]),
            registrado_en=datetime.fromisoformat(row["registrado_en"]),
            ultima_actividad=datetime.fromisoformat(row["ultima_actividad"]),
        )

    def seed_if_empty(self) -> None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM catalogo_canecas").fetchone()[0]
            if count > 0:
                return
        from src.seed_data import CANECAS_SEED, REGLAS_SEED

        with self._connect() as conn:
            for c in CANECAS_SEED:
                conn.execute(
                    """
                    INSERT INTO catalogo_canecas (
                        id_caneca, area, color_caneca, tipos_residuo_permitidos, estado_caneca
                    ) VALUES (?, ?, ?, ?, 'activa')
                    """,
                    (c["id_caneca"], c["area"], c["color_caneca"], json.dumps(c["tipos_residuo_permitidos"])),
                )
            for r in REGLAS_SEED:
                conn.execute(
                    """
                    INSERT INTO reglas_residuos (tipo_residuo, caneca_recomendada, mensaje_educativo)
                    VALUES (?, ?, ?)
                    """,
                    (r["tipo_residuo"], r["caneca_recomendada"], r["mensaje_educativo"]),
                )
            conn.commit()

    @staticmethod
    def _row_to_sesion(row: sqlite3.Row) -> Sesion:
        from src.models import EstadoSesion

        return Sesion(
            id_sesion=row["id_sesion"],
            id_colaborador=row["id_colaborador"],
            id_caneca_inicial=row["id_caneca_inicial"],
            id_caneca_actual=row["id_caneca_actual"],
            estado_sesion=EstadoSesion(row["estado_sesion"]),
            numero_intento_actual=row["numero_intento_actual"],
            creada_en=datetime.fromisoformat(row["creada_en"]),
            actualizada_en=datetime.fromisoformat(row["actualizada_en"]),
        )


class SupabaseDatabase(Database):
    def __init__(self):
        from supabase import create_client

        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY son requeridos para backend supabase")
        self.client = create_client(settings.supabase_url, settings.supabase_key)

    def init_schema(self) -> None:
        raise RuntimeError("Aplica sql/schema.sql en Supabase con apply_migration o el dashboard")

    def get_caneca(self, id_caneca: str) -> Caneca | None:
        res = (
            self.client.table("catalogo_canecas")
            .select("*")
            .eq("id_caneca", id_caneca)
            .eq("estado_caneca", "activa")
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        row = res.data[0]
        return Caneca(
            id_caneca=row["id_caneca"],
            area=row["area"],
            color_caneca=row["color_caneca"],
            tipos_residuo_permitidos=row["tipos_residuo_permitidos"],
            estado_caneca=row["estado_caneca"],
            latitud=row.get("latitud"),
            longitud=row.get("longitud"),
        )

    def list_canecas(self, color: str | None = None) -> list[Caneca]:
        query = self.client.table("catalogo_canecas").select("*").eq("estado_caneca", "activa")
        if color:
            query = query.eq("color_caneca", color)
        res = query.execute()
        return [
            Caneca(
                id_caneca=r["id_caneca"],
                area=r["area"],
                color_caneca=r["color_caneca"],
                tipos_residuo_permitidos=r["tipos_residuo_permitidos"],
                estado_caneca=r["estado_caneca"],
                latitud=r.get("latitud"),
                longitud=r.get("longitud"),
            )
            for r in res.data
        ]

    def get_regla_residuo(self, tipo_residuo: str) -> ReglaResiduo | None:
        res = (
            self.client.table("reglas_residuos")
            .select("*")
            .ilike("tipo_residuo", tipo_residuo)
            .limit(1)
            .execute()
        )
        if not res.data:
            return None
        row = res.data[0]
        return ReglaResiduo(
            tipo_residuo=row["tipo_residuo"],
            caneca_recomendada=row["caneca_recomendada"],
            mensaje_educativo=row["mensaje_educativo"],
        )

    def save_sesion(self, sesion: Sesion) -> None:
        payload = {
            "id_sesion": sesion.id_sesion,
            "id_colaborador": sesion.id_colaborador,
            "id_caneca_inicial": sesion.id_caneca_inicial,
            "id_caneca_actual": sesion.id_caneca_actual,
            "estado_sesion": sesion.estado_sesion.value,
            "numero_intento_actual": sesion.numero_intento_actual,
            "creada_en": sesion.creada_en.isoformat(),
            "actualizada_en": sesion.actualizada_en.isoformat(),
        }
        self.client.table("sesiones").upsert(payload).execute()

    def get_sesion(self, id_sesion: str) -> Sesion | None:
        res = self.client.table("sesiones").select("*").eq("id_sesion", id_sesion).limit(1).execute()
        return self._row_to_sesion(res.data[0]) if res.data else None

    def get_sesion_activa_colaborador(self, id_colaborador: str) -> Sesion | None:
        estados_cerrados = [
            "CERRADA_EXITOSA",
            "CERRADA_POR_INACTIVIDAD",
            "CERRADA_POR_MAXIMO_INTENTOS",
            "CERRADA_POR_ERROR_TECNICO",
        ]
        res = (
            self.client.table("sesiones")
            .select("*")
            .eq("id_colaborador", id_colaborador)
            .not_.in_("estado_sesion", estados_cerrados)
            .order("actualizada_en", desc=True)
            .limit(1)
            .execute()
        )
        return self._row_to_sesion(res.data[0]) if res.data else None

    def save_intento(self, intento: RegistroIntento) -> None:
        payload = {
            "id_sesion": intento.id_sesion,
            "numero_intento": intento.numero_intento,
            "fecha_hora_evento": intento.fecha_hora_evento.isoformat(),
            "id_colaborador": intento.id_colaborador,
            "id_caneca": intento.id_caneca,
            "caneca_qr": intento.caneca_qr,
            "area": intento.area,
            "tipos_residuo_permitidos": intento.tipos_residuo_permitidos,
            "prediccion_ia": intento.prediccion_ia,
            "nivel_confianza": intento.nivel_confianza,
            "explicacion_breve": intento.explicacion_breve,
            "resultado_intento": intento.resultado_intento,
            "mensaje_enviado": intento.mensaje_enviado,
            "confirmacion_deposito": intento.confirmacion_deposito,
            "tiempo_respuesta_ms": intento.tiempo_respuesta_ms,
            "estado_sesion": intento.estado_sesion.value,
            "proveedor_ia": intento.proveedor_ia,
            "respaldo_activado": intento.respaldo_activado,
            "codigo_error": intento.codigo_error,
        }
        self.client.table("registro_intentos").insert(payload).execute()

    def get_puntos_colaborador(self, id_colaborador: str) -> PuntosColaborador:
        res = (
            self.client.table("puntos_colaborador")
            .select("*")
            .eq("id_colaborador", id_colaborador)
            .limit(1)
            .execute()
        )
        if not res.data:
            return PuntosColaborador(id_colaborador=id_colaborador)
        row = res.data[0]
        return PuntosColaborador(
            id_colaborador=row["id_colaborador"],
            puntos_totales=row["puntos_totales"],
            aciertos_primera=row["aciertos_primera"],
            sesiones_completadas=row["sesiones_completadas"],
            ultima_actualizacion=datetime.fromisoformat(row["ultima_actualizacion"]),
        )

    def registrar_puntos_sesion(
        self,
        id_colaborador: str,
        id_sesion: str,
        puntos: int,
        acierto_primera: bool,
    ) -> PuntosColaborador:
        raise NotImplementedError("Usar SQLite en el piloto o aplicar migración puntos en Supabase")

    def get_ranking_puntos(self, limit: int = 10) -> list[PuntosColaborador]:
        res = (
            self.client.table("puntos_colaborador")
            .select("*")
            .order("puntos_totales", desc=True)
            .limit(limit)
            .execute()
        )
        return [
            PuntosColaborador(
                id_colaborador=r["id_colaborador"],
                puntos_totales=r["puntos_totales"],
                aciertos_primera=r["aciertos_primera"],
                sesiones_completadas=r["sesiones_completadas"],
                ultima_actualizacion=datetime.fromisoformat(r["ultima_actualizacion"]),
            )
            for r in res.data
        ]

    def upsert_colaborador(
        self,
        id_colaborador: str,
        nombre: str,
        username_telegram: str | None = None,
        es_semilla: bool = False,
    ) -> Colaborador:
        raise NotImplementedError("Usar SQLite en el piloto")

    def get_colaborador(self, id_colaborador: str) -> Colaborador | None:
        raise NotImplementedError("Usar SQLite en el piloto")

    def seed_if_empty(self) -> None:
        res = self.client.table("catalogo_canecas").select("id_caneca", count="exact").execute()
        if res.count and res.count > 0:
            return
        from src.seed_data import CANECAS_SEED, REGLAS_SEED

        self.client.table("catalogo_canecas").insert(CANECAS_SEED).execute()
        self.client.table("reglas_residuos").insert(REGLAS_SEED).execute()

    @staticmethod
    def _row_to_sesion(row: dict) -> Sesion:
        from src.models import EstadoSesion

        return Sesion(
            id_sesion=row["id_sesion"],
            id_colaborador=row["id_colaborador"],
            id_caneca_inicial=row["id_caneca_inicial"],
            id_caneca_actual=row.get("id_caneca_actual"),
            estado_sesion=EstadoSesion(row["estado_sesion"]),
            numero_intento_actual=row["numero_intento_actual"],
            creada_en=datetime.fromisoformat(row["creada_en"].replace("Z", "+00:00").replace("+00:00", "")),
            actualizada_en=datetime.fromisoformat(row["actualizada_en"].replace("Z", "+00:00").replace("+00:00", "")),
        )


def get_database() -> Database:
    if settings.database_backend.lower() == "supabase":
        return SupabaseDatabase()
    db = SQLiteDatabase()
    db.init_schema()
    db.seed_if_empty()
    return db
