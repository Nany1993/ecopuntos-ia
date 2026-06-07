"""Modelos y constantes del dominio SmartSort."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import uuid4


class EstadoSesion(str, Enum):
    ABIERTA_ESPERANDO_FOTO = "ABIERTA_ESPERANDO_FOTO"
    ABIERTA_CLASIFICACION_INCORRECTA = "ABIERTA_CLASIFICACION_INCORRECTA"
    ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION = "ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION"
    CERRADA_EXITOSA = "CERRADA_EXITOSA"
    CERRADA_POR_INACTIVIDAD = "CERRADA_POR_INACTIVIDAD"
    CERRADA_POR_CONFIRMACION_EXPIRADA = "CERRADA_POR_CONFIRMACION_EXPIRADA"
    CERRADA_POR_MAXIMO_INTENTOS = "CERRADA_POR_MAXIMO_INTENTOS"
    CERRADA_POR_ERROR_TECNICO = "CERRADA_POR_ERROR_TECNICO"


ESTADOS_SESION_CERRADOS = (
    EstadoSesion.CERRADA_EXITOSA,
    EstadoSesion.CERRADA_POR_INACTIVIDAD,
    EstadoSesion.CERRADA_POR_CONFIRMACION_EXPIRADA,
    EstadoSesion.CERRADA_POR_MAXIMO_INTENTOS,
    EstadoSesion.CERRADA_POR_ERROR_TECNICO,
)


ColorCaneca = Literal["blanca", "verde", "negra"]
ResultadoIntento = Literal["correcto", "incorrecto", "error"]
TipoMensaje = Literal["motivacional", "correctivo", "error_tecnico"]


@dataclass
class Caneca:
    id_caneca: str
    area: str
    color_caneca: ColorCaneca
    estado_caneca: str = "activa"
    latitud: float | None = None
    longitud: float | None = None


@dataclass
class ClasificacionIA:
    prediccion_ia: ColorCaneca
    nivel_confianza: float
    explicacion_breve: str
    proveedor_ia: str
    respaldo_activado: bool = False


@dataclass
class Sesion:
    id_sesion: str
    id_colaborador: str
    id_caneca_inicial: str
    estado_sesion: EstadoSesion
    numero_intento_actual: int = 0
    creada_en: datetime = field(default_factory=datetime.utcnow)
    actualizada_en: datetime = field(default_factory=datetime.utcnow)
    id_caneca_actual: str | None = None

    @staticmethod
    def nueva(id_colaborador: str, id_caneca: str) -> Sesion:
        return Sesion(
            id_sesion=f"SES-{uuid4().hex[:12].upper()}",
            id_colaborador=id_colaborador,
            id_caneca_inicial=id_caneca,
            id_caneca_actual=id_caneca,
            estado_sesion=EstadoSesion.ABIERTA_ESPERANDO_FOTO,
        )


@dataclass
class RegistroIntento:
    id_sesion: str
    numero_intento: int
    fecha_hora_evento: datetime
    id_colaborador: str
    id_caneca: str
    caneca_qr: ColorCaneca
    area: str
    prediccion_ia: ColorCaneca | None
    nivel_confianza: float | None
    explicacion_breve: str | None
    resultado_intento: ResultadoIntento
    mensaje_enviado: TipoMensaje
    confirmacion_deposito: bool | None
    tiempo_respuesta_ms: int
    estado_sesion: EstadoSesion
    proveedor_ia: str | None = None
    respaldo_activado: bool = False
    codigo_error: str | None = None
    acierto_primera: bool = False
    puntos_otorgados: int = 0


@dataclass
class PuntosColaborador:
    id_colaborador: str
    puntos_totales: int = 0
    aciertos_primera: int = 0
    sesiones_completadas: int = 0
    ultima_actualizacion: datetime = field(default_factory=datetime.utcnow)
    nombre: str | None = None
    username_telegram: str | None = None


@dataclass
class Colaborador:
    """Usuario persistente identificado por su ID numérico de Telegram."""

    id_colaborador: str
    nombre: str
    username_telegram: str | None = None
    es_semilla: bool = False
    registrado_en: datetime = field(default_factory=datetime.utcnow)
    ultima_actividad: datetime = field(default_factory=datetime.utcnow)


CANECAS_COLORES_VALIDOS = {"blanca", "verde", "negra"}
