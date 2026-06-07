"""Orquestación de sesiones e intentos SmartSort."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.config import settings
from src.database import Database, get_database
from src.models import (
    EstadoSesion,
    RegistroIntento,
    Sesion,
)
from src.models import ClasificacionIA
from src.services.classifier import clasificar_imagen
from src.services import messages
from src.services.points_service import calcular_puntos_sesion, formatear_resumen_puntos


@dataclass
class ResultadoFlujo:
    mensaje: str
    sesion: Sesion
    intento: RegistroIntento | None = None
    requiere_foto: bool = False
    requiere_confirmacion: bool = False
    puntos_ganados: int = 0
    puntos_totales: int = 0


_ESTADOS_SESION_EN_PROGRESO = (
    EstadoSesion.ABIERTA_ESPERANDO_FOTO,
    EstadoSesion.ABIERTA_CLASIFICACION_INCORRECTA,
)


class SessionService:
    def __init__(self, db: Database | None = None):
        self.db = db or get_database()

    def iniciar_sesion(self, id_colaborador: str, id_caneca: str) -> ResultadoFlujo:
        caneca = self.db.get_caneca(id_caneca)
        if not caneca:
            return ResultadoFlujo(
                mensaje=messages.mensaje_error_tecnico("QR_NO_EXISTE"),
                sesion=Sesion.nueva(id_colaborador, id_caneca),
            )

        sesion_activa, cierre = self._obtener_sesion_validada(id_colaborador)
        if cierre:
            return cierre

        if sesion_activa:
            if sesion_activa.estado_sesion == EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION:
                return ResultadoFlujo(
                    mensaje=(
                        "Tienes una clasificación correcta pendiente. "
                        "Responde *sí* o *no* para confirmar si ya depositaste el residuo."
                    ),
                    sesion=sesion_activa,
                    requiere_confirmacion=True,
                )
            if sesion_activa.estado_sesion in _ESTADOS_SESION_EN_PROGRESO:
                return self.cambiar_caneca(id_colaborador, id_caneca)

        sesion = Sesion.nueva(id_colaborador, id_caneca)
        sesion.id_caneca_actual = id_caneca
        self.db.save_sesion(sesion)

        return ResultadoFlujo(
            mensaje=messages.mensaje_bienvenida(id_caneca, caneca.area, caneca.color_caneca),
            sesion=sesion,
            requiere_foto=True,
        )

    def clasificar_con_agente_ia(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> tuple[ClasificacionIA, int]:
        inicio = time.perf_counter()
        clasificacion = clasificar_imagen(image_bytes, mime_type)
        latencia = int((time.perf_counter() - inicio) * 1000)
        return clasificacion, latencia

    def emitir_veredicto(
        self,
        id_colaborador: str,
        clasificacion: ClasificacionIA,
        latencia_ia_ms: int = 0,
        id_caneca_override: str | None = None,
    ) -> ResultadoFlujo:
        sesion, cierre = self._obtener_sesion_validada(id_colaborador)
        if cierre:
            return cierre
        if not sesion:
            return ResultadoFlujo(
                mensaje="Escanea primero el QR de una caneca para iniciar sesión.",
                sesion=Sesion.nueva(id_colaborador, "UNKNOWN"),
            )

        id_caneca = id_caneca_override or sesion.id_caneca_actual or sesion.id_caneca_inicial
        caneca = self.db.get_caneca(id_caneca)
        if not caneca:
            return ResultadoFlujo(
                mensaje=messages.mensaje_error_tecnico("QR_NO_EXISTE"),
                sesion=sesion,
            )

        sesion.numero_intento_actual += 1
        sesion.id_caneca_actual = id_caneca

        try:
            coincide = clasificacion.prediccion_ia == caneca.color_caneca
            if coincide:
                sesion.estado_sesion = EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION
                resultado = "correcto"
                tipo_msg = "motivacional"
                msg = messages.mensaje_correcto(
                    clasificacion.prediccion_ia,
                    caneca.area,
                    clasificacion.nivel_confianza,
                    clasificacion.explicacion_breve,
                )
                requiere_confirmacion = True
            else:
                sesion.estado_sesion = EstadoSesion.ABIERTA_CLASIFICACION_INCORRECTA
                resultado = "incorrecto"
                tipo_msg = "correctivo"
                caneca_recomendada = self._buscar_caneca_por_color(clasificacion.prediccion_ia)
                msg = messages.mensaje_incorrecto(
                    caneca.color_caneca,
                    clasificacion.prediccion_ia,
                    caneca.area,
                    clasificacion.nivel_confianza,
                    clasificacion.explicacion_breve,
                    caneca_recomendada.id_caneca if caneca_recomendada else None,
                )
                requiere_confirmacion = False

                if sesion.numero_intento_actual >= settings.maximo_intentos:
                    sesion.estado_sesion = EstadoSesion.CERRADA_POR_MAXIMO_INTENTOS
                    msg += "\n\n" + messages.mensaje_sesion_cerrada(
                        EstadoSesion.CERRADA_POR_MAXIMO_INTENTOS
                    )

            intento = RegistroIntento(
                id_sesion=sesion.id_sesion,
                numero_intento=sesion.numero_intento_actual,
                fecha_hora_evento=datetime.utcnow(),
                id_colaborador=id_colaborador,
                id_caneca=id_caneca,
                caneca_qr=caneca.color_caneca,
                area=caneca.area,
                prediccion_ia=clasificacion.prediccion_ia,
                nivel_confianza=clasificacion.nivel_confianza,
                explicacion_breve=clasificacion.explicacion_breve,
                resultado_intento=resultado,
                mensaje_enviado=tipo_msg,
                confirmacion_deposito=None,
                tiempo_respuesta_ms=latencia_ia_ms,
                estado_sesion=sesion.estado_sesion,
                proveedor_ia=clasificacion.proveedor_ia,
                respaldo_activado=clasificacion.respaldo_activado,
                codigo_error=None if resultado != "error" else "MISMATCH_QR_IA",
            )

        except Exception as exc:
            sesion.estado_sesion = EstadoSesion.CERRADA_POR_ERROR_TECNICO
            intento = RegistroIntento(
                id_sesion=sesion.id_sesion,
                numero_intento=sesion.numero_intento_actual,
                fecha_hora_evento=datetime.utcnow(),
                id_colaborador=id_colaborador,
                id_caneca=id_caneca,
                caneca_qr=caneca.color_caneca,
                area=caneca.area,
                prediccion_ia=None,
                nivel_confianza=None,
                explicacion_breve=None,
                resultado_intento="error",
                mensaje_enviado="error_tecnico",
                confirmacion_deposito=None,
                tiempo_respuesta_ms=latencia_ia_ms,
                estado_sesion=sesion.estado_sesion,
                proveedor_ia=None,
                respaldo_activado=False,
                codigo_error=f"IA_ERROR:{type(exc).__name__}",
            )
            self.db.save_intento(intento)
            sesion.actualizada_en = datetime.utcnow()
            self.db.save_sesion(sesion)
            return ResultadoFlujo(
                mensaje=(
                    messages.mensaje_error_tecnico(intento.codigo_error or "IA_ERROR")
                    + "\n\n"
                    + messages.mensaje_sesion_cerrada(EstadoSesion.CERRADA_POR_ERROR_TECNICO)
                ),
                sesion=sesion,
                intento=intento,
            )

        sesion.actualizada_en = datetime.utcnow()
        self.db.save_sesion(sesion)
        self.db.save_intento(intento)

        return ResultadoFlujo(
            mensaje=msg,
            sesion=sesion,
            intento=intento,
            requiere_confirmacion=requiere_confirmacion,
            requiere_foto=False,
        )

    def procesar_foto(
        self,
        id_colaborador: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        id_caneca_override: str | None = None,
    ) -> ResultadoFlujo:
        try:
            clasificacion, latencia = self.clasificar_con_agente_ia(image_bytes, mime_type)
        except Exception as exc:
            sesion, cierre = self._obtener_sesion_validada(id_colaborador)
            if cierre:
                return cierre
            if not sesion:
                return ResultadoFlujo(
                    mensaje="Escanea primero el QR de una caneca para iniciar sesión.",
                    sesion=Sesion.nueva(id_colaborador, "UNKNOWN"),
                )
            sesion.numero_intento_actual += 1
            sesion.estado_sesion = EstadoSesion.CERRADA_POR_ERROR_TECNICO
            intento = RegistroIntento(
                id_sesion=sesion.id_sesion,
                numero_intento=sesion.numero_intento_actual,
                fecha_hora_evento=datetime.utcnow(),
                id_colaborador=id_colaborador,
                id_caneca=id_caneca_override or sesion.id_caneca_actual or sesion.id_caneca_inicial,
                caneca_qr="",
                area="",
                prediccion_ia=None,
                nivel_confianza=None,
                explicacion_breve=None,
                resultado_intento="error",
                mensaje_enviado="error_tecnico",
                confirmacion_deposito=None,
                tiempo_respuesta_ms=0,
                estado_sesion=sesion.estado_sesion,
                proveedor_ia=None,
                respaldo_activado=False,
                codigo_error=f"IA_ERROR:{type(exc).__name__}",
            )
            self.db.save_intento(intento)
            self.db.save_sesion(sesion)
            return ResultadoFlujo(
                mensaje=(
                    messages.mensaje_error_tecnico(intento.codigo_error or "IA_ERROR")
                    + "\n\n"
                    + messages.mensaje_sesion_cerrada(EstadoSesion.CERRADA_POR_ERROR_TECNICO)
                ),
                sesion=sesion,
                intento=intento,
            )

        return self.emitir_veredicto(
            id_colaborador,
            clasificacion,
            latencia_ia_ms=latencia,
            id_caneca_override=id_caneca_override,
        )

    def confirmar_deposito(self, id_colaborador: str, confirmado: bool) -> ResultadoFlujo:
        sesion, cierre = self._obtener_sesion_validada(id_colaborador)
        if cierre:
            return cierre
        if not sesion:
            return ResultadoFlujo(
                mensaje="No hay sesión activa.",
                sesion=Sesion.nueva(id_colaborador, "UNKNOWN"),
            )

        if sesion.estado_sesion != EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION:
            return ResultadoFlujo(
                mensaje="No hay confirmación pendiente en esta sesión.",
                sesion=sesion,
            )

        if confirmado:
            sesion.estado_sesion = EstadoSesion.CERRADA_EXITOSA
            puntos, acierto_primera = calcular_puntos_sesion(sesion)
            puntos_colab = self.db.registrar_puntos_sesion(
                id_colaborador,
                sesion.id_sesion,
                puntos,
                acierto_primera,
            )
            msg = formatear_resumen_puntos(puntos_colab, puntos)
        else:
            sesion.estado_sesion = EstadoSesion.ABIERTA_ESPERANDO_FOTO
            msg = "Entendido. Envía otra foto cuando deposites el residuo."
            puntos = 0
            puntos_colab = self.db.get_puntos_colaborador(id_colaborador)

        sesion.actualizada_en = datetime.utcnow()
        self.db.save_sesion(sesion)

        return ResultadoFlujo(
            mensaje=msg,
            sesion=sesion,
            puntos_ganados=puntos if confirmado else 0,
            puntos_totales=puntos_colab.puntos_totales,
        )

    def consultar_puntos(self, id_colaborador: str) -> str:
        from src.services.points_service import formatear_consulta_puntos

        puntos = self.db.get_puntos_colaborador(id_colaborador)
        return formatear_consulta_puntos(puntos)

    def consultar_ranking(self, limit: int = 10) -> str:
        from src.services.points_service import formatear_ranking

        return formatear_ranking(self.db.get_ranking_puntos(limit))

    def cambiar_caneca(self, id_colaborador: str, id_caneca: str) -> ResultadoFlujo:
        sesion, cierre = self._obtener_sesion_validada(id_colaborador)
        if cierre:
            return cierre
        if not sesion:
            return self.iniciar_sesion(id_colaborador, id_caneca)

        caneca = self.db.get_caneca(id_caneca)
        if not caneca:
            return ResultadoFlujo(
                mensaje=messages.mensaje_error_tecnico("QR_NO_EXISTE"),
                sesion=sesion,
            )

        if sesion.estado_sesion == EstadoSesion.ABIERTA_CLASIFICACION_INCORRECTA:
            clasificacion = self._clasificacion_ultimo_intento(sesion.id_sesion)
            if clasificacion:
                resultado = self.emitir_veredicto(
                    id_colaborador,
                    clasificacion,
                    latencia_ia_ms=0,
                    id_caneca_override=id_caneca,
                )
                resultado.mensaje = (
                    messages.mensaje_reintento_caneca(id_caneca, caneca.area, caneca.color_caneca)
                    + "\n\n"
                    + resultado.mensaje
                )
                return resultado

        sesion.id_caneca_actual = id_caneca
        sesion.estado_sesion = EstadoSesion.ABIERTA_ESPERANDO_FOTO
        sesion.actualizada_en = datetime.utcnow()
        self.db.save_sesion(sesion)

        return ResultadoFlujo(
            mensaje=messages.mensaje_bienvenida(id_caneca, caneca.area, caneca.color_caneca),
            sesion=sesion,
            requiere_foto=True,
        )

    def consultar_canecas(self, color: str | None = None) -> str:
        canecas = self.db.list_canecas(color)
        lineas = [f"{c.id_caneca} — {c.area} ({c.color_caneca})" for c in canecas]
        return messages.mensaje_ayuda_canecas(lineas)

    def cerrar_sesiones_expiradas(self) -> list[tuple[str, str]]:
        """Cierra sesiones vencidas y retorna notificaciones para enviar por Telegram."""
        notificaciones: list[tuple[str, str]] = []
        for sesion in self.db.list_sesiones_activas():
            motivo = self._motivo_expiracion(sesion)
            if not motivo:
                continue
            self._cerrar_sesion(sesion, motivo)
            notificaciones.append(
                (sesion.id_colaborador, messages.mensaje_sesion_cerrada(motivo))
            )
        return notificaciones

    def _obtener_sesion_validada(
        self, id_colaborador: str
    ) -> tuple[Sesion | None, ResultadoFlujo | None]:
        sesion = self.db.get_sesion_activa_colaborador(id_colaborador)
        if not sesion:
            return None, None

        motivo = self._motivo_expiracion(sesion)
        if motivo:
            self._cerrar_sesion(sesion, motivo)
            return None, ResultadoFlujo(
                mensaje=messages.mensaje_sesion_cerrada(motivo),
                sesion=sesion,
            )
        return sesion, None

    def _buscar_caneca_por_color(self, color: str):
        canecas = self.db.list_canecas(color)
        return canecas[0] if canecas else None

    def _clasificacion_ultimo_intento(self, id_sesion: str) -> ClasificacionIA | None:
        intento = self.db.get_ultimo_intento_sesion(id_sesion)
        if not intento or not intento.prediccion_ia or intento.resultado_intento != "incorrecto":
            return None
        return ClasificacionIA(
            prediccion_ia=intento.prediccion_ia,
            nivel_confianza=intento.nivel_confianza or 0.0,
            explicacion_breve=intento.explicacion_breve or "",
            proveedor_ia=intento.proveedor_ia or "reintento",
            respaldo_activado=intento.respaldo_activado,
        )

    def _motivo_expiracion(self, sesion: Sesion) -> EstadoSesion | None:
        ahora = datetime.utcnow()
        max_sesion = timedelta(minutes=settings.tiempo_maximo_sesion_min)
        max_inactividad = timedelta(seconds=settings.tiempo_reintento_seg)
        max_confirmacion = timedelta(minutes=settings.tiempo_confirmacion_min)
        inactivo = ahora - sesion.actualizada_en

        if ahora - sesion.creada_en > max_sesion:
            return EstadoSesion.CERRADA_POR_INACTIVIDAD

        if sesion.estado_sesion == EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION:
            if inactivo > max_confirmacion:
                return EstadoSesion.CERRADA_POR_CONFIRMACION_EXPIRADA
            return None

        if inactivo > max_inactividad:
            return EstadoSesion.CERRADA_POR_INACTIVIDAD

        return None

    def _cerrar_sesion(self, sesion: Sesion, estado: EstadoSesion) -> Sesion:
        sesion.estado_sesion = estado
        sesion.actualizada_en = datetime.utcnow()
        self.db.save_sesion(sesion)
        return sesion
