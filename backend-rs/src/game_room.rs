use canvas_game_engine::{Game, GameInput, InputKind};
use canvas_protocol::{
    encode_server_message, ServerMessage, FullFrameMessage,
};
use std::sync::Arc;
use tokio::sync::{broadcast, Mutex, RwLock};
use tracing;

const BROADCAST_CHANNEL_SIZE: usize = 64;
const FULL_STATE_INTERVAL: u64 = 60;

pub struct GameRoom {
    game: Arc<Mutex<Box<dyn Game>>>,
    tx: broadcast::Sender<Arc<Vec<u8>>>,
    last_full_frame: RwLock<Option<Arc<Vec<u8>>>>,
    id: String,
    frame_count: std::sync::atomic::AtomicU64,
}

impl GameRoom {
    pub fn new(id: String, game: Box<dyn Game>) -> Self {
        let (tx, _) = broadcast::channel(BROADCAST_CHANNEL_SIZE);
        Self {
            game: Arc::new(Mutex::new(game)),
            tx,
            last_full_frame: RwLock::new(None),
            id,
            frame_count: std::sync::atomic::AtomicU64::new(0),
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn subscribe(&self) -> broadcast::Receiver<Arc<Vec<u8>>> {
        self.tx.subscribe()
    }

    pub async fn last_full_frame(&self) -> Option<Arc<Vec<u8>>> {
        self.last_full_frame.read().await.clone()
    }

    pub async fn handle_click(&self, x: u16, y: u16, player_id: String) {
        let mut game = self.game.lock().await;
        game.handle_input(GameInput {
            x,
            y,
            kind: InputKind::Click,
            player_id,
        });
    }

    pub async fn handle_chat(&self, text: String, player_id: String) {
        let mut game = self.game.lock().await;
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat(text),
            player_id,
        });
    }

    pub fn broadcast_chat(&self, data: Arc<Vec<u8>>) -> Result<usize, broadcast::error::SendError<Arc<Vec<u8>>>> {
        self.tx.send(data)
    }

    pub async fn tick(&self) {
        let mut game = self.game.lock().await;
        game.update();

        let count = self.frame_count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let send_full = count % FULL_STATE_INTERVAL == 0;

        if send_full {
            self.broadcast_full_frame(&game).await;
        } else {
            self.broadcast_delta(&mut game).await;
        }
    }

    async fn broadcast_full_frame(&self, game: &Box<dyn Game>) {
        let fb = game.frame_buffer();
        let msg = ServerMessage::FullFrame(FullFrameMessage {
            width: game.width(),
            height: game.height(),
            palette: game.palette().to_vec(),
            pixels: fb.pixels().to_vec(),
        });
        if let Ok(encoded) = encode_server_message(&msg) {
            let data = Arc::new(encoded);
            *self.last_full_frame.write().await = Some(Arc::clone(&data));
            let _ = self.tx.send(data);
        }
    }

    async fn broadcast_delta(&self, game: &mut Box<dyn Game>) {
        let fb = game.frame_buffer();
        if !fb.has_dirty_tiles() {
            return;
        }
        // We need mutable access to extract dirty tiles, but the trait gives us &FrameBuffer.
        // For now, send full frame always. We'll optimize this when we add interior mutability to FrameBuffer.
        self.broadcast_full_frame(game).await;
    }

    pub async fn is_finished(&self) -> bool {
        self.game.lock().await.is_finished()
    }

    pub async fn metadata(&self) -> canvas_game_engine::GameMetadata {
        self.game.lock().await.metadata()
    }

    pub async fn player_count(&self) -> u32 {
        self.game.lock().await.player_count()
    }

    pub async fn thumbnail(&self) -> Option<Vec<u8>> {
        let game = self.game.lock().await;
        Some(game.frame_buffer().downsample(64, 64))
    }

    pub async fn run_game_loop(self: Arc<Self>, fps: f64) {
        let interval_ms = (1000.0 / fps) as u64;
        let mut interval = tokio::time::interval(tokio::time::Duration::from_millis(interval_ms));

        loop {
            interval.tick().await;
            if self.is_finished().await {
                tracing::info!("Game {} finished", self.id);
                break;
            }
            self.tick().await;
        }
    }
}
