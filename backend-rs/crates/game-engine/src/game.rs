use crate::color::Color;
use crate::frame_buffer::FrameBuffer;

#[derive(Debug, Clone)]
pub struct GameInput {
    pub x: u16,
    pub y: u16,
    pub kind: InputKind,
    pub player_id: String,
}

#[derive(Debug, Clone)]
pub enum InputKind {
    Click,
    Chat(String),
}

#[derive(Debug, Clone)]
pub struct GameMetadata {
    pub name: String,
    pub description: String,
    pub width: u16,
    pub height: u16,
    pub max_players: Option<u32>,
    pub supports_chat: bool,
}

pub trait Game: Send + Sync {
    fn metadata(&self) -> GameMetadata;
    fn width(&self) -> u16;
    fn height(&self) -> u16;
    fn update(&mut self);
    fn handle_input(&mut self, input: GameInput);
    fn frame_buffer(&self) -> &FrameBuffer;
    fn is_finished(&self) -> bool;
    fn player_count(&self) -> u32;
    fn palette(&self) -> &[Color];
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestGame {
        fb: FrameBuffer,
        finished: bool,
        clicks: Vec<(u16, u16)>,
    }

    impl TestGame {
        fn new(w: u16, h: u16) -> Self {
            Self {
                fb: FrameBuffer::new(w, h),
                finished: false,
                clicks: Vec::new(),
            }
        }
    }

    impl Game for TestGame {
        fn metadata(&self) -> GameMetadata {
            GameMetadata {
                name: "Test".into(),
                description: "A test game".into(),
                width: self.width(),
                height: self.height(),
                max_players: None,
                supports_chat: false,
            }
        }
        fn width(&self) -> u16 { self.fb.width() }
        fn height(&self) -> u16 { self.fb.height() }
        fn update(&mut self) {}
        fn handle_input(&mut self, input: GameInput) {
            self.clicks.push((input.x, input.y));
            self.fb.set_pixel(input.x, input.y, 1);
        }
        fn frame_buffer(&self) -> &FrameBuffer { &self.fb }
        fn is_finished(&self) -> bool { self.finished }
        fn player_count(&self) -> u32 { 0 }
        fn palette(&self) -> &[Color] {
            &[Color::BLACK, Color::WHITE]
        }
    }

    #[test]
    fn test_game_implements_trait() {
        let game = TestGame::new(64, 64);
        assert_eq!(game.width(), 64);
        assert_eq!(game.height(), 64);
        assert!(!game.is_finished());
    }

    #[test]
    fn test_game_handles_input() {
        let mut game = TestGame::new(64, 64);
        game.handle_input(GameInput {
            x: 10,
            y: 20,
            kind: InputKind::Click,
            player_id: "user1".into(),
        });
        assert_eq!(game.clicks, vec![(10, 20)]);
        assert_eq!(game.frame_buffer().get_pixel(10, 20), 1);
    }

    #[test]
    fn test_game_metadata() {
        let game = TestGame::new(128, 64);
        let meta = game.metadata();
        assert_eq!(meta.name, "Test");
        assert_eq!(meta.width, 128);
        assert_eq!(meta.height, 64);
    }
}
