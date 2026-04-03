import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Lobby } from './Lobby'
import { useGameStore } from '../stores/game-store'

describe('Lobby', () => {
  beforeEach(() => {
    useGameStore.setState({
      connectionState: 'disconnected',
      games: [],
      currentGameId: null,
    })
  })

  it('shows connecting message when disconnected with no games', () => {
    render(<Lobby />)
    expect(screen.getByText('Connecting to server...')).toBeInTheDocument()
  })

  it('shows no games message when connected with empty list', () => {
    useGameStore.setState({ connectionState: 'connected' })
    render(<Lobby />)
    expect(screen.getByText('No games available yet.')).toBeInTheDocument()
  })

  it('renders game cards when games are available', () => {
    useGameStore.setState({
      connectionState: 'connected',
      games: [
        {
          id: 'place-1',
          name: 'Place',
          description: 'Click pixels',
          width: 256,
          height: 256,
          player_count: 5,
          thumbnail: null,
        },
      ],
    })
    render(<Lobby />)
    expect(screen.getByText('Place')).toBeInTheDocument()
    expect(screen.getByText('Click pixels')).toBeInTheDocument()
    expect(screen.getByText('5 players')).toBeInTheDocument()
  })

  it('shows connection status indicator', () => {
    useGameStore.setState({ connectionState: 'connected' })
    render(<Lobby />)
    expect(screen.getByText('● Connected')).toBeInTheDocument()
  })
})
