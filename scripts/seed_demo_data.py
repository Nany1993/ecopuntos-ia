"""Genera ~200 registros de prueba con colaboradores inventados (ID Telegram simulado)."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta

from src.config import settings
from src.database import SQLiteDatabase
from src.models import EstadoSesion
from src.seed_data import CANECAS_SEED

NUM_INTENTOS = 200
NUM_COLABORADORES = 32
PUNTOS_ACIERTO = settings.puntos_acierto_primera

NOMBRES_DEMO = [
    "Ana María García", "Carlos Andrés López", "Laura Valentina Ruiz",
    "Diego Felipe Morales", "Sofía Isabel Torres", "Juan Pablo Herrera",
    "Mariana Lucía Castro", "Andrés Camilo Vargas", "Valentina Gómez",
    "Sebastián Mejía", "Camila Restrepo", "Nicolás Duarte",
    "Isabella Muñoz", "Santiago Ríos", "Daniela Ortiz", "Felipe Salazar",
    "Paula Henao", "Mateo Giraldo", "Juliana Quintero", "Tomás Álvarez",
    "Gabriela Pardo", "Emilio Cardona", "Carolina Jiménez", "Jorge Elías Núñez",
    "Natalia Acevedo", "Ricardo Soto", "Alejandra Marín", "David Cárdenas",
    "Luisa Fernanda Peña", "Oscar Iván Botero", "Manuela Zapata", "Cristian Arango",
]

EXPLICACIONES = {
    "blanca": [
        "Papel y cartón limpio identificado.",
        "Material reciclable blanco: documentos o cajas.",
        "Cartón apto para caneca blanca.",
    ],
    "verde": [
        "Envase plástico o botella PET detectada.",
        "Metal o vidrio reciclable.",
        "Residuo aprovechable en caneca verde.",
    ],
    "negra": [
        "Residuo no aprovechable o contaminado.",
        "Servilleta usada u orgánico no separable.",
        "Material para disposición final.",
    ],
}

OTROS_COLORES = {
    "blanca": ["verde", "negra"],
    "verde": ["blanca", "negra"],
    "negra": ["blanca", "verde"],
}


def _telegram_id_demo(indice: int) -> str:
    """ID numérico estilo Telegram (9 dígitos, único por colaborador demo)."""
    return str(510_000_000 + indice * 7_891)


def _username_desde_nombre(nombre: str) -> str:
    base = nombre.lower().split()[0]
    return f"{base}_eco{random.randint(10, 99)}"


def limpiar_datos_semilla(db: SQLiteDatabase) -> None:
    with db._connect() as conn:
        filas = conn.execute(
            "SELECT id_colaborador FROM colaboradores WHERE es_semilla = 1"
        ).fetchall()
        if not filas:
            return
        ids = [r["id_colaborador"] for r in filas]
        ph = ",".join("?" * len(ids))
        conn.execute(f"DELETE FROM registro_intentos WHERE id_colaborador IN ({ph})", ids)
        conn.execute(f"DELETE FROM sesiones WHERE id_colaborador IN ({ph})", ids)
        conn.execute(f"DELETE FROM puntos_colaborador WHERE id_colaborador IN ({ph})", ids)
        conn.execute("DELETE FROM colaboradores WHERE es_semilla = 1")
        conn.commit()


def crear_colaboradores_demo(db: SQLiteDatabase) -> list[dict]:
    colaboradores = []
    base = datetime.utcnow() - timedelta(days=45)
    for i, nombre in enumerate(NOMBRES_DEMO[:NUM_COLABORADORES]):
        tid = _telegram_id_demo(i)
        registrado = base + timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
        username = _username_desde_nombre(nombre)
        colaboradores.append(
            {
                "id_colaborador": tid,
                "nombre": nombre,
                "username_telegram": username,
                "registrado_en": registrado,
            }
        )
        db.upsert_colaborador(
            tid,
            nombre=nombre,
            username_telegram=username,
            es_semilla=True,
        )
    return colaboradores


def generar_intentos(db: SQLiteDatabase, colaboradores: list[dict]) -> int:
    random.seed(42)
    intentos_creados = 0
    inicio = datetime.utcnow() - timedelta(days=30)
    puntos_por_colab: dict[str, dict] = {
        c["id_colaborador"]: {"puntos": 0, "aciertos": 0, "sesiones": 0, "ultima": inicio}
        for c in colaboradores
    }

    while intentos_creados < NUM_INTENTOS:
        colab = random.choice(colaboradores)
        id_colab = colab["id_colaborador"]
        caneca = random.choice(CANECAS_SEED)
        color_caneca = caneca["color_caneca"]
        id_sesion = f"SES-{uuid.uuid4().hex[:12].upper()}"

        max_en_sesion = min(random.randint(1, 3), NUM_INTENTOS - intentos_creados)
        sesion_inicio = inicio + timedelta(
            hours=random.randint(0, 30 * 24),
            minutes=random.randint(0, 59),
        )
        estado_final = EstadoSesion.CERRADA_POR_INACTIVIDAD
        acierto_primera_sesion = False
        puntos_sesion = 0

        for num in range(1, max_en_sesion + 1):
            if random.random() < 0.78:
                prediccion = color_caneca
                resultado = "correcto"
                tipo_msg = "motivacional"
            else:
                prediccion = random.choice(OTROS_COLORES[color_caneca])
                resultado = "incorrecto"
                tipo_msg = "correctivo"

            confianza = round(random.uniform(0.72, 0.99), 2)
            latencia = random.randint(1800, 28000)
            ts = sesion_inicio + timedelta(seconds=(num - 1) * random.randint(30, 180))

            if resultado == "correcto" and num == 1:
                estado_sesion = EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION
                if num == max_en_sesion:
                    estado_sesion = EstadoSesion.CERRADA_EXITOSA
                    estado_final = EstadoSesion.CERRADA_EXITOSA
                    acierto_primera_sesion = True
                    puntos_sesion = PUNTOS_ACIERTO
            elif resultado == "correcto":
                estado_sesion = EstadoSesion.ABIERTA_CORRECTA_PENDIENTE_CONFIRMACION
            elif num >= max_en_sesion and max_en_sesion >= 3:
                estado_sesion = EstadoSesion.CERRADA_POR_MAXIMO_INTENTOS
                estado_final = EstadoSesion.CERRADA_POR_MAXIMO_INTENTOS
            else:
                estado_sesion = EstadoSesion.ABIERTA_CLASIFICACION_INCORRECTA

            confirmacion = 1 if (resultado == "correcto" and num == max_en_sesion and puntos_sesion) else None

            with db._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO registro_intentos (
                        id_sesion, numero_intento, fecha_hora_evento, id_colaborador,
                        id_caneca, caneca_qr, area, tipos_residuo_permitidos,
                        prediccion_ia, nivel_confianza, explicacion_breve,
                        resultado_intento, mensaje_enviado, confirmacion_deposito,
                        tiempo_respuesta_ms, estado_sesion, proveedor_ia,
                        respaldo_activado, acierto_primera, puntos_otorgados
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    """,
                    (
                        id_sesion,
                        num,
                        ts.isoformat(),
                        id_colab,
                        caneca["id_caneca"],
                        color_caneca,
                        caneca["area"],
                        json.dumps(caneca["tipos_residuo_permitidos"], ensure_ascii=False),
                        prediccion,
                        confianza,
                        random.choice(EXPLICACIONES[prediccion]),
                        resultado,
                        tipo_msg,
                        confirmacion,
                        latencia,
                        estado_sesion.value,
                        "gemini",
                        int(acierto_primera_sesion and num == 1 and puntos_sesion),
                        puntos_sesion if (puntos_sesion and num == max_en_sesion) else 0,
                    ),
                )
                conn.commit()

            intentos_creados += 1
            puntos_por_colab[id_colab]["ultima"] = max(puntos_por_colab[id_colab]["ultima"], ts)

            if resultado == "correcto" and num == 1 and num == max_en_sesion:
                break

        fin_sesion = sesion_inicio + timedelta(minutes=random.randint(2, 15))
        with db._connect() as conn:
            conn.execute(
                """
                INSERT INTO sesiones (
                    id_sesion, id_colaborador, id_caneca_inicial, id_caneca_actual,
                    estado_sesion, numero_intento_actual, creada_en, actualizada_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_sesion,
                    id_colab,
                    caneca["id_caneca"],
                    caneca["id_caneca"],
                    estado_final.value,
                    max_en_sesion,
                    sesion_inicio.isoformat(),
                    fin_sesion.isoformat(),
                ),
            )
            conn.commit()

        if puntos_sesion:
            puntos_por_colab[id_colab]["puntos"] += puntos_sesion
            puntos_por_colab[id_colab]["aciertos"] += 1
            puntos_por_colab[id_colab]["sesiones"] += 1

    with db._connect() as conn:
        for id_colab, stats in puntos_por_colab.items():
            if stats["puntos"] == 0 and stats["sesiones"] == 0:
                continue
            conn.execute(
                """
                INSERT INTO puntos_colaborador (
                    id_colaborador, puntos_totales, aciertos_primera,
                    sesiones_completadas, ultima_actualizacion
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id_colaborador) DO UPDATE SET
                    puntos_totales = excluded.puntos_totales,
                    aciertos_primera = excluded.aciertos_primera,
                    sesiones_completadas = excluded.sesiones_completadas,
                    ultima_actualizacion = excluded.ultima_actualizacion
                """,
                (
                    id_colab,
                    stats["puntos"],
                    stats["aciertos"],
                    stats["sesiones"],
                    stats["ultima"].isoformat(),
                ),
            )
        conn.commit()

    return intentos_creados


def backfill_colaboradores_sin_perfil(db: SQLiteDatabase) -> None:
    """Registra colaboradores reales que ya tienen intentos pero aún no están en colaboradores."""
    ahora = datetime.utcnow().isoformat()
    with db._connect() as conn:
        conn.execute(
            """
            INSERT INTO colaboradores (
                id_colaborador, nombre, username_telegram,
                es_semilla, registrado_en, ultima_actividad
            )
            SELECT
                r.id_colaborador,
                'Colaborador ' || r.id_colaborador,
                NULL,
                0,
                MIN(r.fecha_hora_evento),
                MAX(r.fecha_hora_evento)
            FROM registro_intentos r
            LEFT JOIN colaboradores c ON c.id_colaborador = r.id_colaborador
            WHERE c.id_colaborador IS NULL
            GROUP BY r.id_colaborador
            """,
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos demo SmartSort (~200 intentos)")
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Elimina solo datos de semilla (es_semilla=1) antes de cargar",
    )
    args = parser.parse_args()

    db = SQLiteDatabase()
    db.init_schema()

    if args.limpiar:
        limpiar_datos_semilla(db)
        print("Datos de semilla anteriores eliminados.")

    with db._connect() as conn:
        existentes = conn.execute(
            """
            SELECT COUNT(*) FROM registro_intentos r
            JOIN colaboradores c ON c.id_colaborador = r.id_colaborador
            WHERE c.es_semilla = 1
            """
        ).fetchone()[0]

    if existentes >= NUM_INTENTOS and not args.limpiar:
        print(f"Ya hay {existentes} intentos de semilla. Usa --limpiar para regenerar.")
        return

    if existentes > 0 and not args.limpiar:
        limpiar_datos_semilla(db)

    colaboradores = crear_colaboradores_demo(db)
    total = generar_intentos(db, colaboradores)
    backfill_colaboradores_sin_perfil(db)

    print(f"Semilla cargada: {len(colaboradores)} colaboradores demo (ID Telegram simulado)")
    print(f"Registros en registro_intentos: {total}")
    print(f"Base de datos: {db.path.resolve()}")
    print("Los usuarios reales de Telegram se registran al usar el bot (id numérico único).")


if __name__ == "__main__":
    main()
