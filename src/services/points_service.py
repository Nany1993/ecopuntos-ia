"""Lógica de EcoPuntos — recompensa por acierto a la primera."""

from __future__ import annotations

from src.config import settings
from src.models import PuntosColaborador, Sesion


def calcular_puntos_sesion(sesion: Sesion) -> tuple[int, bool]:
    """
    Otorga puntos solo si la sesión se cierra exitosamente en el primer intento.
    Retorna (puntos, acierto_primera).
    """
    acierto_primera = sesion.numero_intento_actual == 1
    if acierto_primera:
        return settings.puntos_acierto_primera, True
    return 0, False


def formatear_consulta_puntos(puntos: PuntosColaborador) -> str:
    return (
        f"💰 Tus **EcoPuntos**: {puntos.puntos_totales}\n"
        f"🎯 Aciertos al 1er intento: {puntos.aciertos_primera}\n"
        f"✅ Sesiones completadas: {puntos.sesiones_completadas}\n\n"
        f"💡 Clasifica bien **a la primera** y gana **{settings.puntos_acierto_primera}** puntos."
    )


def formatear_resumen_puntos(puntos: PuntosColaborador, puntos_ganados: int) -> str:
    if puntos_ganados > 0:
        return (
            f"🏆 ¡+{puntos_ganados} EcoPuntos por acertar a la primera!\n"
            f"💰 Total acumulado: **{puntos.puntos_totales}** puntos\n"
            f"🎯 Aciertos al primer intento: **{puntos.aciertos_primera}**"
        )
    return (
        "✅ Sesión completada.\n"
        f"💰 Total acumulado: **{puntos.puntos_totales}** EcoPuntos\n"
        "💡 Tip: acierta a la primera para ganar "
        f"**{settings.puntos_acierto_primera}** puntos extra."
    )


def formatear_ranking(ranking: list[PuntosColaborador]) -> str:
    if not ranking:
        return "🏅 Aún no hay puntos registrados. ¡Sé el primero en clasificar bien!"
    lineas = ["🏅 **Ranking EcoPuntos**\n"]
    for i, row in enumerate(ranking, start=1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        etiqueta = row.nombre or f"ID {row.id_colaborador}"
        if row.username_telegram:
            etiqueta += f" (@{row.username_telegram})"
        lineas.append(
            f"{emoji} **{etiqueta}** — "
            f"**{row.puntos_totales}** pts ({row.aciertos_primera} aciertos 1er intento)"
        )
    return "\n".join(lineas)
