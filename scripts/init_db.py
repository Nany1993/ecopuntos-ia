"""Inicializa la base de datos local y carga datos semilla."""

from src.database import SQLiteDatabase


def main() -> None:
    db = SQLiteDatabase()
    db.init_schema()
    db.seed_if_empty()
    print(f"Base de datos lista: {db.path.resolve()}")


if __name__ == "__main__":
    main()
