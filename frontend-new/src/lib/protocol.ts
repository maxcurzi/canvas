import { decode, encode } from '@msgpack/msgpack'
import { decompress } from 'fzstd'

export type Color = { r: number; g: number; b: number }

export type FullFrameMessage = {
  type: 'full_frame'
  width: number
  height: number
  palette: Color[]
  pixels: Uint8Array | number[]
}

export type TileDelta = {
  tile_x: number
  tile_y: number
  data: Uint8Array | number[]
}

export type DeltaMessage = {
  type: 'delta'
  tiles: TileDelta[]
}

export type GameInfo = {
  id: string
  name: string
  description: string
  width: number
  height: number
  player_count: number
  thumbnail: Uint8Array | null
}

export type GameListMessage = {
  type: 'game_list'
  games: GameInfo[]
}

export type ChatMessage = {
  type: 'chat'
  player_id: string
  text: string
  timestamp_ms: number
}

export type ErrorMessage = {
  type: 'error'
  message: string
}

export type ServerMessage =
  | FullFrameMessage
  | DeltaMessage
  | GameListMessage
  | ChatMessage
  | ErrorMessage

export type ClientMessage =
  | { type: 'click'; x: number; y: number }
  | { type: 'join_game'; game_id: string }
  | { type: 'leave_game' }
  | { type: 'list_games' }
  | { type: 'chat'; text: string }

export function encodeClientMessage(msg: ClientMessage): Uint8Array {
  return encode(msg) as Uint8Array
}

export function decodeServerMessage(data: ArrayBuffer): ServerMessage {
  const decompressed = decompress(new Uint8Array(data))
  return decode(decompressed) as ServerMessage
}
