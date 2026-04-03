pub mod game;
pub mod frame_buffer;
pub mod color;

pub use game::{Game, GameInput, GameMetadata, InputKind};
pub use frame_buffer::FrameBuffer;
pub use color::Color;
