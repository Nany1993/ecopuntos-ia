"""Bot de Telegram — interfaz principal del prototipo."""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import re
import sys
from pathlib import Path

from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.config import settings
from src.services.session_service import SessionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CANECA_PATTERN = re.compile(r"CAN-[A-Z]+-\d+", re.IGNORECASE)
LOCK_PATH = Path(settings.sqlite_path).parent / "bot.lock"
INTERVALO_CIERRE_SESIONES_SEG = 60


async def _iniciar_monitor_sesiones(app: Application) -> None:
    async def _loop_monitor() -> None:
        while True:
            await asyncio.sleep(INTERVALO_CIERRE_SESIONES_SEG)
            try:
                for id_colaborador, mensaje in app.bot_data["service"].cerrar_sesiones_expiradas():
                    try:
                        await app.bot.send_message(
                            chat_id=int(id_colaborador),
                            text=mensaje,
                            parse_mode="Markdown",
                        )
                    except Exception:
                        logger.exception(
                            "No se pudo notificar cierre de sesión a %s", id_colaborador
                        )
            except Exception:
                logger.exception("Error en monitor de sesiones expiradas")

    asyncio.create_task(_loop_monitor())


def _proceso_activo(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _liberar_lock() -> None:
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _adquirir_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        try:
            pid_previo = int(LOCK_PATH.read_text(encoding="utf-8").strip())
        except ValueError:
            pid_previo = 0
        if _proceso_activo(pid_previo) and pid_previo != os.getpid():
            logger.error(
                "Bot ya en ejecucion (PID %s). Cierra la otra terminal o ejecuta: .\\scripts\\stop_bot.ps1",
                pid_previo,
            )
            sys.exit(1)
        _liberar_lock()

    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(_liberar_lock)


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.error(
            "409 Conflict: hay otra instancia del bot con el mismo token. "
            "Ejecuta .\\scripts\\stop_bot.ps1 y vuelve a iniciar."
        )
        return
    logger.exception("Error en el bot", exc_info=context.error)


def _extraer_id_caneca(texto: str) -> str | None:
    if not texto:
        return None
    match = CANECA_PATTERN.search(texto)
    if match:
        return match.group(0).upper()
    # deep link: /start CAN-BLANCA-01
    parts = texto.strip().split()
    if len(parts) >= 2 and parts[0].startswith("/start"):
        candidato = parts[1].strip()
        if CANECA_PATTERN.fullmatch(candidato):
            return candidato.upper()
    return None


def _es_confirmacion_positiva(texto: str) -> bool:
    return texto.strip().lower() in {"si", "sí", "yes", "y", "confirmo", "confirmar", "ok"}


def _es_confirmacion_negativa(texto: str) -> bool:
    return texto.strip().lower() in {"no", "n", "cancelar"}


def _persistir_usuario(update: Update, service: SessionService) -> None:
    """Registra o actualiza al colaborador por su ID único de Telegram."""
    user = update.effective_user
    if not user:
        return
    service.db.upsert_colaborador(
        id_colaborador=str(user.id),
        nombre=user.full_name or user.first_name or f"Colaborador {user.id}",
        username_telegram=user.username,
        es_semilla=False,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    user_id = str(update.effective_user.id)
    texto = update.message.text if update.message else ""
    id_caneca = _extraer_id_caneca(texto)

    if not id_caneca:
        await update.message.reply_text(
            "👋 Bienvenido a *ECOPUNTOS IA*.\n\n"
            "Escanea el QR de una caneca para iniciar, o usa:\n"
            "`/start CAN-BLANCA-01`\n\n"
            "Comandos:\n"
            "• /canecas — ver ubicaciones\n"
            "• /ayuda — guía rápida",
            parse_mode="Markdown",
        )
        return

    resultado = service.iniciar_sesion(user_id, id_caneca)
    await update.message.reply_text(resultado.mensaje, parse_mode="Markdown")


async def cmd_canecas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    msg = service.consultar_canecas()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *Cómo usar ECOPUNTOS IA*\n\n"
        "1. Escanea el QR de la caneca donde piensas depositar.\n"
        "2. Envía una foto del residuo.\n"
        "3. El *agente IA* clasifica según la Resolución 2184 de 2019 (Código de Colores Colombia).\n"
        "4. Si es correcto, confirma el depósito y gana *EcoPuntos* (acierto a la 1ra).\n"
        "5. Si es incorrecto, escanea la caneca recomendada — *no hace falta otra foto*.\n\n"
        "Comandos:\n"
        "• /puntos — ver tus EcoPuntos\n"
        "• /ranking — tabla de líderes\n"
        "• /canecas — ubicaciones",
        parse_mode="Markdown",
    )


async def cmd_puntos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    user_id = str(update.effective_user.id)
    msg = service.consultar_puntos(user_id)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    msg = service.consultar_ranking()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    user_id = str(update.effective_user.id)

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = bytes(await file.download_as_bytearray())

    resultado = service.procesar_foto(user_id, image_bytes, mime_type="image/jpeg")
    await update.message.reply_text(resultado.mensaje, parse_mode="Markdown")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: SessionService = context.bot_data["service"]
    _persistir_usuario(update, service)
    user_id = str(update.effective_user.id)
    texto = update.message.text or ""

    id_caneca = _extraer_id_caneca(texto)
    if id_caneca:
        resultado = service.cambiar_caneca(user_id, id_caneca)
        await update.message.reply_text(resultado.mensaje, parse_mode="Markdown")
        return

    if _es_confirmacion_positiva(texto):
        resultado = service.confirmar_deposito(user_id, True)
        await update.message.reply_text(resultado.mensaje, parse_mode="Markdown")
        return

    if _es_confirmacion_negativa(texto):
        resultado = service.confirmar_deposito(user_id, False)
        await update.message.reply_text(resultado.mensaje, parse_mode="Markdown")
        return

    if "donde" in texto.lower() and "caneca" in texto.lower():
        msg = service.consultar_canecas()
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    await update.message.reply_text(
        "No entendí el mensaje. Escanea un QR, envía una foto o escribe *sí*/*no* para confirmar.",
        parse_mode="Markdown",
    )


def build_application() -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN no configurado en .env")

    app = Application.builder().token(settings.telegram_bot_token).post_init(_iniciar_monitor_sesiones).build()
    app.bot_data["service"] = SessionService()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("canecas", cmd_canecas))
    app.add_handler(CommandHandler("puntos", cmd_puntos))
    app.add_handler(CommandHandler("ranking", cmd_ranking))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(_on_error)

    return app


def main() -> None:
    _adquirir_lock()
    app = build_application()
    logger.info("ECOPUNTOS IA - bot iniciado (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
