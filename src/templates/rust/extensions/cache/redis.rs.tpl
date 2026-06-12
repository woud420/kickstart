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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_client_parses_url_without_connecting() {
        assert!(create_client("redis://127.0.0.1:6379/2").is_ok());
    }

    #[test]
    fn invalid_url_is_rejected() {
        assert!(create_client("not-a-redis-url").is_err());
    }
}
