use canvas_game_engine::Color;
use serde::{Deserialize, Serialize};

// --- Server -> Client messages ---

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ServerMessage {
    #[serde(rename = "full_frame")]
    FullFrame(FullFrameMessage),

    #[serde(rename = "delta")]
    Delta(DeltaMessage),

    #[serde(rename = "game_list")]
    GameList(GameListMessage),

    #[serde(rename = "chat")]
    Chat(ChatMessage),

    #[serde(rename = "error")]
    Error(ErrorMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FullFrameMessage {
    pub width: u16,
    pub height: u16,
    pub palette: Vec<Color>,
    pub pixels: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TileDeltaMsg {
    pub tile_x: u16,
    pub tile_y: u16,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeltaMessage {
    pub tiles: Vec<TileDeltaMsg>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameInfo {
    pub id: String,
    pub name: String,
    pub description: String,
    pub width: u16,
    pub height: u16,
    pub player_count: u32,
    pub thumbnail: Option<Vec<u8>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameListMessage {
    pub games: Vec<GameInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub player_id: String,
    pub text: String,
    pub timestamp_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorMessage {
    pub message: String,
}

// --- Client -> Server messages ---

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ClientMessage {
    #[serde(rename = "click")]
    Click(ClickMessage),

    #[serde(rename = "join_game")]
    JoinGame(JoinGameMessage),

    #[serde(rename = "leave_game")]
    LeaveGame,

    #[serde(rename = "list_games")]
    ListGames,

    #[serde(rename = "chat")]
    Chat(ClientChatMessage),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClickMessage {
    pub x: u16,
    pub y: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JoinGameMessage {
    pub game_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientChatMessage {
    pub text: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn client_click_roundtrips_via_msgpack() {
        let msg = ClientMessage::Click(ClickMessage { x: 10, y: 20 });
        let bytes = rmp_serde::to_vec(&msg).unwrap();
        let decoded: ClientMessage = rmp_serde::from_slice(&bytes).unwrap();
        match decoded {
            ClientMessage::Click(click) => {
                assert_eq!(click.x, 10);
                assert_eq!(click.y, 20);
            }
            _ => panic!("Expected Click"),
        }
    }

    #[test]
    fn server_full_frame_roundtrips() {
        let msg = ServerMessage::FullFrame(FullFrameMessage {
            width: 64,
            height: 64,
            palette: vec![Color::BLACK, Color::WHITE],
            pixels: vec![0; 64 * 64],
        });
        let bytes = rmp_serde::to_vec(&msg).unwrap();
        let decoded: ServerMessage = rmp_serde::from_slice(&bytes).unwrap();
        match decoded {
            ServerMessage::FullFrame(frame) => {
                assert_eq!(frame.width, 64);
                assert_eq!(frame.height, 64);
                assert_eq!(frame.pixels.len(), 64 * 64);
            }
            _ => panic!("Expected FullFrame"),
        }
    }

    #[test]
    fn server_delta_roundtrips() {
        let msg = ServerMessage::Delta(DeltaMessage {
            tiles: vec![TileDeltaMsg {
                tile_x: 0,
                tile_y: 0,
                data: vec![1, 2, 3],
            }],
        });
        let bytes = rmp_serde::to_vec(&msg).unwrap();
        let decoded: ServerMessage = rmp_serde::from_slice(&bytes).unwrap();
        match decoded {
            ServerMessage::Delta(delta) => {
                assert_eq!(delta.tiles.len(), 1);
                assert_eq!(delta.tiles[0].data, vec![1, 2, 3]);
            }
            _ => panic!("Expected Delta"),
        }
    }

    #[test]
    fn game_list_roundtrips() {
        let msg = ServerMessage::GameList(GameListMessage {
            games: vec![GameInfo {
                id: "abc".into(),
                name: "Test".into(),
                description: "A test".into(),
                width: 64,
                height: 64,
                player_count: 5,
                thumbnail: None,
            }],
        });
        let bytes = rmp_serde::to_vec(&msg).unwrap();
        let decoded: ServerMessage = rmp_serde::from_slice(&bytes).unwrap();
        match decoded {
            ServerMessage::GameList(list) => {
                assert_eq!(list.games.len(), 1);
                assert_eq!(list.games[0].name, "Test");
            }
            _ => panic!("Expected GameList"),
        }
    }

    #[test]
    fn join_game_roundtrips() {
        let msg = ClientMessage::JoinGame(JoinGameMessage {
            game_id: "room1".into(),
        });
        let bytes = rmp_serde::to_vec(&msg).unwrap();
        let decoded: ClientMessage = rmp_serde::from_slice(&bytes).unwrap();
        match decoded {
            ClientMessage::JoinGame(join) => assert_eq!(join.game_id, "room1"),
            _ => panic!("Expected JoinGame"),
        }
    }
}
