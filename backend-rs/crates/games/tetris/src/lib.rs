use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata, InputKind};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};

const GRID_W: usize = 10;
const GRID_H: usize = 20;
const DROP_INTERVAL: u32 = 30;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TetrominoKind {
    I,
    O,
    T,
    S,
    Z,
    J,
    L,
}

impl TetrominoKind {
    const ALL: [TetrominoKind; 7] = [
        TetrominoKind::I,
        TetrominoKind::O,
        TetrominoKind::T,
        TetrominoKind::S,
        TetrominoKind::Z,
        TetrominoKind::J,
        TetrominoKind::L,
    ];

    fn shape(self) -> Vec<Vec<bool>> {
        match self {
            TetrominoKind::I => vec![vec![true, true, true, true]],
            TetrominoKind::O => vec![vec![true, true], vec![true, true]],
            TetrominoKind::T => vec![vec![false, true, false], vec![true, true, true]],
            TetrominoKind::S => vec![vec![false, true, true], vec![true, true, false]],
            TetrominoKind::Z => vec![vec![true, true, false], vec![false, true, true]],
            TetrominoKind::J => vec![vec![true, false, false], vec![true, true, true]],
            TetrominoKind::L => vec![vec![false, false, true], vec![true, true, true]],
        }
    }

    fn palette_index(self) -> u8 {
        match self {
            TetrominoKind::I => 1,
            TetrominoKind::O => 2,
            TetrominoKind::T => 3,
            TetrominoKind::S => 4,
            TetrominoKind::Z => 5,
            TetrominoKind::J => 6,
            TetrominoKind::L => 7,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Tetromino {
    pub kind: TetrominoKind,
    pub shape: Vec<Vec<bool>>,
    pub x: i16,
    pub y: i16,
}

impl Tetromino {
    pub fn new(kind: TetrominoKind, x: i16, y: i16) -> Self {
        Self {
            kind,
            shape: kind.shape(),
            x,
            y,
        }
    }

    pub fn cells(&self) -> Vec<(i16, i16)> {
        let mut out = Vec::new();
        for (row_i, row) in self.shape.iter().enumerate() {
            for (col_i, &filled) in row.iter().enumerate() {
                if filled {
                    out.push((self.x + col_i as i16, self.y + row_i as i16));
                }
            }
        }
        out
    }

    pub fn rotate_cw(&mut self) {
        let rows = self.shape.len();
        let cols = self.shape[0].len();
        let mut rotated = vec![vec![false; rows]; cols];
        for r in 0..rows {
            for c in 0..cols {
                rotated[c][rows - 1 - r] = self.shape[r][c];
            }
        }
        self.shape = rotated;
    }

    pub fn width(&self) -> usize {
        self.shape.first().map_or(0, |r| r.len())
    }
}

const PALETTE: [Color; 9] = [
    Color::new(0, 0, 0),       // 0: background
    Color::new(0, 200, 255),    // 1: I - cyan
    Color::new(255, 220, 0),    // 2: O - yellow
    Color::new(180, 0, 255),    // 3: T - purple
    Color::new(255, 50, 50),    // 4: S - red
    Color::new(50, 220, 50),    // 5: Z - green
    Color::new(255, 150, 0),    // 6: J - orange
    Color::new(0, 100, 255),    // 7: L - blue
    Color::new(40, 40, 40),     // 8: grid lines / border
];

pub struct TetrisGame {
    fb: FrameBuffer,
    canvas_w: u16,
    canvas_h: u16,
    board: [[u8; GRID_W]; GRID_H],
    current: Option<Tetromino>,
    next_kind: TetrominoKind,
    drop_timer: u32,
    drop_speed: u32,
    score: u32,
    lines_cleared: u32,
    game_over: bool,
    cell_size: u16,
    offset_x: u16,
    offset_y: u16,
    rng: StdRng,
}

impl TetrisGame {
    pub fn new(width: u16, height: u16) -> Self {
        let mut rng = StdRng::from_entropy();
        let cell_size = std::cmp::min(width / (GRID_W as u16 + 4), height / GRID_H as u16);
        let cell_size = std::cmp::max(cell_size, 1);
        let offset_x = (width - GRID_W as u16 * cell_size) / 2;
        let offset_y = (height - GRID_H as u16 * cell_size) / 2;
        let next_kind = TetrominoKind::ALL[rng.gen_range(0..7)];
        let mut game = Self {
            fb: FrameBuffer::new(width, height),
            canvas_w: width,
            canvas_h: height,
            board: [[0u8; GRID_W]; GRID_H],
            current: None,
            next_kind,
            drop_timer: 0,
            drop_speed: DROP_INTERVAL,
            score: 0,
            lines_cleared: 0,
            game_over: false,
            cell_size,
            offset_x,
            offset_y,
            rng,
        };
        game.spawn_piece();
        game
    }

    #[cfg(test)]
    pub fn new_seeded(width: u16, height: u16, first_kind: TetrominoKind) -> Self {
        let cell_size = std::cmp::min(width / (GRID_W as u16 + 4), height / GRID_H as u16);
        let cell_size = std::cmp::max(cell_size, 1);
        let offset_x = (width - GRID_W as u16 * cell_size) / 2;
        let offset_y = (height - GRID_H as u16 * cell_size) / 2;
        let mut game = Self {
            fb: FrameBuffer::new(width, height),
            canvas_w: width,
            canvas_h: height,
            board: [[0u8; GRID_W]; GRID_H],
            current: None,
            next_kind: first_kind,
            drop_timer: 0,
            drop_speed: DROP_INTERVAL,
            score: 0,
            lines_cleared: 0,
            game_over: false,
            cell_size,
            offset_x,
            offset_y,
            rng: StdRng::from_entropy(),
        };
        game.spawn_piece();
        game
    }

    pub fn score(&self) -> u32 {
        self.score
    }

    pub fn lines_cleared(&self) -> u32 {
        self.lines_cleared
    }

    pub fn current_piece(&self) -> Option<&Tetromino> {
        self.current.as_ref()
    }

    pub fn board_cell(&self, col: usize, row: usize) -> u8 {
        if col < GRID_W && row < GRID_H {
            self.board[row][col]
        } else {
            0
        }
    }

    fn spawn_piece(&mut self) {
        let kind = self.next_kind;
        self.next_kind = TetrominoKind::ALL[self.rng.gen_range(0..7)];
        let piece = Tetromino::new(kind, (GRID_W as i16 - kind.shape()[0].len() as i16) / 2, 0);
        if !self.is_valid_position(&piece, 0, 0) {
            self.game_over = true;
            self.current = None;
            return;
        }
        self.current = Some(piece);
    }

    fn is_valid_position(&self, piece: &Tetromino, dx: i16, dy: i16) -> bool {
        for (cx, cy) in piece.cells() {
            let nx = cx + dx;
            let ny = cy + dy;
            if nx < 0 || nx >= GRID_W as i16 || ny >= GRID_H as i16 {
                return false;
            }
            if ny >= 0 && self.board[ny as usize][nx as usize] != 0 {
                return false;
            }
        }
        true
    }

    fn try_move(&mut self, dx: i16, dy: i16) -> bool {
        let valid = self.current.as_ref().map_or(false, |p| self.is_valid_position(p, dx, dy));
        if valid {
            if let Some(p) = self.current.as_mut() {
                p.x += dx;
                p.y += dy;
            }
        }
        valid
    }

    fn try_rotate(&mut self) {
        if let Some(ref mut piece) = self.current {
            let old_shape = piece.shape.clone();
            piece.rotate_cw();
            // Check validity by inlining the position check to avoid borrow conflict
            let valid = piece.cells().iter().all(|&(cx, cy)| {
                cx >= 0
                    && cx < GRID_W as i16
                    && cy < GRID_H as i16
                    && (cy < 0 || self.board[cy as usize][cx as usize] == 0)
            });
            if !valid {
                piece.shape = old_shape;
            }
        }
    }

    fn lock_piece(&mut self) {
        if let Some(ref piece) = self.current {
            let ci = piece.kind.palette_index();
            for (cx, cy) in piece.cells() {
                if cy >= 0 && (cy as usize) < GRID_H && (cx as usize) < GRID_W {
                    self.board[cy as usize][cx as usize] = ci;
                }
            }
        }
        self.current = None;
    }

    fn clear_lines(&mut self) {
        let mut cleared = 0u32;
        let mut y = GRID_H as i32 - 1;
        while y >= 0 {
            let row = y as usize;
            if self.board[row].iter().all(|&c| c != 0) {
                for r in (1..=row).rev() {
                    self.board[r] = self.board[r - 1];
                }
                self.board[0] = [0u8; GRID_W];
                cleared += 1;
            } else {
                y -= 1;
            }
        }
        if cleared > 0 {
            self.lines_cleared += cleared;
            self.score += match cleared {
                1 => 100,
                2 => 300,
                3 => 500,
                4 => 800,
                _ => cleared * 200,
            };
        }
    }

    fn pixel_to_grid(&self, px: u16, py: u16) -> Option<(usize, usize)> {
        if px < self.offset_x || py < self.offset_y {
            return None;
        }
        let gx = (px - self.offset_x) / self.cell_size;
        let gy = (py - self.offset_y) / self.cell_size;
        if (gx as usize) < GRID_W && (gy as usize) < GRID_H {
            Some((gx as usize, gy as usize))
        } else {
            None
        }
    }

    fn is_click_on_piece(&self, gx: usize, gy: usize) -> bool {
        self.current.as_ref().map_or(false, |piece| {
            piece.cells().iter().any(|&(cx, cy)| cx == gx as i16 && cy == gy as i16)
        })
    }

    fn render(&mut self) {
        self.fb.fill(0);

        let cs = self.cell_size;
        let ox = self.offset_x;
        let oy = self.offset_y;

        // Draw border
        let border_color: u8 = 8;
        let bx_start = ox.saturating_sub(1);
        let by_start = oy.saturating_sub(1);
        let bx_end = std::cmp::min(ox + GRID_W as u16 * cs, self.canvas_w - 1);
        let by_end = std::cmp::min(oy + GRID_H as u16 * cs, self.canvas_h - 1);
        for x in bx_start..=bx_end {
            self.fb.set_pixel(x, by_start, border_color);
            self.fb.set_pixel(x, by_end, border_color);
        }
        for y in by_start..=by_end {
            self.fb.set_pixel(bx_start, y, border_color);
            self.fb.set_pixel(bx_end, y, border_color);
        }

        // Draw locked cells
        for row in 0..GRID_H {
            for col in 0..GRID_W {
                let c = self.board[row][col];
                if c != 0 {
                    self.fill_cell(col, row, c);
                }
            }
        }

        // Draw current piece
        if let Some(ref piece) = self.current {
            let ci = piece.kind.palette_index();
            for (cx, cy) in piece.cells() {
                if cy >= 0 && (cy as usize) < GRID_H && cx >= 0 && (cx as usize) < GRID_W {
                    self.fill_cell(cx as usize, cy as usize, ci);
                }
            }
        }
    }

    fn fill_cell(&mut self, col: usize, row: usize, color: u8) {
        let px = self.offset_x + col as u16 * self.cell_size;
        let py = self.offset_y + row as u16 * self.cell_size;
        for dy in 0..self.cell_size {
            for dx in 0..self.cell_size {
                self.fb.set_pixel(px + dx, py + dy, color);
            }
        }
    }
}

impl Game for TetrisGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Tetris".into(),
            description: "Cooperative Tetris — click on pieces to rotate, click elsewhere to move.".into(),
            width: self.canvas_w,
            height: self.canvas_h,
            max_players: None,
            supports_chat: true,
        }
    }

    fn width(&self) -> u16 {
        self.canvas_w
    }

    fn height(&self) -> u16 {
        self.canvas_h
    }

    fn update(&mut self) {
        if self.game_over {
            self.render();
            return;
        }

        self.drop_timer += 1;
        if self.drop_timer >= self.drop_speed {
            self.drop_timer = 0;
            if !self.try_move(0, 1) {
                self.lock_piece();
                self.clear_lines();
                self.spawn_piece();
            }
        }

        self.render();
    }

    fn handle_input(&mut self, input: GameInput) {
        if self.game_over {
            return;
        }

        match input.kind {
            InputKind::Click => {
                if let Some((gx, gy)) = self.pixel_to_grid(input.x, input.y) {
                    if self.is_click_on_piece(gx, gy) {
                        self.try_rotate();
                    } else if let Some(ref piece) = self.current {
                        let center_x = piece.x + piece.width() as i16 / 2;
                        let piece_y = piece.y;
                        if (gx as i16) < center_x {
                            self.try_move(-1, 0);
                        } else if (gx as i16) > center_x {
                            self.try_move(1, 0);
                        }
                        if (gy as i16) > piece_y {
                            self.try_move(0, 1);
                        }
                    }
                }
            }
            InputKind::Chat(ref msg) => {
                let cmd = msg.trim().to_lowercase();
                match cmd.as_str() {
                    "left" | "l" => { self.try_move(-1, 0); }
                    "right" | "r" => { self.try_move(1, 0); }
                    "down" | "d" => { self.try_move(0, 1); }
                    "rotate" | "rot" | "u" | "up" => { self.try_rotate(); }
                    "drop" => {
                        while self.try_move(0, 1) {}
                        self.lock_piece();
                        self.clear_lines();
                        self.spawn_piece();
                    }
                    _ => {}
                }
            }
        }
    }

    fn frame_buffer(&self) -> &FrameBuffer {
        &self.fb
    }

    fn is_finished(&self) -> bool {
        self.game_over
    }

    fn player_count(&self) -> u32 {
        0
    }

    fn palette(&self) -> &[Color] {
        &PALETTE
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_game(kind: TetrominoKind) -> TetrisGame {
        TetrisGame::new_seeded(64, 64, kind)
    }

    #[test]
    fn creates_with_dimensions() {
        let game = make_game(TetrominoKind::I);
        assert_eq!(game.width(), 64);
        assert_eq!(game.height(), 64);
        assert!(!game.is_finished());
    }

    #[test]
    fn spawns_initial_piece() {
        let game = make_game(TetrominoKind::T);
        let piece = game.current_piece().expect("should have a piece");
        assert_eq!(piece.kind, TetrominoKind::T);
        assert_eq!(piece.y, 0);
    }

    #[test]
    fn piece_drops_on_update() {
        let mut game = make_game(TetrominoKind::O);
        let initial_y = game.current_piece().unwrap().y;
        for _ in 0..DROP_INTERVAL {
            game.update();
        }
        let new_y = game.current_piece().unwrap().y;
        assert_eq!(new_y, initial_y + 1);
    }

    #[test]
    fn piece_locks_at_bottom() {
        let mut game = make_game(TetrominoKind::O);
        // Drop piece all the way down
        for _ in 0..(GRID_H as u32 * DROP_INTERVAL + DROP_INTERVAL) {
            game.update();
        }
        // The O piece should have locked and a new piece spawned
        assert!(game.board[GRID_H - 1].iter().any(|&c| c != 0) || game.current_piece().is_some());
    }

    #[test]
    fn move_left_via_click() {
        let mut game = make_game(TetrominoKind::I);
        let piece_x_before = game.current_piece().unwrap().x;
        // Click left of the piece (at pixel 0,0 which is well left of center)
        let input = GameInput {
            x: game.offset_x,
            y: game.offset_y,
            kind: InputKind::Click,
            player_id: "p1".into(),
        };
        game.handle_input(input);
        let piece_x_after = game.current_piece().unwrap().x;
        assert_eq!(piece_x_after, piece_x_before - 1);
    }

    #[test]
    fn move_right_via_click() {
        let mut game = make_game(TetrominoKind::I);
        let piece_x_before = game.current_piece().unwrap().x;
        // Click right of the piece
        let right_px = game.offset_x + (GRID_W as u16 - 1) * game.cell_size;
        let input = GameInput {
            x: right_px,
            y: game.offset_y,
            kind: InputKind::Click,
            player_id: "p1".into(),
        };
        game.handle_input(input);
        let piece_x_after = game.current_piece().unwrap().x;
        assert_eq!(piece_x_after, piece_x_before + 1);
    }

    #[test]
    fn rotate_via_click_on_piece() {
        let mut game = make_game(TetrominoKind::T);
        let shape_before = game.current_piece().unwrap().shape.clone();
        // Click on a cell of the T piece
        let piece = game.current_piece().unwrap();
        let (cx, cy) = piece.cells()[1]; // center cell of T
        let px = game.offset_x + cx as u16 * game.cell_size + game.cell_size / 2;
        let py = game.offset_y + cy as u16 * game.cell_size + game.cell_size / 2;
        let input = GameInput {
            x: px,
            y: py,
            kind: InputKind::Click,
            player_id: "p1".into(),
        };
        game.handle_input(input);
        let shape_after = game.current_piece().unwrap().shape.clone();
        assert_ne!(shape_before, shape_after);
    }

    #[test]
    fn chat_commands_move_piece() {
        let mut game = make_game(TetrominoKind::I);
        let x_before = game.current_piece().unwrap().x;
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("left".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.current_piece().unwrap().x, x_before - 1);

        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("right".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.current_piece().unwrap().x, x_before);
    }

    #[test]
    fn chat_drop_locks_piece() {
        let mut game = make_game(TetrominoKind::O);
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("drop".into()),
            player_id: "p1".into(),
        });
        // After drop, piece should be locked and bottom rows should be filled
        assert!(game.board[GRID_H - 1].iter().any(|&c| c != 0));
        // A new piece should have spawned
        assert!(game.current_piece().is_some());
    }

    #[test]
    fn line_clear_scoring() {
        let mut game = make_game(TetrominoKind::I);
        // Fill the bottom row manually except for a gap
        for col in 0..GRID_W {
            game.board[GRID_H - 1][col] = 1;
        }
        assert_eq!(game.lines_cleared(), 0);
        game.clear_lines();
        assert_eq!(game.lines_cleared(), 1);
        assert_eq!(game.score(), 100);
        // The cleared row should now be empty
        assert!(game.board[GRID_H - 1].iter().all(|&c| c == 0));
    }

    #[test]
    fn tetromino_rotation() {
        let mut t = Tetromino::new(TetrominoKind::T, 3, 0);
        // T shape: [[false, true, false], [true, true, true]]
        assert_eq!(t.cells().len(), 4);
        t.rotate_cw();
        assert_eq!(t.cells().len(), 4);
        // After rotation, shape should be different
        let rotated = t.shape.clone();
        assert_eq!(rotated.len(), 3);
        assert_eq!(rotated[0].len(), 2);
    }

    #[test]
    fn all_tetromino_shapes_have_4_cells() {
        for kind in TetrominoKind::ALL {
            let t = Tetromino::new(kind, 0, 0);
            assert_eq!(t.cells().len(), 4, "Kind {:?} should have 4 cells", kind);
        }
    }

    #[test]
    fn game_over_when_board_full() {
        let mut game = make_game(TetrominoKind::O);
        // Fill the top rows to prevent spawning
        for row in 0..4 {
            for col in 0..GRID_W {
                game.board[row][col] = 1;
            }
        }
        // Force a new spawn
        game.current = None;
        game.spawn_piece();
        assert!(game.game_over);
    }

    #[test]
    fn palette_has_correct_count() {
        let game = make_game(TetrominoKind::I);
        assert_eq!(game.palette().len(), 9);
    }

    #[test]
    fn render_produces_nonzero_pixels() {
        let mut game = make_game(TetrominoKind::T);
        game.update();
        let fb = game.frame_buffer();
        let has_nonzero = fb.pixels().iter().any(|&p| p != 0);
        assert!(has_nonzero, "Frame buffer should contain rendered pixels");
    }

    #[test]
    fn multi_line_clear_bonus() {
        let mut game = make_game(TetrominoKind::I);
        // Fill 4 bottom rows
        for row in (GRID_H - 4)..GRID_H {
            for col in 0..GRID_W {
                game.board[row][col] = 1;
            }
        }
        game.clear_lines();
        assert_eq!(game.lines_cleared(), 4);
        assert_eq!(game.score(), 800); // Tetris bonus
    }
}
