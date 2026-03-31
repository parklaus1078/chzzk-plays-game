from pathlib import Path

import aiosqlite


async def init_database(db_path: str) -> aiosqlite.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 5000")
    db.row_factory = aiosqlite.Row
    await _run_migrations(db)
    return db


async def _run_migrations(db: aiosqlite.Connection) -> None:
    """Apply migrations idempotently from migrations/ directory."""
    # Create migrations tracking table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)
    await db.commit()

    # Get migrations directory
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return

    # Find all .sql files
    migration_files = sorted(migrations_dir.glob("*.sql"))

    for migration_file in migration_files:
        migration_name = migration_file.name

        # Check if already applied
        cursor = await db.execute(
            "SELECT name FROM _migrations WHERE name = ?", (migration_name,)
        )
        row = await cursor.fetchone()

        if row is None:
            # Apply migration
            migration_sql = migration_file.read_text()
            await db.executescript(migration_sql)

            # Record migration
            await db.execute(
                "INSERT INTO _migrations (name) VALUES (?)", (migration_name,)
            )
            await db.commit()
