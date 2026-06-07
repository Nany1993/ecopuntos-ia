"""Genera códigos QR para las canecas del piloto."""

from __future__ import annotations

import argparse
from pathlib import Path

import qrcode

from src.config import settings
from src.database import get_database


def generar_qr(id_caneca: str, output_dir: Path) -> Path:
    url = f"{settings.telegram_deep_link_base}?start={id_caneca}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = output_dir / f"qr_{id_caneca}.png"
    img.save(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generar QR de canecas SmartSort")
    parser.add_argument("--output", default="output/qr", help="Directorio de salida")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    db = get_database()
    canecas = db.list_canecas()

    if not canecas:
        print("No hay canecas en catálogo. Ejecuta primero: python -m scripts.init_db")
        return

    print(f"Generando {len(canecas)} QR en {output_dir.resolve()}...")
    print(f"{'id_caneca':<18} {'color':<8} {'area':<25} QR")
    print("-" * 70)
    for caneca in canecas:
        path = generar_qr(caneca.id_caneca, output_dir)
        print(f"  {caneca.id_caneca:<16} {caneca.color_caneca:<8} {caneca.area:<25} {path.name}")

    manifest = output_dir / "inventario_qr.txt"
    with manifest.open("w", encoding="utf-8") as f:
        f.write("INVENTARIO CANECAS — MAPEO QR\n")
        f.write("=" * 50 + "\n\n")
        for caneca in canecas:
            link = f"{settings.telegram_deep_link_base}?start={caneca.id_caneca}"
            f.write(f"{caneca.id_caneca}\n")
            f.write(f"  Color:  {caneca.color_caneca}\n")
            f.write(f"  Area:   {caneca.area}\n")
            f.write(f"  QR:     qr_{caneca.id_caneca}.png\n")
            f.write(f"  Link:   {link}\n\n")
    print(f"\nManifiesto: {manifest.resolve()}")

    print("\nDeep link ejemplo:")
    print(f"  {settings.telegram_deep_link_base}?start=CAN-BLANCA-01")


if __name__ == "__main__":
    main()
