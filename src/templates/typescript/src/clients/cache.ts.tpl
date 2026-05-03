import { createClient } from "redis";

export type CacheClient = ReturnType<typeof createClient>;

export function createCacheClient(redisUrl: string): CacheClient {
  return createClient({ url: redisUrl });
}

export async function connectCacheClient(client: CacheClient): Promise<CacheClient> {
  if (!client.isOpen) {
    await client.connect();
  }
  return client;
}

export async function ping(client: CacheClient): Promise<string> {
  return client.ping();
}

export async function closeCacheClient(client: CacheClient): Promise<void> {
  if (client.isOpen) {
    await client.quit();
  }
}
