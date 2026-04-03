import { describe, it, expect } from 'vitest'
import { encodeClientMessage } from './protocol'

describe('protocol', () => {
  it('encodes click message as msgpack binary', () => {
    const encoded = encodeClientMessage({ type: 'click', x: 10, y: 20 })
    expect(encoded).toBeInstanceOf(Uint8Array)
    expect(encoded.length).toBeGreaterThan(0)
  })

  it('encodes join_game message', () => {
    const encoded = encodeClientMessage({ type: 'join_game', game_id: 'test-room' })
    expect(encoded).toBeInstanceOf(Uint8Array)
    expect(encoded.length).toBeGreaterThan(0)
  })

  it('encodes leave_game message', () => {
    const encoded = encodeClientMessage({ type: 'leave_game' })
    expect(encoded).toBeInstanceOf(Uint8Array)
  })

  it('encodes list_games message', () => {
    const encoded = encodeClientMessage({ type: 'list_games' })
    expect(encoded).toBeInstanceOf(Uint8Array)
  })

  it('encodes chat message', () => {
    const encoded = encodeClientMessage({ type: 'chat', text: 'hello world' })
    expect(encoded).toBeInstanceOf(Uint8Array)
  })
})
