import { Pool, type PoolConfig, type QueryResult } from "pg";

export type DatabaseClient = Pool;

export function createDatabaseClient(databaseUrl: string): DatabaseClient {
  const config: PoolConfig = {
    connectionString: databaseUrl,
  };
  return new Pool(config);
}

export async function healthCheck(client: DatabaseClient): Promise<number> {
  const result: QueryResult<{ value: number }> = await client.query("SELECT 1::int AS value");
  return result.rows[0]?.value ?? 0;
}

export async function closeDatabaseClient(client: DatabaseClient): Promise<void> {
  await client.end();
}
