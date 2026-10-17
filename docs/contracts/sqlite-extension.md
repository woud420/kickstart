# SQLite service extension

Date: 2026-10-17

The first supported slice is Python/FastAPI container services:

```bash
kickstart create service local-api --lang python --database sqlite
```

Rust and TypeScript remain separate implementation slices. Python minimal
services, Cloudflare Workers and other unsupported combinations fail before
creating a project. SQLite here is a local file database, not Cloudflare D1.

## Dependency, configuration and files

The Python client uses `aiosqlite>=0.22.1,<1` over Python's SQLite library.
It follows the driver's [asynchronous connection and cursor context managers](https://aiosqlite.omnilib.dev/en/stable/).
No database server, ORM or connection pool is generated.

`Settings.sqlite_path` is a `Path` loaded from `SQLITE_PATH`, including the
normal `.env` settings file. The example is `data/app.sqlite3`, relative to the
process working directory. Application code passes that path to
`connect_database`; importing the client or generating the project opens no
database. Entering the connection context creates missing parent directories.

The SQLite extension owns its environment example and initial migration seed.
The base Python content plan must not replace them with Postgres examples.
The manifest records `extensions.database: sqlite`; generated helpers, settings,
migration and usage notes remain user-owned seeds after creation.

## Connections and transactions

`async with connect_database(path) as connection` enables foreign-key enforcement
for each connection and closes it on success or failure. SQLite requires this
[per-connection foreign-key setting](https://www.sqlite.org/foreignkeys.html).
The health helper executes a small query without applying a schema or creating
application records. Application code owns explicit `commit()` and `rollback()`;
leaving the context does not commit unfinished work. See Python's
[transaction-control contract](https://docs.python.org/3.12/library/sqlite3.html#transaction-control).

`migrations/001_initial.sql` is an ordinary, user-owned SQLite SQL seed with an
example table. The generated operations guide shows an explicit application
step. There is no automatic startup migration, version ledger, schema diff or
rollback manager. Owners must review and evolve the seed for their application.

The sample API repository remains in memory until application code integrates
the client. Enabling the extension does not silently replace its storage or
make the ordinary health route depend on a database.

## Local development and storage

The generated guide covers installation, configuration, applying the seed,
parameterized queries and explicit commits. Tests use temporary file databases
to prove reopening preserves committed records, closing rolls back unfinished
work, foreign keys are enforced, and connection contexts release resources.

The default data directory, SQLite files and local environment files are
excluded from Git and Docker build contexts. Custom paths need equivalent
application-owned exclusions. Containers need an explicitly selected persistent
mount for durable state; no volume, replication or deployment is provisioned.

## Rollout and validation

Every additional language must implement its dependency and typed client,
configuration, file lifecycle, migration seed, generated docs and real database
tests before its capability row is enabled. Unsupported combinations continue
to fail explicitly. A supported slice must pass its generated `make check`,
taste/capability checks, repository checks and required scaffold evals. The
Python slice is checked alone and with its supported Redis/JWT extensions.
