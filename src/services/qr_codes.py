"""Generación de códigos QR para canecas."""

from __future__ import annotations

from pathlib import Path

import qrcode

from src.config import settings


def generar_qr_caneca(id_caneca: str, output_dir: Path | None = None) -> Path:
    destino = output_dir or Path("output/qr")
    destino.mkdir(parents=True, exist_ok=True)
    url = f"{settings.telegram_deep_link_base}?start={id_caneca}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = destino / f"qr_{id_caneca}.png"
    img.save(path)
    return path
