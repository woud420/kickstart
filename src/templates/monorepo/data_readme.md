# Data Notes

PostgreSQL is the default system of record. Start schema work in `data/postgres/schema.sql`, then promote changes into your migration tool once the application framework is chosen.

Default conventions:

- UUID primary keys.
- `timestamptz` audit fields.
- JSONB only for bounded, queryable flexible attributes.
- Explicit indexes for lookup and JSONB access paths.
- Soft deletes only when the domain needs audit recovery.
