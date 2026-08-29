from pathlib import Path

import models  # noqa: F401 - registers SQLAlchemy models before create_all
from database import Base, engine


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "supabase" / "migrations"


def main() -> None:
    Base.metadata.create_all(bind=engine)
    connection = engine.raw_connection()
    try:
        with connection.cursor() as cursor:
            for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
                cursor.execute(migration.read_text(encoding="utf-8"))
                print(f"Applied {migration.name}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
