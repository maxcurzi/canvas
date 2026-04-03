# Architecture: pixels.today Platform

> Living architecture document. Updated as the system evolves.

## Overview

**pixels.today** is a multiplayer pixel canvas platform where many users interact on shared pixel grids in real time. The platform hosts multiple concurrent mini-canvases, each running a different game — from collaborative pixel art (Place) to classic arcade games (Tetris, Space Invaders) to novel multiplayer experiences (Snake Royale, Pixel Wars).

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       FRONTEND (SPA)                          │
│  React 19 · TypeScript · Vite · Zustand                      │
│                                                               │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐               │
│  │  Lobby   │  │  Game      │  │  Chat /    │               │
│  │  Page    │  │  Canvas    │  │  Input     │               │
│  │ (cards)  │  │ (Canvas2D) │  │  Panel     │               │
│  └──────────┘  └────────────┘  └────────────┘               │
│       ↕ Binary WebSocket (MessagePack + zstd)                 │
└──────────────────────────────────────────────────────────────┘
                          ↕
┌──────────────────────────────────────────────────────────────┐
│                RUST BACKEND (Tokio + Axum)                    │
│                                                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ WS Gateway   │  │ Game Registry   │  │ Rate Limiter   │  │
│  │ (per-client) │  │ (room manager)  │  │ (per-client)   │  │
│  └──────┬───────┘  └───────┬─────────┘  └────────────────┘  │
│         │                  │                                  │
│  ┌──────▼──────────────────▼──────────┐                      │
│  │       Game Room (per game)         │ ← game loop thread   │
│  │  ┌─────────────┐  ┌─────────────┐ │                      │
│  │  │ Game Engine │  │ FrameBuffer │ │                      │
│  │  │ (Game trait)│  │ (tile dirty │ │                      │
│  │  │             │  │  tracking)  │ │                      │
│  │  └─────────────┘  └─────────────┘ │                      │
│  └────────────────────────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Rust Backend (replacing Python)

**Decision**: Rewrite the backend in Rust using Tokio + Axum.

**Rationale**: The original Python asyncio backend serializes full JSON state every frame — O(W×H×clients) bandwidth. Rust's zero-cost abstractions, native concurrency (Tokio), and binary protocol handling provide 10-100× throughput improvement. The compile-time type safety also catches protocol serialization bugs early.

**Trade-off**: Higher development cost per feature, steeper learning curve. Acceptable because this is a performance-critical real-time system where the core loop (serialize → compress → broadcast) dominates server CPU.

### 2. Binary Protocol (MessagePack + zstd)

**Decision**: Replace JSON full-state broadcast with binary MessagePack messages and zstd-compressed pixel data.

**Rationale**: A 256×256 canvas in JSON is ~200KB per frame. The same data palette-indexed (1 byte/pixel) and zstd-compressed is ~5-20KB. MessagePack adds structured message framing with minimal overhead vs raw binary.

**Wire format**:
```
ServerMessage (tagged enum, MessagePack):
  FullFrame  { width, height, palette, pixels (zstd), frame_number }
  Delta      { tiles: [{x, y, pixels (raw)}], frame_number }
  GameList   { games: [{id, name, description, width, height, player_count}] }
  Chat       { player_id, message }
  Error      { message }

ClientMessage:
  Click      { x, y }
  JoinGame   { game_id }
  LeaveGame  {}
  ListGames  {}
  Chat       { message }
```

### 3. Palette-Indexed Pixels

**Decision**: Use 256-color palettes with 1 byte per pixel, not RGBA.

**Rationale**: 75% bandwidth reduction vs RGBA. Pixel art games don't need millions of colors. Each game defines its own palette (e.g., Place uses 8 colors, Tetris uses ~16). The palette is sent once with FullFrame; deltas reference palette indices.

### 4. Tile-Based Dirty Tracking

**Decision**: Divide the canvas into 16×16 tiles. Track which tiles changed since last broadcast. Send only dirty tiles as deltas.

**Rationale**: Per-pixel tracking has too much bookkeeping overhead. Tile-based is the sweet spot: simple to implement, good compression (spatial locality within tiles), and the overhead of sending a few extra unchanged pixels per tile is negligible vs. the protocol overhead of per-pixel addressing.

**Keyframe strategy**: Full frame every 60 ticks (or on client join). Deltas between keyframes. Clients that miss deltas self-heal at the next keyframe.

### 5. Vite + React 19 (replacing CRA)

**Decision**: Replace Create React App with Vite + React 19 + TypeScript.

**Rationale**: CRA is unmaintained (the project used `react-scripts ^0.0.0` — a placeholder version). Vite provides faster dev builds, native TypeScript support, and a healthy ecosystem. React 19 is current. TypeScript catches bugs that the original JS codebase couldn't.

### 6. Zustand for State Management

**Decision**: Use Zustand instead of React useState/useReducer for game state.

**Rationale**: High-frequency WebSocket updates (10-30 FPS) would cause re-render storms with useState. Zustand allows updating the pixel buffer without re-rendering the React tree. Only the Canvas component subscribes to pixel data; the rest of the UI subscribes to metadata (game list, connection status).

### 7. Game Trait Architecture

**Decision**: All games implement a common `Game` trait with a fixed interface.

```rust
pub trait Game: Send + Sync {
    fn metadata(&self) -> GameMetadata;
    fn width(&self) -> u16;
    fn height(&self) -> u16;
    fn update(&mut self);
    fn handle_input(&mut self, input: GameInput);
    fn frame_buffer(&self) -> &FrameBuffer;
    fn is_finished(&self) -> bool;
    fn player_count(&self) -> u32;
    fn palette(&self) -> Vec<Color>;
}
```

**Rationale**: Uniform interface lets the server manage any game identically — same room abstraction, same broadcast logic, same protocol. New games are added by implementing the trait. Future: the trait is WASM-compatible for dynamic game loading.

### 8. Game Room Pattern

**Decision**: Each active game runs in its own `GameRoom` — an async task with a game loop, broadcast channel, and client list.

**Rationale**: Isolates games from each other (a buggy game can't crash the server). The broadcast channel (Tokio `broadcast::Sender`) handles fan-out to all clients in the room efficiently. The game loop ticks at the game's configured FPS.

### 9. No Redis Initially

**Decision**: Single-server architecture. No Redis or external pub/sub.

**Rationale**: For v1, a single Rust server can handle thousands of concurrent WebSocket connections and dozens of game rooms. The architecture is designed so that Redis pub/sub can be added later for horizontal scaling (multiple server instances sharing game state), but the complexity isn't justified yet.

## Crate Structure

```
backend-rs/
├── Cargo.toml              # Workspace root
├── src/
│   ├── main.rs             # Axum server entry point
│   ├── game_room.rs        # Game room (loop + broadcast)
│   └── registry.rs         # Game registry (room manager)
└── crates/
    ├── game-engine/        # Core: Game trait, FrameBuffer, Color
    ├── protocol/           # Wire protocol: messages, codec (msgpack+zstd)
    └── games/
        ├── place/          # r/Place-style pixel art
        ├── tetris/         # Multiplayer Tetris
        ├── invaders/       # Space Invaders
        └── snake/          # Snake Royale
```

## Frontend Structure

```
frontend-new/
├── src/
│   ├── App.tsx             # Root: WS connection, routing
│   ├── lib/
│   │   ├── protocol.ts     # Binary protocol encode/decode
│   │   └── ws-client.ts    # WebSocket client with auto-reconnect
│   ├── stores/
│   │   └── game-store.ts   # Zustand store for game state
│   ├── components/
│   │   ├── GameCanvas.tsx   # Canvas renderer with zoom
│   │   └── GameCard.tsx     # Lobby game card
│   └── pages/
│       ├── Lobby.tsx        # Game grid overview
│       └── GameView.tsx     # Full game view
├── vite.config.ts
├── vitest.config.ts
└── tsconfig.json
```

## Scalability Analysis

| Metric | Target | How |
|--------|--------|-----|
| Canvas size | Up to 1024×1024 | Palette indexing (1B/px), tile deltas, zstd |
| Clients per room | 1000+ | Tokio broadcast channel, binary protocol |
| Total rooms | 50+ | Each room is a lightweight async task |
| Bandwidth per client | <50 KB/s @ 10 FPS | Delta compression, only dirty tiles sent |
| Input latency | <50ms server-side | Lock-free where possible, efficient routing |

## Testing Strategy

- **Rust unit tests**: Every crate. Run: `cargo test --workspace`
- **Frontend unit tests**: Vitest + Testing Library. Run: `cd frontend-new && npm test`
- **Integration tests**: Multi-client WebSocket scenarios (planned)
- **Load tests**: Criterion benchmarks + concurrent client stress test (planned)
- **E2E tests**: Playwright (planned)

## Future Considerations

1. **WASM Game Plugins**: The `Game` trait is designed to be WASM-compatible. Future versions could load games dynamically as WASM modules.
2. **Horizontal Scaling**: Add Redis pub/sub between server instances for shared game state.
3. **Persistence**: SQLite or PostgreSQL for game state snapshots, replay history.
4. **Internet Archive Integration**: Embed classic games via iframe initially; explore libretro WASM cores for pixel-level integration later.
5. **Auth**: Simple JWT-based auth. Anonymous play with rate limiting; registered users get higher limits.
