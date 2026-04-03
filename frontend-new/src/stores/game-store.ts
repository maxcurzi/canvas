import { create } from 'zustand'
import type { GameInfo, Color, ServerMessage, ChatMessage } from '../lib/protocol'
import { WsClient, type ConnectionState } from '../lib/ws-client'

const TILE_SIZE = 16

type GameState = {
  // Connection
  connectionState: ConnectionState
  client: WsClient | null

  // Lobby
  games: GameInfo[]

  // Current game
  currentGameId: string | null
  width: number
  height: number
  palette: Color[]
  pixels: Uint8Array

  // Chat
  chatMessages: ChatMessage[]

  // Actions
  connect: (url: string) => void
  disconnect: () => void
  joinGame: (gameId: string) => void
  leaveGame: () => void
  click: (x: number, y: number) => void
  sendChat: (text: string) => void
  requestGameList: () => void
}

export const useGameStore = create<GameState>((set, get) => ({
  connectionState: 'disconnected',
  client: null,
  games: [],
  currentGameId: null,
  width: 0,
  height: 0,
  palette: [],
  pixels: new Uint8Array(0),
  chatMessages: [],

  connect: (url: string) => {
    const existing = get().client
    if (existing) existing.disconnect()

    const client = new WsClient({
      url,
      onMessage: (msg: ServerMessage) => handleServerMessage(msg, set, get),
      onStateChange: (state: ConnectionState) => set({ connectionState: state }),
    })
    set({ client })
    client.connect()
  },

  disconnect: () => {
    get().client?.disconnect()
    set({ client: null, connectionState: 'disconnected' })
  },

  joinGame: (gameId: string) => {
    get().client?.send({ type: 'join_game', game_id: gameId })
    set({ currentGameId: gameId })
  },

  leaveGame: () => {
    get().client?.send({ type: 'leave_game' })
    set({
      currentGameId: null,
      width: 0,
      height: 0,
      palette: [],
      pixels: new Uint8Array(0),
      chatMessages: [],
    })
  },

  click: (x: number, y: number) => {
    get().client?.send({ type: 'click', x, y })
  },

  sendChat: (text: string) => {
    get().client?.send({ type: 'chat', text })
  },

  requestGameList: () => {
    get().client?.send({ type: 'list_games' })
  },
}))

function handleServerMessage(
  msg: ServerMessage,
  set: (partial: Partial<GameState>) => void,
  get: () => GameState,
): void {
  switch (msg.type) {
    case 'full_frame': {
      const pixelData = msg.pixels instanceof Uint8Array
        ? msg.pixels
        : new Uint8Array(msg.pixels)
      set({
        width: msg.width,
        height: msg.height,
        palette: msg.palette,
        pixels: pixelData,
      })
      break
    }
    case 'delta': {
      const state = get()
      if (state.width === 0) break
      const newPixels = new Uint8Array(state.pixels)
      for (const tile of msg.tiles) {
        const tileData = tile.data instanceof Uint8Array ? tile.data : new Uint8Array(tile.data)
        const startX = tile.tile_x * TILE_SIZE
        const startY = tile.tile_y * TILE_SIZE
        const tileW = Math.min(TILE_SIZE, state.width - startX)
        const tileH = Math.min(TILE_SIZE, state.height - startY)
        for (let row = 0; row < tileH; row++) {
          const destOffset = (startY + row) * state.width + startX
          const srcOffset = row * tileW
          newPixels.set(tileData.subarray(srcOffset, srcOffset + tileW), destOffset)
        }
      }
      set({ pixels: newPixels })
      break
    }
    case 'game_list': {
      set({ games: msg.games })
      break
    }
    case 'chat': {
      const state = get()
      set({ chatMessages: [...state.chatMessages.slice(-99), msg] })
      break
    }
    case 'error': {
      console.error('Server error:', msg.message)
      break
    }
  }
}
