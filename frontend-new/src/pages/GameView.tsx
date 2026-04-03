import { useGameStore } from '../stores/game-store'
import { GameCanvas } from '../components/GameCanvas'

export function GameView() {
  const currentGameId = useGameStore((s) => s.currentGameId)
  const leaveGame = useGameStore((s) => s.leaveGame)
  const width = useGameStore((s) => s.width)
  const height = useGameStore((s) => s.height)

  if (!currentGameId) return null

  return (
    <div className="game-view">
      <div className="game-view-header">
        <button className="back-button" onClick={leaveGame}>
          ← Back to Lobby
        </button>
        <span className="game-info-bar">
          {currentGameId} — {width}×{height}
        </span>
      </div>
      <div className="game-view-canvas">
        <GameCanvas />
      </div>
    </div>
  )
}
