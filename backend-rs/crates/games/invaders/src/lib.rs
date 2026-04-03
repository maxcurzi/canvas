use canvas_game_engine::{Color, FrameBuffer, Game, GameInput, GameMetadata, InputKind};

const SHIP_W: i16 = 5;
const SHIP_H: i16 = 3;
const ALIEN_W: i16 = 4;
const ALIEN_H: i16 = 3;
const ALIEN_COLS: usize = 8;
const ALIEN_ROWS: usize = 2;
const ALIEN_SPACING: i16 = 6;
const ALIEN_MOVE_INTERVAL: u32 = 8;
const ALIEN_SHOOT_INTERVAL: u32 = 20;
const ROCKET_SPEED: i16 = 1;
const SHIELD_W: i16 = 3;
const SHIELD_H: i16 = 2;

// Palette indices
const BG: u8 = 0;
const C_SHIP: u8 = 1;
const C_ALIEN: u8 = 2;
const C_ROCKET_FRIENDLY: u8 = 3;
const C_ROCKET_ENEMY: u8 = 4;
const C_SHIELD: u8 = 5;
const C_BORDER: u8 = 6;

const PALETTE: [Color; 7] = [
    Color::new(0, 0, 0),       // 0: bg
    Color::new(50, 220, 50),   // 1: ship (green)
    Color::new(220, 50, 50),   // 2: alien (red)
    Color::new(100, 255, 100), // 3: friendly rocket (bright green)
    Color::new(255, 100, 100), // 4: enemy rocket (bright red)
    Color::new(80, 80, 220),   // 5: shield (blue)
    Color::new(40, 40, 40),    // 6: border
];

#[derive(Debug, Clone)]
struct Ship {
    x: i16,
    y: i16,
    health: i16,
}

#[derive(Debug, Clone)]
struct Alien {
    x: i16,
    y: i16,
    health: i16,
    alive: bool,
}

#[derive(Debug, Clone)]
struct Rocket {
    x: i16,
    y: i16,
    friendly: bool,
    alive: bool,
}

#[derive(Debug, Clone)]
struct Shield {
    x: i16,
    y: i16,
    health: i16,
}

pub struct InvadersGame {
    fb: FrameBuffer,
    canvas_w: u16,
    canvas_h: u16,
    ship: Ship,
    aliens: Vec<Alien>,
    rockets: Vec<Rocket>,
    shields: Vec<Shield>,
    alien_dir: i16,
    alien_timer: u32,
    alien_shoot_timer: u32,
    shoot_queue: Vec<i16>,
    tick: u32,
    finished: bool,
    humans_won: bool,
}

impl InvadersGame {
    pub fn new(width: u16, height: u16) -> Self {
        let ship_y = height as i16 - SHIP_H - 2;
        let ship = Ship {
            x: width as i16 / 2 - SHIP_W / 2,
            y: ship_y,
            health: 11,
        };

        let mut aliens = Vec::new();
        let total_w = ALIEN_COLS as i16 * ALIEN_SPACING;
        let start_x = (width as i16 - total_w) / 2;
        for row in 0..ALIEN_ROWS {
            for col in 0..ALIEN_COLS {
                aliens.push(Alien {
                    x: start_x + col as i16 * ALIEN_SPACING,
                    y: 4 + row as i16 * (ALIEN_H + 2),
                    health: 7,
                    alive: true,
                });
            }
        }

        Self {
            fb: FrameBuffer::new(width, height),
            canvas_w: width,
            canvas_h: height,
            ship,
            aliens,
            rockets: Vec::new(),
            shields: Vec::new(),
            alien_dir: 1,
            alien_timer: 0,
            alien_shoot_timer: 0,
            shoot_queue: Vec::new(),
            tick: 0,
            finished: false,
            humans_won: false,
        }
    }

    pub fn ship_health(&self) -> i16 {
        self.ship.health
    }

    pub fn alive_alien_count(&self) -> usize {
        self.aliens.iter().filter(|a| a.alive).count()
    }

    pub fn rocket_count(&self) -> usize {
        self.rockets.iter().filter(|r| r.alive).count()
    }

    pub fn shield_count(&self) -> usize {
        self.shields.len()
    }

    pub fn humans_won(&self) -> bool {
        self.humans_won
    }

    fn move_aliens(&mut self) {
        self.alien_timer += 1;
        if self.alien_timer < ALIEN_MOVE_INTERVAL {
            return;
        }
        self.alien_timer = 0;

        let mut should_reverse = false;
        for alien in self.aliens.iter().filter(|a| a.alive) {
            let nx = alien.x + self.alien_dir;
            if nx <= 0 || nx + ALIEN_W >= self.canvas_w as i16 {
                should_reverse = true;
                break;
            }
        }

        if should_reverse {
            self.alien_dir = -self.alien_dir;
            for alien in self.aliens.iter_mut().filter(|a| a.alive) {
                alien.y += 1;
            }
        } else {
            for alien in self.aliens.iter_mut().filter(|a| a.alive) {
                alien.x += self.alien_dir;
            }
        }
    }

    fn alien_shoot(&mut self) {
        self.alien_shoot_timer += 1;
        if self.alien_shoot_timer < ALIEN_SHOOT_INTERVAL {
            return;
        }
        self.alien_shoot_timer = 0;

        // Bottom-most alive alien in a random column shoots
        let alive: Vec<usize> = self.aliens.iter().enumerate()
            .filter(|(_, a)| a.alive)
            .map(|(i, _)| i)
            .collect();
        if let Some(&idx) = alive.last() {
            let alien = &self.aliens[idx];
            self.rockets.push(Rocket {
                x: alien.x + ALIEN_W / 2,
                y: alien.y + ALIEN_H,
                friendly: false,
                alive: true,
            });
        }
    }

    fn process_shoot_queue(&mut self) {
        for target_x in self.shoot_queue.drain(..).collect::<Vec<_>>() {
            self.rockets.push(Rocket {
                x: target_x,
                y: self.ship.y - 1,
                friendly: true,
                alive: true,
            });
        }
    }

    fn update_rockets(&mut self) {
        for rocket in self.rockets.iter_mut() {
            if !rocket.alive {
                continue;
            }
            if rocket.friendly {
                rocket.y -= ROCKET_SPEED;
            } else {
                rocket.y += ROCKET_SPEED;
            }
            if rocket.y < 0 || rocket.y >= self.canvas_h as i16 {
                rocket.alive = false;
            }
        }
    }

    fn check_collisions(&mut self) {
        // Friendly rockets vs aliens
        for rocket in self.rockets.iter_mut().filter(|r| r.alive && r.friendly) {
            for alien in self.aliens.iter_mut().filter(|a| a.alive) {
                if rocket.x >= alien.x
                    && rocket.x < alien.x + ALIEN_W
                    && rocket.y >= alien.y
                    && rocket.y < alien.y + ALIEN_H
                {
                    alien.health -= 2;
                    rocket.alive = false;
                    if alien.health <= 0 {
                        alien.alive = false;
                    }
                }
            }
        }

        // Enemy rockets vs ship
        for rocket in self.rockets.iter_mut().filter(|r| r.alive && !r.friendly) {
            if rocket.x >= self.ship.x
                && rocket.x < self.ship.x + SHIP_W
                && rocket.y >= self.ship.y
                && rocket.y < self.ship.y + SHIP_H
            {
                self.ship.health -= 1;
                rocket.alive = false;
            }
        }

        // Rockets vs shields
        for rocket in self.rockets.iter_mut().filter(|r| r.alive) {
            for shield in self.shields.iter_mut() {
                if rocket.x >= shield.x
                    && rocket.x < shield.x + SHIELD_W
                    && rocket.y >= shield.y
                    && rocket.y < shield.y + SHIELD_H
                {
                    shield.health -= 1;
                    rocket.alive = false;
                }
            }
        }
        self.shields.retain(|s| s.health > 0);

        // Rocket vs rocket
        let len = self.rockets.len();
        for i in 0..len {
            if !self.rockets[i].alive {
                continue;
            }
            for j in (i + 1)..len {
                if !self.rockets[j].alive {
                    continue;
                }
                if self.rockets[i].friendly != self.rockets[j].friendly
                    && (self.rockets[i].x - self.rockets[j].x).abs() <= 1
                    && (self.rockets[i].y - self.rockets[j].y).abs() <= 1
                {
                    self.rockets[i].alive = false;
                    self.rockets[j].alive = false;
                }
            }
        }

        // Aliens reaching ship
        for alien in self.aliens.iter().filter(|a| a.alive) {
            if alien.y + ALIEN_H >= self.ship.y {
                self.ship.health = 0;
            }
        }

        // Cleanup dead rockets
        self.rockets.retain(|r| r.alive);
    }

    fn check_win_condition(&mut self) {
        if self.ship.health <= 0 {
            self.finished = true;
            self.humans_won = false;
        }
        if self.aliens.iter().all(|a| !a.alive) {
            self.finished = true;
            self.humans_won = true;
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

        // Ship
        draw_rect(&mut self.fb, self.ship.x, self.ship.y, SHIP_W, SHIP_H, C_SHIP, self.canvas_w, self.canvas_h);

        // Aliens
        for alien in self.aliens.iter().filter(|a| a.alive) {
            draw_rect(&mut self.fb, alien.x, alien.y, ALIEN_W, ALIEN_H, C_ALIEN, self.canvas_w, self.canvas_h);
        }

        // Rockets
        for rocket in self.rockets.iter().filter(|r| r.alive) {
            let c = if rocket.friendly { C_ROCKET_FRIENDLY } else { C_ROCKET_ENEMY };
            self.fb.set_pixel(rocket.x as u16, rocket.y as u16, c);
            if rocket.y + 1 < self.canvas_h as i16 {
                self.fb.set_pixel(rocket.x as u16, (rocket.y + 1) as u16, c);
            }
        }

        // Shields
        for shield in &self.shields {
            draw_rect(&mut self.fb, shield.x, shield.y, SHIELD_W, SHIELD_H, C_SHIELD, self.canvas_w, self.canvas_h);
        }
    }

    fn is_on_alien(&self, px: u16, py: u16) -> Option<usize> {
        for (i, alien) in self.aliens.iter().enumerate() {
            if !alien.alive {
                continue;
            }
            if px as i16 >= alien.x
                && (px as i16) < alien.x + ALIEN_W
                && py as i16 >= alien.y
                && (py as i16) < alien.y + ALIEN_H
            {
                return Some(i);
            }
        }
        None
    }

    fn is_on_ship(&self, px: u16, py: u16) -> bool {
        px as i16 >= self.ship.x
            && (px as i16) < self.ship.x + SHIP_W
            && py as i16 >= self.ship.y
            && (py as i16) < self.ship.y + SHIP_H
    }
}

fn draw_rect(fb: &mut FrameBuffer, x: i16, y: i16, w: i16, h: i16, color: u8, cw: u16, ch: u16) {
    for dy in 0..h {
        for dx in 0..w {
            let px = x + dx;
            let py = y + dy;
            if px >= 0 && px < cw as i16 && py >= 0 && py < ch as i16 {
                fb.set_pixel(px as u16, py as u16, color);
            }
        }
    }
}
                
impl Game for InvadersGame {
    fn metadata(&self) -> GameMetadata {
        GameMetadata {
            name: "Space Invaders".into(),
            description: "Cooperative Space Invaders — click aliens to shoot, click empty space to place shields.".into(),
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
        if self.finished {
            self.render();
            return;
        }

        self.tick += 1;
        self.move_aliens();
        self.alien_shoot();
        self.process_shoot_queue();
        self.update_rockets();
        self.check_collisions();
        self.check_win_condition();
        self.render();
    }

    fn handle_input(&mut self, input: GameInput) {
        if self.finished {
            return;
        }

        match input.kind {
            InputKind::Click => {
                if self.is_on_alien(input.x, input.y).is_some() {
                    // Click on alien → queue a rocket aimed at that X
                    self.shoot_queue.push(input.x as i16);
                } else if !self.is_on_ship(input.x, input.y) {
                    // Click empty space → place shield
                    let sx = input.x as i16 - SHIELD_W / 2;
                    let sy = input.y as i16 - SHIELD_H / 2;
                    if self.shields.len() < 10 {
                        self.shields.push(Shield {
                            x: sx,
                            y: sy,
                            health: 3,
                        });
                    }
                }
            }
            InputKind::Chat(ref msg) => {
                let cmd = msg.trim().to_lowercase();
                match cmd.as_str() {
                    "left" | "l" => {
                        if self.ship.x > 1 {
                            self.ship.x -= 1;
                        }
                    }
                    "right" | "r" => {
                        if self.ship.x + SHIP_W < self.canvas_w as i16 - 1 {
                            self.ship.x += 1;
                        }
                    }
                    "shoot" | "fire" | "s" => {
                        self.shoot_queue.push(self.ship.x + SHIP_W / 2);
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
        self.finished
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

    fn make_game() -> InvadersGame {
        InvadersGame::new(64, 64)
    }

    #[test]
    fn creates_with_dimensions() {
        let game = make_game();
        assert_eq!(game.width(), 64);
        assert_eq!(game.height(), 64);
        assert!(!game.is_finished());
    }

    #[test]
    fn initial_state() {
        let game = make_game();
        assert_eq!(game.ship_health(), 11);
        assert_eq!(game.alive_alien_count(), ALIEN_COLS * ALIEN_ROWS);
        assert_eq!(game.rocket_count(), 0);
        assert_eq!(game.shield_count(), 0);
    }

    #[test]
    fn click_on_alien_queues_rocket() {
        let mut game = make_game();
        let alien = &game.aliens[0];
        let ax = alien.x as u16 + 1;
        let ay = alien.y as u16 + 1;
        game.handle_input(GameInput {
            x: ax,
            y: ay,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        assert_eq!(game.shoot_queue.len(), 1);
        game.update();
        assert_eq!(game.rocket_count(), 1);
    }

    #[test]
    fn click_empty_places_shield() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 32,
            y: 50,
            kind: InputKind::Click,
            player_id: "p1".into(),
        });
        assert_eq!(game.shield_count(), 1);
    }

    #[test]
    fn shield_limit() {
        let mut game = make_game();
        for i in 0..15 {
            game.handle_input(GameInput {
                x: 10 + i * 3,
                y: 50,
                kind: InputKind::Click,
                player_id: "p1".into(),
            });
        }
        assert_eq!(game.shield_count(), 10);
    }

    #[test]
    fn aliens_move_over_time() {
        let mut game = make_game();
        let initial_x = game.aliens[0].x;
        for _ in 0..ALIEN_MOVE_INTERVAL + 1 {
            game.update();
        }
        assert_ne!(game.aliens[0].x, initial_x);
    }

    #[test]
    fn friendly_rocket_kills_alien() {
        let mut game = make_game();
        let alien = &game.aliens[0];
        // Place a friendly rocket just above the first alien
        game.rockets.push(Rocket {
            x: alien.x + 1,
            y: alien.y - 1,
            friendly: true,
            alive: true,
        });
        // Run enough updates for the rocket to hit (it moves up, but alien is above)
        // Actually, place rocket right on the alien
        game.rockets.clear();
        game.rockets.push(Rocket {
            x: game.aliens[0].x + 1,
            y: game.aliens[0].y + 1,
            friendly: true,
            alive: true,
        });
        // Kill alien by reducing health first
        game.aliens[0].health = 2;
        game.check_collisions();
        assert!(!game.aliens[0].alive);
    }

    #[test]
    fn enemy_rocket_damages_ship() {
        let mut game = make_game();
        let initial_health = game.ship_health();
        game.rockets.push(Rocket {
            x: game.ship.x + 1,
            y: game.ship.y + 1,
            friendly: false,
            alive: true,
        });
        game.check_collisions();
        assert_eq!(game.ship_health(), initial_health - 1);
    }

    #[test]
    fn ship_death_ends_game() {
        let mut game = make_game();
        game.ship.health = 1;
        game.rockets.push(Rocket {
            x: game.ship.x + 1,
            y: game.ship.y + 1,
            friendly: false,
            alive: true,
        });
        game.check_collisions();
        game.check_win_condition();
        assert!(game.is_finished());
        assert!(!game.humans_won());
    }

    #[test]
    fn all_aliens_dead_humans_win() {
        let mut game = make_game();
        for alien in game.aliens.iter_mut() {
            alien.alive = false;
        }
        game.check_win_condition();
        assert!(game.is_finished());
        assert!(game.humans_won());
    }

    #[test]
    fn chat_move_left() {
        let mut game = make_game();
        let x_before = game.ship.x;
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("left".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.ship.x, x_before - 1);
    }

    #[test]
    fn chat_shoot_fires_rocket() {
        let mut game = make_game();
        game.handle_input(GameInput {
            x: 0,
            y: 0,
            kind: InputKind::Chat("shoot".into()),
            player_id: "p1".into(),
        });
        assert_eq!(game.shoot_queue.len(), 1);
    }

    #[test]
    fn render_produces_pixels() {
        let mut game = make_game();
        game.update();
        let has_nonzero = game.frame_buffer().pixels().iter().any(|&p| p != 0);
        assert!(has_nonzero);
    }

    #[test]
    fn palette_correct_size() {
        let game = make_game();
        assert_eq!(game.palette().len(), 7);
    }

    #[test]
    fn rockets_collide_and_cancel() {
        let mut game = make_game();
        game.rockets.push(Rocket { x: 30, y: 30, friendly: true, alive: true });
        game.rockets.push(Rocket { x: 30, y: 30, friendly: false, alive: true });
        game.check_collisions();
        assert_eq!(game.rocket_count(), 0);
    }

    #[test]
    fn shield_absorbs_rocket() {
        let mut game = make_game();
        game.shields.push(Shield { x: 28, y: 40, health: 1 });
        game.rockets.push(Rocket { x: 29, y: 41, friendly: false, alive: true });
        game.check_collisions();
        assert_eq!(game.shield_count(), 0);
        assert_eq!(game.rocket_count(), 0);
    }
}
