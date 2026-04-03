use crate::game_room::GameRoom;
use axum::extract::ws::{Message, WebSocket};
use canvas_protocol::{
    decode_client_message, encode_server_message, ClientMessage, ChatMessage, GameInfo,
    GameListMessage, ServerMessage,
};
use dashmap::DashMap;
use futures_util::{SinkExt, StreamExt};
use std::sync::Arc;
use tracing;

pub struct GameRegistry {
    rooms: DashMap<String, Arc<GameRoom>>,
}

impl GameRegistry {
    pub fn new() -> Self {
        Self {
            rooms: DashMap::new(),
        }
    }

    pub fn spawn_default_games(&self) {
        self.create_room(
            "place-default".into(),
            Box::new(canvas_game_place::PlaceGame::new(256, 256)),
            1.0,
        );
        self.create_room(
            "tetris-default".into(),
            Box::new(canvas_game_tetris::TetrisGame::new(64, 64)),
            2.0,
        );
        self.create_room(
            "invaders-default".into(),
            Box::new(canvas_game_invaders::InvadersGame::new(64, 64)),
            5.0,
        );
        self.create_room(
            "snake-default".into(),
            Box::new(canvas_game_snake::SnakeGame::new(128, 128)),
            10.0,
        );
    }

    pub fn create_room(
        &self,
        id: String,
        game: Box<dyn canvas_game_engine::Game>,
        fps: f64,
    ) {
        let room = Arc::new(GameRoom::new(id.clone(), game));
        let room_clone = Arc::clone(&room);
        tokio::spawn(async move {
            room_clone.run_game_loop(fps).await;
        });
        self.rooms.insert(id, room);
    }

    pub async fn list_games(&self) -> Vec<GameInfo> {
        let mut games = Vec::new();
        for entry in self.rooms.iter() {
            let room = entry.value();
            let meta = room.metadata().await;
            games.push(GameInfo {
                id: room.id().to_string(),
                name: meta.name,
                description: meta.description,
                width: meta.width,
                height: meta.height,
                player_count: room.player_count().await,
                thumbnail: room.thumbnail().await,
            });
        }
        games
    }

    pub fn get_room(&self, id: &str) -> Option<Arc<GameRoom>> {
        self.rooms.get(id).map(|r| Arc::clone(r.value()))
    }

    pub async fn handle_connection(&self, socket: WebSocket) {
        let (mut sender, mut receiver) = socket.split();

        // Send game list on connect
        let games = self.list_games().await;
        let list_msg = ServerMessage::GameList(GameListMessage { games });
        if let Ok(encoded) = encode_server_message(&list_msg) {
            let _ = sender.send(Message::Binary(encoded.into())).await;
        }

        let mut current_room: Option<Arc<GameRoom>> = None;
        let mut broadcast_rx: Option<tokio::sync::broadcast::Receiver<Arc<Vec<u8>>>> = None;
        let player_id = uuid::Uuid::new_v4().to_string();

        loop {
            tokio::select! {
                // Handle incoming client messages
                msg = receiver.next() => {
                    match msg {
                        Some(Ok(Message::Binary(data))) => {
                            if let Ok(client_msg) = decode_client_message(&data) {
                                match client_msg {
                                    ClientMessage::JoinGame(join) => {
                                        if let Some(room) = self.get_room(&join.game_id) {
                                            // Send last full frame
                                            if let Some(frame) = room.last_full_frame().await {
                                                let _ = sender.send(Message::Binary(frame.to_vec().into())).await;
                                            }
                                            broadcast_rx = Some(room.subscribe());
                                            current_room = Some(room);
                                            tracing::info!("Player {player_id} joined {}", join.game_id);
                                        }
                                    }
                                    ClientMessage::Click(click) => {
                                        if let Some(ref room) = current_room {
                                            room.handle_click(click.x, click.y, player_id.clone()).await;
                                        }
                                    }
                                    ClientMessage::ListGames => {
                                        let games = self.list_games().await;
                                        let list_msg = ServerMessage::GameList(GameListMessage { games });
                                        if let Ok(encoded) = encode_server_message(&list_msg) {
                                            let _ = sender.send(Message::Binary(encoded.into())).await;
                                        }
                                    }
                                    ClientMessage::LeaveGame => {
                                        current_room = None;
                                        broadcast_rx = None;
                                    }
                                    ClientMessage::Chat(chat) => {
                                        if let Some(ref room) = current_room {
                                            room.handle_chat(chat.text.clone(), player_id.clone()).await;
                                            // Broadcast chat message to all players in room
                                            let chat_msg = ServerMessage::Chat(ChatMessage {
                                                player_id: player_id.clone(),
                                                text: chat.text,
                                                timestamp_ms: std::time::SystemTime::now()
                                                    .duration_since(std::time::UNIX_EPOCH)
                                                    .unwrap_or_default()
                                                    .as_millis() as u64,
                                            });
                                            if let Ok(encoded) = encode_server_message(&chat_msg) {
                                                let data = Arc::new(encoded);
                                                let _ = room.broadcast_chat(data);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Some(Ok(Message::Close(_))) | None => break,
                        _ => {}
                    }
                }
                // Forward game broadcasts to client
                frame = async {
                    match &mut broadcast_rx {
                        Some(rx) => rx.recv().await,
                        None => std::future::pending().await,
                    }
                } => {
                    if let Ok(data) = frame {
                        if sender.send(Message::Binary(data.to_vec().into())).await.is_err() {
                            break;
                        }
                    }
                }
            }
        }
        tracing::info!("Player {player_id} disconnected");
    }
}
