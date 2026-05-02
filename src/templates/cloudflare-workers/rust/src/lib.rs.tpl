use worker::*;

fn json_response(value: serde_json::Value) -> Result<Response> {
    Response::from_json(&value)
}

#[event(fetch)]
async fn fetch(req: Request, env: Env, _ctx: Context) -> Result<Response> {
    console_error_panic_hook::set_once();

    let url = req.url()?;
    let service = env
        .var("SERVICE_NAME")
        .map(|value| value.to_string())
        .unwrap_or_else(|_| "{{ service_name }}".to_string());

    match url.path() {
        "/healthz" => json_response(serde_json::json!({
            "status": "ok",
            "service": service,
        })),
        _ => json_response(serde_json::json!({
            "message": format!("Hello from {}", service),
        })),
    }
}
