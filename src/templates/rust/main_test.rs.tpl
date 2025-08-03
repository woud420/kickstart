#[cfg(test)]
mod tests {
    use super::*;
    use actix_web::{test, App};

    #[actix_web::test]
    async fn test_root_endpoint() {
        let app = test::init_service(
            App::new()
                .route("/", web::get().to(root))
        ).await;

        let req = test::TestRequest::get()
            .uri("/")
            .to_request();
        
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }

    #[actix_web::test]
    async fn test_health_endpoint() {
        let app = test::init_service(
            App::new()
                .route("/health", web::get().to(health))
        ).await;

        let req = test::TestRequest::get()
            .uri("/health")
            .to_request();
        
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }
}