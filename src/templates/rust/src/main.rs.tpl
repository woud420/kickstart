{% if include_redis_cache %}mod clients;
{% endif %}{% if include_jwt_auth %}mod handler;
{% endif %}{% if include_redis_cache or include_jwt_auth %}
{% endif %}use actix_web::{App, HttpResponse, HttpServer, web};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new().route(
            "/",
            web::get().to(|| async { HttpResponse::Ok().json("Hello World") }),
        )
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
