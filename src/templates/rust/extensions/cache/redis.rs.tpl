#![allow(dead_code)]

use redis::{Client, RedisResult, aio::MultiplexedConnection};

pub fn create_client(redis_url: &str) -> RedisResult<Client> {
    Client::open(redis_url)
}

pub async fn create_connection(client: &Client) -> RedisResult<MultiplexedConnection> {
    client.get_multiplexed_async_connection().await
}

pub async fn ping(connection: &mut MultiplexedConnection) -> RedisResult<String> {
    redis::cmd("PING").query_async(connection).await
}
