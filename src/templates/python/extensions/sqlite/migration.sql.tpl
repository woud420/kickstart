-- SQLite starter schema. Review and evolve this user-owned seed explicitly.
BEGIN;
CREATE TABLE IF NOT EXISTS example_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
COMMIT;
