"""Prueba rápida del flujo de sesión (reintento + expiración por confirmación)."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.database import SQLiteDatabase
from src.models import ClasificacionIA, EstadoSesion
from src.services.session_service import SessionService


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test.db")
    db = SQLiteDatabase(db_path)
    db.init_schema()
    db.seed_if_empty()
    svc = SessionService(db)
    uid = "test-user-1"

    # Reintento: QR no debe reiniciar sesión
    svc.iniciar_sesion(uid, "CAN-BLANCA-01")
    cl = ClasificacionIA("verde", 0.9, "organico", "test", False)
    r2 = svc.emitir_veredicto(uid, cl)
    sid = r2.sesion.id_sesion
    r3 = svc.iniciar_sesion(uid, "CAN-VERDE-01")
    assert r3.sesion.id_sesion == sid, "Re-escaneo QR debe mantener la sesión"
    assert r3.sesion.numero_intento_actual == 2, "Reintento debe re-evaluar sin nueva foto"
    assert r3.requiere_confirmacion is True
    r5 = svc.confirmar_deposito(uid, True)
    assert r5.puntos_ganados == 0, "2.º intento no debe dar puntos"

    # Expiración por confirmación pendiente (15 min simulados)
    svc.iniciar_sesion(uid, "CAN-VERDE-01")
    cl3 = ClasificacionIA("verde", 0.9, "ok", "test", False)
    r6 = svc.emitir_veredicto(uid, cl3)
    sesion = db.get_sesion(r6.sesion.id_sesion)
    assert sesion is not None
    sesion.actualizada_en = datetime.utcnow() - timedelta(
        minutes=settings.tiempo_confirmacion_min + 1
    )
    db.save_sesion(sesion)

    notifs = svc.cerrar_sesiones_expiradas()
    assert len(notifs) == 1
    assert uid in notifs[0][0]
    assert "confirmaste" in notifs[0][1].lower() or "15" in notifs[0][1]

    sesion_cerrada = db.get_sesion(sesion.id_sesion)
    assert sesion_cerrada is not None
    assert sesion_cerrada.estado_sesion == EstadoSesion.CERRADA_POR_CONFIRMACION_EXPIRADA

    print("OK: flujo de sesión y expiración por confirmación")


if __name__ == "__main__":
    main()
