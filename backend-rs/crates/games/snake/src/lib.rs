use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata, InputKind};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use std::collections::{HashMap, VecDeque};

const MOVE_INTERVAL: u32 = 3;
const FOOD_COUNT: usize = 5;
const INITIAL_LENGTH: usize = 3;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    Up,
    Down,
    Left,
    Right,
}

impl Direction {
    fn opposite(self) -> Self {
        match self {
            Direction::Up => Direction::Down,
            Direction::Down => Direction::Up,
            Direction::Left => Direction::Right,
            Direction::Right => Direction::Left,
        }
    }

    fn dx(self) -> i16 {
        match self {
            Direction::Left => -1,
            Direction::Right => 1,
            _ => 0,
        }
    }

    fn dy(self) -> i16 {
        match self {
            Direction::Up => -1,
            Direction::Down => 1,
            _ => 0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Snake {
    pub body: VecDeque<(u16, u16)>,
    pub direction: Direction,
    pub alive: bool,
    pub color_index: u8,
    pub score: u32,
}

// Palette indices
const BG: u8 = 0;
const C_FOOD: u8 = 1;
const C_BORDER: u8 = 2;
// Snake colors start at index 3
const C_SNAKE_BASE: u8 = 3;

const SNAKE_COLORS: [Color; 8] = [
    Color::new(50, 220, 50),   // green
    Color::new(50, 150, 255),  // blue
    Color::new(255, 80, 80),   // red
    Color::new(255, 220, 50),  // yellow
    Color::new(200, 80, 255),  // purple
    Color::new(255, 150, 50),  // orange
    Color::new(50, 220, 220),  // cyan
    Color::new(220, 100, 180), // pink
];

const PALETTE: [Color; 11] = [
    Color::new(0, 0, 0),       // 0: bg
    Color::new(255, 50, 50),   // 1: food
    Color::new(40, 40, 40),    // 2: border
    Color::new(50, 220, 50),   // 3: snake 0
    Color::new(50, 150, 255),  // 4: snake 1
    Color::new(255, 80, 80),   // 5: snake 2
    Color::new(255, 220, 50),  // 6: snake 3
    Color::new(200, 80, 255),  // 7: snake 4
    Color::new(255, 150, 50),  // 8: snake 5
    Color::new(50, 220, 220),  // 9: snake 6
    Color::new(220, 100, 180), // 10: snake 7
];

pub struct SnakeGame {
    fb: FrameBuffer,
    canvas_w: u16,
    canvas_h: u16,
    snakes: HashMap<String, Snake>,
    food: Vec<(u16, u16)>,
    move_timer: u32,
    next_color: u8,
    rng: StdRng,
    finished: bool,
}

impl SnakeGame {
    pub fn new(width: u16, height: u16) -> Self {
        let mut rng = StdRng::from_entropy();
        let mut food = Vec::new();
        for _ in 0..FOOD_COUNT {
            food.push((rng.gen_range(1..width - 1), rng.gen_range(1..height - 1)));
        }

        Self {
            fb: FrameBuffer::new(width, height),
            canvas_w: width,
            canvas_h: height,
            snakes: HashMap::new(),
            food,
            move_timer: 0,
            next_color: 0,
            rng,
            finished: false,
        }
    }

    #[cfg(test)]
    pub fn new_test(width: u16, height: u16) -> Self {
        Self {
            fb: FrameBuffer::new(width, height),
            canvas_w: width,
            canvas_h: height,
            snakes: HashMap::new(),
            food: vec![(width / 2, height / 2)],
            move_timer: 0,
            next_color: 0,
            rng: StdRng::seed_from_u64(42),
            finished: false,
        }
    }

    pub fn snake_count(&self) -> usize {
        self.snakes.len()
    }

    pub fn alive_snake_count(&self) -> usize {
        self.snakes.values().filter(|s| s.alive).count()
    }

    pub fn food_count(&self) -> usize {
        self.food.len()
    }

    pub fn get_snake(&self, player_id: &str) -> Option<&Snake> {
        self.snakes.get(player_id)
    }

    fn join_player(&mut self, player_id: &str) {
        if self.snakes.contains_key(player_id) {
            return;
        }
        let color_index = C_SNAKE_BASE + self.next_color;
        self.next_color = (self.next_color + 1) % SNAKE_COLORS.len() as u8;

        // Spawn at random position
        let x = self.rng.gen_range(5..self.canvas_w.saturating_sub(5).max(6));
        let y = self.rng.gen_range(5..self.canvas_h.saturating_sub(5).max(6));

        let mut body = VecDeque::new();
        for i in 0..INITIAL_LENGTH {
            body.push_back((x.saturating_sub(i as u16), y));
        }

        self.snakes.insert(
            player_id.to_string(),
            Snake {
                body,
                direction: Direction::Right,
                alive: true,
                color_index,
                score: 0,
            },
        );
    }

    fn move_snakes(&mut self) {
        let player_ids: Vec<String> = self.snakes.keys().cloned().collect();
        let mut new_heads: Vec<(String, u16, u16)> = Vec::new();

        // Calculate new head positions
        for pid in &player_ids {
            let snake = &self.snakes[pid];
            if !snake.alive {
                continue;
            }
            let (hx, hy) = snake.body[0];
            let nx = (hx as i16 + snake.direction.dx()).rem_euclid(self.canvas_w as i16) as u16;
            let ny = (hy as i16 + snake.direction.dy()).rem_euclid(self.canvas_h as i16) as u16;
            new_heads.push((pid.clone(), nx, ny));
        }

        // Check wall collisions (border pixels)
        for (pid, nx, ny) in &new_heads {
            if *nx == 0 || *nx >= self.canvas_w - 1 || *ny == 0 || *ny >= self.canvas_h - 1 {
                self.snakes.get_mut(pid.as_str()).unwrap().alive = false;
            }
        }

        // Check self and other-snake collisions
        let all_bodies: Vec<(u16, u16)> = self
            .snakes
            .values()
            .filter(|s| s.alive)
            .flat_map(|s| s.body.iter().copied())
            .collect();

        for (pid, nx, ny) in &new_heads {
            let snake = &self.snakes[pid];
            if !snake.alive {
                continue;
            }
            if all_bodies.contains(&(*nx, *ny)) {
                self.snakes.get_mut(pid.as_str()).unwrap().alive = false;
            }
        }

        // Move surviving snakes and check food
        for (pid, nx, ny) in new_heads {
            let snake = self.snakes.get_mut(&pid).unwrap();
            if !snake.alive {
                continue;
            }
            snake.body.push_front((nx, ny));

            // Check food
            if let Some(fi) = self.food.iter().position(|&f| f == (nx, ny)) {
                snake.score += 1;
                self.food.remove(fi);
                // Spawn new food
                let fx = self.rng.gen_range(2..self.canvas_w - 2);
                let fy = self.rng.gen_range(2..self.canvas_h - 2);
                self.food.push((fx, fy));
            } else {
                snake.body.pop_back();
            }
        }
    }

    fn render(&mut self) {
        self.fb.fill(BG);

        // Border
        for x in 0..self.canvas_w {
            self.fb.set_pixel(x, 0, C_BORDER);
            self.fb.set_pixel(x, self.canvas_h - 1, C_BORDER);
        }
        for y in 0..self.canvas_h {
            self.fb.set_pixel(0, y, C_BORDER);
            self.fb.set_pixel(self.canvas_w - 1, y, C_BORDER);
        }

        // Food
        for &(fx, fy) in &self.food {
            self.fb.set_pixel(fx, fy, C_FOOD);
        }

        // Snakes
        for snake in self.snakes.values() {
            if !snake.alive {
                continue;
            }
            for &(sx, sy) in &snake.body {
                self.fb.set_pixel(sx, sy, snake.color_index);
            }
        }
    }
}

impl Game for SnakeGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Snake Royale".into(),
            description: "Multiplayer snake — eat, grow, survive. Click or use chat commands to steer.".into(),
            width: self.canvas_w,
            height: self.canvas_h,
            max_players: Some(100),
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
        if self.finished {
            return;
        }

        self.move_timer += 1;
        if self.move_timer >= MOVE_INTERVAL {
            self.move_timer = 0;
            self.move_snakes();
        }

        self.render();
    }

    fn handle_input(&mut self, input: GameInput) {
        if self.finished {
            return;
        }

        // Auto-join on first input
        self.join_player(&input.player_id);

        let new_dir = match input.kind {
            InputKind::Click => {
                let snake = match self.snakes.get(&input.player_id) {
                    Some(s) if s.alive => s,
                    _ => return,
                };
                let (hx, hy) = snake.body[0];
                let dx = input.x as i16 - hx as i16;
                let dy = input.y as i16 - hy as i16;
                if dx.abs() > dy.abs() {
                    if dx > 0 { Direction::Right } else { Direction::Left }
                } else if dy > 0 {
                    Direction::Down
                } else {
                    Direction::Up
                }
            }
            InputKind::Chat(ref msg) => {
                match msg.trim().to_lowercase().as_str() {
                    "up" | "u" | "w" => Direction::Up,
                    "down" | "d" | "s" => Direction::Down,
                    "left" | "l" | "a" => Direction::Left,
                    "right" | "r" => Direction::Right,
                    _ => return,
                }
            }
        };

        if let Some(snake) = self.snakes.get_mut(&input.player_id) {
            if snake.alive && new_dir != snake.direction.opposite() {
                snake.direction = new_dir;
            }
        }
    }

    fn frame_buffer(&self) -> &FrameBuffer {
        &self.fb
    }

    fn is_finished(&self) -> bool {
        self.finished
    }

    fn player_count(&self) -> u32 {
        self.snakes.len() as u32
    }

    fn palette(&self) -> &[Color] {
        &PALETTE
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_game() -> SnakeGame {
        SnakeGame::new_test(64, 64)
    }

    #[test]
    fn creates_with_dimensions() {
        let game = make_game();
        assert_eq!(game.width(), 64);
        assert_eq!(game.height(), 64);
        assert!(!game.is_finished());
    }

    #[test]
    fn player_joins_on_input() {
        let mut game = make_game();
        assert_eq!(game.snake_count(), 0);
        game.handle_input(GameInput {
            x: 40,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        assert_eq!(game.snake_count(), 1);
        assert_eq!(game.alive_snake_count(), 1);
    }

    #[test]
    fn snake_moves_on_update() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        let head_before = game.get_snake("p1").unwrap().body[0];
        for _ in 0..MOVE_INTERVAL + 1 {
            game.update();
        }
        let head_after = game.get_snake("p1").unwrap().body[0];
        assert_ne!(head_before, head_after);
    }

    #[test]
    fn snake_changes_direction_via_click() {
        let mut game = make_game();
        // Join and set direction to right
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        assert_eq!(game.get_snake("p1").unwrap().direction, Direction::Right);

        // Click below snake → should change to Down
        let (hx, hy) = game.get_snake("p1").unwrap().body[0];
        game.handle_input(GameInput {
            x: hx,
            y: hy + 10,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        assert_eq!(game.get_snake("p1").unwrap().direction, Direction::Down);
    }

    #[test]
    fn cannot_reverse_direction() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        // Direction is Right, try to go Left (opposite)
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("left".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.get_snake("p1").unwrap().direction, Direction::Right);
    }

    #[test]
    fn chat_commands_change_direction() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("down".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.get_snake("p1").unwrap().direction, Direction::Down);
    }

    #[test]
    fn snake_eats_food_and_grows() {
        let mut game = make_game();
        // Place snake right next to food
        let food_pos = game.food[0];
        let mut body = VecDeque::new();
        body.push_back((food_pos.0 - 1, food_pos.1));
        body.push_back((food_pos.0 - 2, food_pos.1));
        body.push_back((food_pos.0 - 3, food_pos.1));
        game.snakes.insert(
            "p1".into(),
            Snake {
                body,
                direction: Direction::Right,
                alive: true,
                color_index: C_SNAKE_BASE,
                score: 0,
            },
        );
        let len_before = game.get_snake("p1").unwrap().body.len();
        game.move_snakes();
        let len_after = game.get_snake("p1").unwrap().body.len();
        assert_eq!(len_after, len_before + 1);
        assert_eq!(game.get_snake("p1").unwrap().score, 1);
    }

    #[test]
    fn snake_dies_at_border() {
        let mut game = make_game();
        // Place snake heading into border
        let mut body = VecDeque::new();
        body.push_back((1, 10));
        body.push_back((2, 10));
        body.push_back((3, 10));
        game.snakes.insert(
            "p1".into(),
            Snake {
                body,
                direction: Direction::Left,
                alive: true,
                color_index: C_SNAKE_BASE,
                score: 0,
            },
        );
        game.move_snakes();
        assert!(!game.get_snake("p1").unwrap().alive);
    }

    #[test]
    fn snake_dies_on_self_collision() {
        let mut game = make_game();
        // Create a snake that has looped back on itself
        let mut body = VecDeque::new();
        body.push_back((10, 10)); // head
        body.push_back((11, 10));
        body.push_back((11, 11));
        body.push_back((10, 11));
        body.push_back((9, 11));
        body.push_back((9, 10));
        body.push_back((9, 9));
        body.push_back((10, 9));
        // Heading Down means next position is (10, 11) which is in the body
        game.snakes.insert(
            "p1".into(),
            Snake {
                body,
                direction: Direction::Down,
                alive: true,
                color_index: C_SNAKE_BASE,
                score: 0,
            },
        );
        game.move_snakes();
        assert!(!game.get_snake("p1").unwrap().alive);
    }

    #[test]
    fn multiple_players_supported() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p2".into(),
        });
        assert_eq!(game.snake_count(), 2);
        assert_eq!(game.player_count(), 2);
    }

    #[test]
    fn render_produces_pixels() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 50,
            y: 32,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        game.update();
        let has_nonzero = game.frame_buffer().pixels().iter().any(|&p| p != 0);
        assert!(has_nonzero);
    }

    #[test]
    fn palette_correct_size() {
        let game = make_game();
        assert_eq!(game.palette().len(), 11);
    }

    #[test]
    fn food_respawns_after_eaten() {
        let mut game = make_game();
        let initial_food = game.food_count();
        // Place snake right next to food
        let food_pos = game.food[0];
        let mut body = VecDeque::new();
        body.push_back((food_pos.0 - 1, food_pos.1));
        body.push_back((food_pos.0 - 2, food_pos.1));
        game.snakes.insert(
            "p1".into(),
            Snake {
                body,
                direction: Direction::Right,
                alive: true,
                color_index: C_SNAKE_BASE,
                score: 0,
            },
        );
        game.move_snakes();
        assert_eq!(game.food_count(), initial_food);
    }

    #[test]
    fn direction_opposite() {
        assert_eq!(Direction::Up.opposite(), Direction::Down);
        assert_eq!(Direction::Down.opposite(), Direction::Up);
        assert_eq!(Direction::Left.opposite(), Direction::Right);
        assert_eq!(Direction::Right.opposite(), Direction::Left);
    }
}
