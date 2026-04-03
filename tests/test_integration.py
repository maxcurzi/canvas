"""Integration tests for the canvas WebSocket server.

Requires the backend server to be running on localhost:8765.
Run: cargo run --manifest-path backend-rs/Cargo.toml
Then: python -m pytest tests/test_integration.py -v
"""

import asyncio
import msgpack
import zstandard
import pytest
import websockets

SERVER_URL = "ws://localhost:8765/ws"

ZSTD_COMPRESSOR = zstandard.ZstdCompressor(level=3)
ZSTD_DECOMPRESSOR = zstandard.ZstdDecompressor()


def encode_client_msg(msg: dict) -> bytes:
    packed = msgpack.packb(msg, use_bin_type=True)
    return ZSTD_COMPRESSOR.compress(packed)


def decode_server_msg(data: bytes) -> dict:
    reader = ZSTD_DECOMPRESSOR.stream_reader(data)
    decompressed = reader.read()
    reader.close()
    return msgpack.unpackb(decompressed, raw=False)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def connect():
    return await websockets.connect(SERVER_URL)


async def recv_msg(ws, timeout=5):
    data = await asyncio.wait_for(ws.recv(), timeout=timeout)
    return decode_server_msg(data)


async def drain_game_list(ws):
    """Server sends a game_list on connect; drain it."""
    msg = await recv_msg(ws)
    assert msg["type"] == "game_list"
    return msg


@pytest.mark.asyncio
async def test_health_endpoint():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8765/health") as resp:
            assert resp.status == 200
            text = await resp.text()
            assert text == "ok"


@pytest.mark.asyncio
async def test_list_games():
    async with websockets.connect(SERVER_URL) as ws:
        # Server sends game_list on connect
        decoded = await drain_game_list(ws)
        games = decoded["games"]
        assert len(games) >= 4
        game_ids = {g["id"] for g in games}
        assert "place-default" in game_ids
        assert "tetris-default" in game_ids
        assert "invaders-default" in game_ids
        assert "snake-default" in game_ids


@pytest.mark.asyncio
async def test_join_game_receives_full_frame():
    async with websockets.connect(SERVER_URL) as ws:
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "place-default"}))
        decoded = await recv_msg(ws)
        assert decoded["type"] == "full_frame"
        assert decoded["width"] == 256
        assert decoded["height"] == 256
        assert len(decoded["palette"]) > 0
        assert len(decoded["pixels"]) == 256 * 256


@pytest.mark.asyncio
async def test_join_tetris_receives_frame():
    async with websockets.connect(SERVER_URL) as ws:
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "tetris-default"}))
        decoded = await recv_msg(ws)
        assert decoded["type"] == "full_frame"
        assert decoded["width"] == 64
        assert decoded["height"] == 64


@pytest.mark.asyncio
async def test_click_on_place():
    async with websockets.connect(SERVER_URL) as ws:
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "place-default"}))
        await recv_msg(ws)  # full_frame

        await ws.send(encode_client_msg({"type": "click", "x": 10, "y": 10}))
        # Wait for next broadcast (could be full_frame or delta)
        decoded = await recv_msg(ws, timeout=10)
        assert decoded["type"] in ("full_frame", "delta")


@pytest.mark.asyncio
async def test_chat_message_broadcast():
    async with websockets.connect(SERVER_URL) as ws1, \
               websockets.connect(SERVER_URL) as ws2:
        await drain_game_list(ws1)
        await drain_game_list(ws2)
        await ws1.send(encode_client_msg({"type": "join_game", "game_id": "place-default"}))
        await ws2.send(encode_client_msg({"type": "join_game", "game_id": "place-default"}))
        await recv_msg(ws1)  # full_frame
        await recv_msg(ws2)  # full_frame

        await ws1.send(encode_client_msg({"type": "chat", "text": "hello world"}))

        deadline = asyncio.get_event_loop().time() + 5
        found_chat = False
        while asyncio.get_event_loop().time() < deadline:
            try:
                decoded = await recv_msg(ws2, timeout=2)
                if decoded["type"] == "chat":
                    assert decoded["text"] == "hello world"
                    assert "player_id" in decoded
                    assert "timestamp_ms" in decoded
                    found_chat = True
                    break
            except asyncio.TimeoutError:
                break
        assert found_chat, "Did not receive chat message on ws2"


@pytest.mark.asyncio
async def test_leave_and_rejoin():
    async with websockets.connect(SERVER_URL) as ws:
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "tetris-default"}))
        decoded = await recv_msg(ws)
        assert decoded["type"] == "full_frame"

        await ws.send(encode_client_msg({"type": "leave_game"}))
        await asyncio.sleep(0.2)

        await ws.send(encode_client_msg({"type": "join_game", "game_id": "snake-default"}))
        decoded = await recv_msg(ws)
        assert decoded["type"] == "full_frame"
        assert decoded["width"] == 128
        assert decoded["height"] == 128


@pytest.mark.asyncio
async def test_multiple_clients_same_game():
    clients = []
    for _ in range(5):
        ws = await websockets.connect(SERVER_URL)
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "place-default"}))
        decoded = await recv_msg(ws)
        assert decoded["type"] == "full_frame"
        clients.append(ws)

    for ws in clients:
        await ws.close()


@pytest.mark.asyncio
async def test_chat_command_to_tetris():
    async with websockets.connect(SERVER_URL) as ws:
        await drain_game_list(ws)
        await ws.send(encode_client_msg({"type": "join_game", "game_id": "tetris-default"}))
        await recv_msg(ws)  # full_frame

        await ws.send(encode_client_msg({"type": "chat", "text": "left"}))
        await ws.send(encode_client_msg({"type": "chat", "text": "rotate"}))

        decoded = await recv_msg(ws, timeout=5)
        assert decoded["type"] in ("full_frame", "delta", "chat")
