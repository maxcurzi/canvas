use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata};

pub struct SnakeGame {
    fb: FrameBuffer,
    width: u16,
    height: u16,
    finished: bool,
}

impl SnakeGame {
    pub fn new(width: u16, height: u16) -> Self {
        Self {
            fb: FrameBuffer::new(width, height),
            width,
            height,
            finished: false,
        }
    }
}

impl Game for SnakeGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Snake Royale".into(),
            description: "Multiplayer snake — eat, grow, survive. Last snake standing wins.".into(),
            width: self.width,
            height: self.height,
            max_players: Some(100),
            supports_chat: false,
        }
    }
    fn width(&self) -> u16 { self.width }
    fn height(&self) -> u16 { self.height }
    fn update(&mut self) {}
    fn handle_input(&mut self, _input: GameInput) {}
    fn frame_buffer(&self) -> &FrameBuffer { &self.fb }
    fn is_finished(&self) -> bool { self.finished }
    fn player_count(&self) -> u32 { 0 }
    fn palette(&self) -> &[Color] { &[Color::BLACK, Color::GREEN, Color::RED, Color::BLUE] }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snake_creates_with_dimensions() {
        let game = SnakeGame::new(128, 128);
        assert_eq!(game.width(), 128);
        assert!(!game.is_finished());
    }
}
