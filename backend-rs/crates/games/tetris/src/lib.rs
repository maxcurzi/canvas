use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata};

pub struct TetrisGame {
    fb: FrameBuffer,
    width: u16,
    height: u16,
    finished: bool,
}

impl TetrisGame {
    pub fn new(width: u16, height: u16) -> Self {
        Self {
            fb: FrameBuffer::new(width, height),
            width,
            height,
            finished: false,
        }
    }
}

impl Game for TetrisGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Tetris".into(),
            description: "Cooperative Tetris — click to rotate and move pieces.".into(),
            width: self.width,
            height: self.height,
            max_players: None,
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
    fn palette(&self) -> &[Color] { &[Color::BLACK, Color::WHITE] }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tetris_creates_with_dimensions() {
        let game = TetrisGame::new(64, 64);
        assert_eq!(game.width(), 64);
        assert_eq!(game.height(), 64);
        assert!(!game.is_finished());
    }
}
