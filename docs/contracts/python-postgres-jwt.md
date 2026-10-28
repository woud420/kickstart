# Python Postgres and JWT

Python/FastAPI container services support Postgres alone or together with JWT
and/or Redis. Python's minimal framework does not support these extensions.
The capability registry is `src/generator/service_capabilities.py`.

## Generated behavior

| Component | Contract |
| --- | --- |
| `src/model/entities.py` | Example `User` with `id` and `email`; not a database row model. |
| `src/model/repository.py` | In-memory create/get operations. |
| `src/api/services.py`, `src/routes/users.py` | Public example create/get routes using that in-memory repository, even with Postgres/JWT selected. |
| `src/clients/database.py` | Explicit asyncpg pool creation, health check, and pool closure. The caller supplies the connection URL. |
| `migrations/001_initial.sql` | Postgres example schema: users, profiles, UUID defaults, constraints, indexes, update triggers, and views. |
| `src/handler/auth.py` (JWT) | Token creation/verification and bcrypt hashing/verification; no database access or route registration. |

The app does not automatically connect a pool, apply migrations, read database
credentials into its settings, or persist example HTTP users. The Postgres
schema requires a username as well as an email; the HTTP example accepts only
an email because it uses independent in-memory storage. Its data is lost when
the process restarts.

Password storage, signup/login endpoints, account lookup, deactivation policy,
and route protection must be designed and wired by the application. Combining
`--database postgres --auth jwt` does not implement those features. Adding only
a `password_hash` column would not implement a login flow.

## Migration ownership

The Postgres extension owns `migrations/001_initial.sql`. The generator must not
overwrite it with the generic core example. With no database extension, the
core example remains; SQLite owns its own separate migration.

The Postgres schema does not contain the core example's `password_hash` or
`deactivated_at` columns. No currently emitted Python code queries them. Older
templates under `python/core/services/`, `python/core/model/entities/user/`,
`python/dao/`, and `python/repository/` are not part of the current core render
plan and do not establish a generated persistence contract.

Apply the initial migration once to a new database, using a role that can install
`uuid-ossp` (or have an administrator install that extension first):

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 --single-transaction -f migrations/001_initial.sql
```

`DATABASE_URL` here is a caller-supplied connection string, not an automatically
loaded setting. The app owner must arrange pool lifecycle and pass that URL to
`create_pool`. The migration is not a migration runner or an upgrade path for
existing generated projects; its trigger creation is not rerunnable.

## Behavioral validation

The CI job **Python Postgres contract** installs dependencies from a generated
Postgres/JWT project and tests both configurations against Postgres 16. It applies
each generated migration in a transaction that is rolled back, exercises the
generated pool helpers, and checks inserts, constraints, JSONB, update triggers,
views, profile foreign keys, and cascading deletion. It also exercises the
generated HTTP and JWT helpers and verifies that example HTTP users do not
silently become database rows.

To run locally against a disposable database, install the generated project's
requirements into a separate Python environment, then run:

```bash
KICKSTART_TEST_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/kickstart_test \
KICKSTART_GENERATED_PYTHON=/absolute/path/to/generated-env/bin/python \
poetry run pytest tests/integration/test_python_postgres.py -v
```

Without the DSN these database tests skip. With a DSN, missing dependencies,
connection failures, or behavioral failures fail the test. SQL text checks alone
are not evidence of database or authentication integration.
