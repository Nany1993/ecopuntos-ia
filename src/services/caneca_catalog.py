"""Alta de canecas en el catálogo del piloto."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.database import get_database
from src.models import Caneca
from src.services.qr_codes import generar_qr_caneca

_COLOR_CODIGO = {"blanca": "BLANCA", "verde": "VERDE", "negra": "NEGRA"}
_ID_CANECA_RE = re.compile(r"^CAN-(BLANCA|VERDE|NEGRA)-\d{2}$")


@dataclass
class ResultadoNuevaCaneca:
    caneca: Caneca
    qr_path: Path


def sugerir_id_caneca(color: str, ids_existentes: list[str] | None = None) -> str:
    codigo = _COLOR_CODIGO[color]
    prefix = f"CAN-{codigo}-"
    ids = ids_existentes or []
    numeros: list[int] = []
    for cid in ids:
        if cid.startswith(prefix):
            try:
                numeros.append(int(cid.rsplit("-", 1)[-1]))
            except ValueError:
                continue
    siguiente = max(numeros, default=0) + 1
    return f"{prefix}{siguiente:02d}"


def registrar_caneca(
    area: str,
    color: str,
    id_caneca: str | None = None,
    output_dir: Path | None = None,
) -> ResultadoNuevaCaneca:
    area = area.strip()
    if not area:
        raise ValueError("El área es obligatoria.")

    if color not in _COLOR_CODIGO:
        raise ValueError("Color inválido. Use blanca, verde o negra.")

    db = get_database()
    ids = db.listar_ids_canecas()
    id_final = (id_caneca or sugerir_id_caneca(color, ids)).strip().upper()

    if not _ID_CANECA_RE.match(id_final):
        raise ValueError(
            "ID inválido. Use el formato CAN-BLANCA-01, CAN-VERDE-02 o CAN-NEGRA-03."
        )

    color_esperado = _COLOR_CODIGO[color]
    if color_esperado not in id_final:
        raise ValueError(f"El ID debe corresponder al color {color} ({color_esperado}).")

    if db.existe_caneca(id_final):
        raise ValueError(f"Ya existe una caneca con ID `{id_final}`.")

    caneca = Caneca(
        id_caneca=id_final,
        area=area,
        color_caneca=color,  # type: ignore[arg-type]
        estado_caneca="activa",
    )
    db.crear_caneca(caneca)
    qr_path = generar_qr_caneca(id_final, output_dir)
    return ResultadoNuevaCaneca(caneca=caneca, qr_path=qr_path)
