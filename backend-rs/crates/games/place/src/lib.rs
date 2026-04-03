use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata, InputKind};

const PALETTE: [Color; 8] = [
    Color::new(189, 189, 189), // 0: inactive (light gray)
    Color::new(96, 96, 96),    // 1: dark gray
    Color::new(255, 0, 0),     // 2: red
    Color::new(0, 255, 0),     // 3: green
    Color::new(0, 0, 255),     // 4: blue
    Color::new(255, 255, 0),   // 5: yellow
    Color::new(255, 0, 255),   // 6: magenta
    Color::new(0, 255, 255),   // 7: cyan
];

pub struct PlaceGame {
    fb: FrameBuffer,
    width: u16,
    height: u16,
    owners: Vec<Option<String>>,
    player_count: u32,
}

impl PlaceGame {
    pub fn new(width: u16, height: u16) -> Self {
        Self {
            fb: FrameBuffer::new(width, height),
            width,
            height,
            owners: vec![None; width as usize * height as usize],
            player_count: 0,
        }
    }

    pub fn owner_at(&self, x: u16, y: u16) -> Option<&str> {
        if x >= self.width || y >= self.height {
            return None;
        }
        self.owners[y as usize * self.width as usize + x as usize].as_deref()
    }
}

impl Game for PlaceGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Place".into(),
            description: "Click pixels to toggle their color. Collaborative pixel art canvas.".into(),
            width: self.width,
            height: self.height,
            max_players: None,
            supports_chat: true,
        }
    }

    fn width(&self) -> u16 {
        self.width
    }

    fn height(&self) -> u16 {
        self.height
    }

    fn update(&mut self) {
        // Place is passive — no per-tick logic
    }

    fn handle_input(&mut self, input: GameInput) {
        if input.x >= self.width || input.y >= self.height {
            return;
        }
        if let InputKind::Click = input.kind {
            let idx = input.y as usize * self.width as usize + input.x as usize;
            let current = self.fb.get_pixel(input.x, input.y);
            let next = (current + 1) % PALETTE.len() as u8;
            self.fb.set_pixel(input.x, input.y, next);
            self.owners[idx] = Some(input.player_id);
        }
    }

    fn frame_buffer(&self) -> &FrameBuffer {
        &self.fb
    }

    fn is_finished(&self) -> bool {
        false // Place never ends
    }

    fn player_count(&self) -> u32 {
        self.player_count
    }

    fn palette(&self) -> &[Color] {
        &PALETTE
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_game(w: u16, h: u16) -> PlaceGame {
        PlaceGame::new(w, h)
    }

    fn click(game: &mut PlaceGame, x: u16, y: u16, player: &str) {
        game.handle_input(GameInput {
            x,
            y,
            kind: InputKind::Click,
            player_id: player.into(),
        });
    }

    #[test]
    fn new_game_has_all_zeroes() {
        let game = make_game(64, 64);
        assert!(game.frame_buffer().pixels().iter().all(|&p| p == 0));
    }

    #[test]
    fn click_toggles_pixel_color() {
        let mut game = make_game(64, 64);
        click(&mut game, 10, 10, "alice");
        assert_eq!(game.frame_buffer().get_pixel(10, 10), 1);
    }

    #[test]
    fn multiple_clicks_cycle_colors() {
        let mut game = make_game(64, 64);
        for i in 0..PALETTE.len() as u8 {
            assert_eq!(game.frame_buffer().get_pixel(5, 5), i);
            click(&mut game, 5, 5, "alice");
        }
        assert_eq!(game.frame_buffer().get_pixel(5, 5), 0); // wraps around
    }

    #[test]
    fn click_tracks_owner() {
        let mut game = make_game(64, 64);
        click(&mut game, 10, 10, "alice");
        assert_eq!(game.owner_at(10, 10), Some("alice"));
    }

    #[test]
    fn different_players_overwrite_owner() {
        let mut game = make_game(64, 64);
        click(&mut game, 10, 10, "alice");
        click(&mut game, 10, 10, "bob");
        assert_eq!(game.owner_at(10, 10), Some("bob"));
    }

    #[test]
    fn out_of_bounds_click_is_ignored() {
        let mut game = make_game(32, 32);
        click(&mut game, 100, 100, "alice");
        // Should not panic, no effect
    }

    #[test]
    fn place_never_finishes() {
        let game = make_game(64, 64);
        assert!(!game.is_finished());
    }

    #[test]
    fn metadata_is_correct() {
        let game = make_game(128, 64);
        let meta = game.metadata();
        assert_eq!(meta.name, "Place");
        assert_eq!(meta.width, 128);
        assert_eq!(meta.height, 64);
    }

    #[test]
    fn click_marks_tile_dirty() {
        let mut game = make_game(64, 64);
        click(&mut game, 10, 10, "alice");
        assert!(game.frame_buffer().has_dirty_tiles());
    }

    #[test]
    fn palette_has_8_colors() {
        let game = make_game(64, 64);
        assert_eq!(game.palette().len(), 8);
    }

    #[test]
    fn unowned_pixel_returns_none() {
        let game = make_game(64, 64);
        assert_eq!(game.owner_at(10, 10), None);
    }
}
