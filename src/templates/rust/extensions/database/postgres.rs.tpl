#![allow(dead_code)]

use tokio_postgres::{Client, Error, NoTls};

pub async fn create_client(database_url: &str) -> Result<Client, Error> {
    let (client, connection) = tokio_postgres::connect(database_url, NoTls).await?;

    actix_web::rt::spawn(async move {
        if let Err(error) = connection.await {
            eprintln!("Postgres connection task ended: {error}");
        }
    });

    Ok(client)
}

pub async fn health_check(client: &Client) -> Result<i32, Error> {
    let row = client.query_one("SELECT 1::INT4", &[]).await?;
    Ok(row.get(0))
}
