import { useGameStore } from '../stores/game-store'
import { GameCard } from '../components/GameCard'

export function Lobby() {
  const games = useGameStore((s) => s.games)
  const joinGame = useGameStore((s) => s.joinGame)
  const connectionState = useGameStore((s) => s.connectionState)

  return (
    <div className="lobby">
      <header className="lobby-header">
        <h1>🎮 Pixel Games</h1>
        <p className="lobby-subtitle">
          Pick a game to join. Play together with other players in real-time.
        </p>
        <div className="connection-status" data-state={connectionState}>
          {connectionState === 'connected' ? '● Connected' :
           connectionState === 'connecting' ? '◌ Connecting...' :
           '○ Disconnected'}
        </div>
      </header>

      {games.length === 0 ? (
        <div className="lobby-empty">
          {connectionState === 'connected'
            ? 'No games available yet.'
            : 'Connecting to server...'}
        </div>
      ) : (
        <div className="game-grid">
          {games.map((game) => (
            <GameCard key={game.id} game={game} onJoin={joinGame} />
          ))}
        </div>
      )}
    </div>
  )
}
