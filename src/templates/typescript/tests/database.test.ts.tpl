import { describe, expect, it } from "vitest";

import { createDatabaseClient } from "../src/clients/database.js";

describe("database client", () => {
  it("builds a pool from the connection string without connecting", async () => {
    const connectionString = "postgres://app:secret@db-host:5433/{{ service_name }}";
    const pool = createDatabaseClient(connectionString);

    expect(pool.options.connectionString).toBe(connectionString);
    await pool.end();
  });
});
