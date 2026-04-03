mod game_room;
mod registry;

use axum::{
    Router,
    extract::{
        State, WebSocketUpgrade,
        ws::WebSocket,
    },
    response::IntoResponse,
    routing::get,
};
use registry::GameRegistry;
use std::sync::Arc;
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;
use tracing_subscriber::EnvFilter;

type AppState = Arc<GameRegistry>;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("canvas_server=info".parse().unwrap()))
        .init();

    let registry = Arc::new(GameRegistry::new());
    registry.spawn_default_games();

    let app = Router::new()
        .route("/ws", get(ws_handler))
        .route("/health", get(health))
        .layer(CorsLayer::permissive())
        .with_state(registry);

    let addr = "0.0.0.0:8765";
    tracing::info!("Listening on {addr}");
    let listener = TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "ok"
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    State(registry): State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_socket(socket, registry))
}

async fn handle_socket(socket: WebSocket, registry: Arc<GameRegistry>) {
    registry.handle_connection(socket).await;
}
