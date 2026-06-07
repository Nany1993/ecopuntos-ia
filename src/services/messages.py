"""Plantillas de mensajes al colaborador."""

from src.models import ColorCaneca


def mensaje_correcto(prediccion: ColorCaneca, area: str, confianza: float, explicacion: str) -> str:
    pct = int(confianza * 100)
    return (
        f"✅ Excelente. Este residuo corresponde a la caneca **{prediccion}**.\n\n"
        f"Tu acción ayuda a mejorar el reciclaje en **{area}** y reduce contaminación cruzada.\n\n"
        f"📊 Confianza: {pct}%\n"
        f"💡 {explicacion}\n\n"
        f"🏆 Si acertaste a la primera, confirma el depósito y gana EcoPuntos.\n\n"
        "¿Confirmas que depositaste el residuo? Responde *sí* o *no*."
    )


def mensaje_incorrecto(
    caneca_escaneada: ColorCaneca,
    prediccion: ColorCaneca,
    area: str,
    confianza: float,
    explicacion: str,
    id_caneca_recomendada: str | None = None,
) -> str:
    pct = int(confianza * 100)
    extra = ""
    if id_caneca_recomendada:
        extra = f"\n\nEscanea la caneca recomendada: `{id_caneca_recomendada}`"
    return (
        f"⚠️ Este residuo **no** corresponde a la caneca **{caneca_escaneada}** escaneada.\n\n"
        f"Debe ir en la caneca **{prediccion}**.\n"
        f"Segregar correctamente evita pérdidas de material reciclable.\n\n"
        f"📊 Confianza: {pct}%\n"
        f"💡 {explicacion}{extra}\n\n"
        "Envía otra foto del residuo o escanea el QR de la caneca correcta."
    )


def mensaje_error_tecnico(codigo: str) -> str:
    return (
        "❌ No pudimos procesar tu solicitud en este momento.\n"
        f"Código: `{codigo}`\n\n"
        "Intenta de nuevo en unos segundos."
    )


def mensaje_bienvenida(id_caneca: str, area: str, color: ColorCaneca) -> str:
    return (
        f"👋 Sesión iniciada en **{area}** (caneca {color}).\n"
        f"Caneca: `{id_caneca}`\n\n"
        "📸 Envía una foto del residuo que vas a depositar."
    )


def mensaje_sesion_cerrada(razon: str) -> str:
    return f"🔒 Sesión cerrada: {razon}\n\nEscanea un QR de caneca para iniciar una nueva sesión."


def mensaje_ayuda_canecas(canecas_info: list[str]) -> str:
    cuerpo = "\n".join(f"• {linea}" for linea in canecas_info)
    return f"🗺️ Canecas disponibles:\n\n{cuerpo}\n\nEscanea el QR de la caneca que necesites."
