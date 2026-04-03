use crate::messages::{ServerMessage, ClientMessage};

pub fn encode_server_message(msg: &ServerMessage) -> Result<Vec<u8>, CodecError> {
    let msgpack_bytes = rmp_serde::to_vec_named(msg)
        .map_err(|e| CodecError::Serialize(e.to_string()))?;
    zstd::encode_all(msgpack_bytes.as_slice(), 3)
        .map_err(|e| CodecError::Compress(e.to_string()))
}

pub fn decode_server_message(data: &[u8]) -> Result<ServerMessage, CodecError> {
    let decompressed = zstd::decode_all(data)
        .map_err(|e| CodecError::Decompress(e.to_string()))?;
    rmp_serde::from_slice(&decompressed)
        .map_err(|e| CodecError::Deserialize(e.to_string()))
}

pub fn encode_client_message(msg: &ClientMessage) -> Result<Vec<u8>, CodecError> {
    let msgpack_bytes = rmp_serde::to_vec_named(msg)
        .map_err(|e| CodecError::Serialize(e.to_string()))?;
    zstd::encode_all(msgpack_bytes.as_slice(), 3)
        .map_err(|e| CodecError::Compress(e.to_string()))
}

pub fn decode_client_message(data: &[u8]) -> Result<ClientMessage, CodecError> {
    let decompressed = zstd::decode_all(data)
        .map_err(|e| CodecError::Decompress(e.to_string()))?;
    rmp_serde::from_slice(&decompressed)
        .map_err(|e| CodecError::Deserialize(e.to_string()))
}

#[derive(Debug, thiserror::Error)]
pub enum CodecError {
    #[error("Serialization failed: {0}")]
    Serialize(String),
    #[error("Deserialization failed: {0}")]
    Deserialize(String),
    #[error("Compression failed: {0}")]
    Compress(String),
    #[error("Decompression failed: {0}")]
    Decompress(String),
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::messages::*;
    use canvas_game_engine::Color;

    #[test]
    fn server_message_encode_decode_roundtrip() {
        let msg = ServerMessage::FullFrame(FullFrameMessage {
            width: 64,
            height: 64,
            palette: vec![Color::BLACK, Color::WHITE],
            pixels: vec![0; 64 * 64],
        });
        let encoded = encode_server_message(&msg).unwrap();
        let decoded = decode_server_message(&encoded).unwrap();
        match decoded {
            ServerMessage::FullFrame(frame) => {
                assert_eq!(frame.width, 64);
                assert_eq!(frame.pixels.len(), 64 * 64);
            }
            _ => panic!("Wrong message type"),
        }
    }

    #[test]
    fn client_message_encode_decode_roundtrip() {
        let msg = ClientMessage::Click(ClickMessage { x: 42, y: 99 });
        let encoded = encode_client_message(&msg).unwrap();
        let decoded = decode_client_message(&encoded).unwrap();
        match decoded {
            ClientMessage::Click(click) => {
                assert_eq!(click.x, 42);
                assert_eq!(click.y, 99);
            }
            _ => panic!("Wrong message type"),
        }
    }

    #[test]
    fn compressed_size_is_smaller_than_raw() {
        let msg = ServerMessage::FullFrame(FullFrameMessage {
            width: 256,
            height: 256,
            palette: vec![Color::BLACK],
            pixels: vec![0; 256 * 256],
        });
        let raw = rmp_serde::to_vec(&msg).unwrap();
        let compressed = encode_server_message(&msg).unwrap();
        assert!(compressed.len() < raw.len());
    }

    #[test]
    fn invalid_data_returns_error() {
        let result = decode_server_message(&[0xFF, 0xFE, 0xFD]);
        assert!(result.is_err());
    }
}
