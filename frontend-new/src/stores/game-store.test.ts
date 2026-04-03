import { describe, it, expect, beforeEach } from 'vitest'
import { useGameStore } from './game-store'

describe('game-store', () => {
  beforeEach(() => {
    useGameStore.setState({
      connectionState: 'disconnected',
      client: null,
      games: [],
      currentGameId: null,
      width: 0,
      height: 0,
      palette: [],
      pixels: new Uint8Array(0),
    })
  })

  it('starts with disconnected state', () => {
    const state = useGameStore.getState()
    expect(state.connectionState).toBe('disconnected')
    expect(state.games).toEqual([])
    expect(state.currentGameId).toBeNull()
  })

  it('sets currentGameId on joinGame', () => {
    useGameStore.getState().joinGame('test-room')
    expect(useGameStore.getState().currentGameId).toBe('test-room')
  })

  it('clears game state on leaveGame', () => {
    useGameStore.setState({
      currentGameId: 'test-room',
      width: 64,
      height: 64,
      pixels: new Uint8Array(64 * 64),
    })
    useGameStore.getState().leaveGame()
    const state = useGameStore.getState()
    expect(state.currentGameId).toBeNull()
    expect(state.width).toBe(0)
    expect(state.height).toBe(0)
    expect(state.pixels.length).toBe(0)
  })
})
