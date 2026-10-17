# SQLite operations

This service includes an asynchronous SQLite client and an initial SQL seed.
Application code chooses when to use them; the sample API repository remains
in memory and its health route does not query the database.

## Configuration and local development

Run `make install`, copy `.env.example` to `.env` and set `SQLITE_PATH` if needed.
The default is `data/app.sqlite3`, relative to the process working directory.
`Settings.sqlite_path` reads the value from the environment or `.env`.
The client creates missing parent directories when a connection is opened;
generation and imports do not create a database.

Apply the user-owned starter migration explicitly from the project root:

```bash
.venv/bin/python - <<'PY'
import asyncio
from pathlib import Path

from src.clients.database import connect_database
from src.config.settings import get_settings

async def migrate() -> None:
    async with connect_database(get_settings().sqlite_path) as connection:
        cursor = await connection.executescript(Path("migrations/001_initial.sql").read_text())
        await cursor.close()
        await connection.commit()

asyncio.run(migrate())
PY
```

The seed creates `example_items`. It is not an automatic migration runner or
version ledger. Review and evolve it for the application before production.

Use scoped connections, parameterized queries and explicit transactions:

```python
async with connect_database(get_settings().sqlite_path) as connection:
    await connection.execute_insert(
        "INSERT INTO example_items (name) VALUES (?)", ("local example",)
    )
    await connection.commit()
```

Connections enable foreign keys and close on success or failure. Closing does
not commit unfinished writes. `health_check(connection)` runs a small query
without applying the schema. `make check` exercises real temporary databases,
including persistence, rollback, foreign keys and connection cleanup.

## Storage and deployment

The default data directory, `.env` and SQLite files are excluded from Git and
Docker build contexts. Add equivalent exclusions for custom paths. Container
filesystems are ephemeral unless the application owner supplies persistent
storage; this scaffold does not provision volumes or distributed replication.
The SQLite client is intended for local file storage and is not a Cloudflare
D1 binding. No database server process is needed.
