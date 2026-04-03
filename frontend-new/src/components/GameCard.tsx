import type { GameInfo } from '../lib/protocol'

type GameCardProps = {
  game: GameInfo
  onJoin: (gameId: string) => void
}

export function GameCard({ game, onJoin }: GameCardProps) {
  return (
    <div className="game-card" onClick={() => onJoin(game.id)} role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onJoin(game.id) }}>
      <div className="game-card-preview">
        {game.thumbnail ? (
          <ThumbnailCanvas data={game.thumbnail} />
        ) : (
          <div className="game-card-no-preview">No Preview</div>
        )}
      </div>
      <div className="game-card-info">
        <h3>{game.name}</h3>
        <p>{game.description}</p>
        <div className="game-card-meta">
          <span>{game.width}×{game.height}</span>
          <span>{game.player_count} player{game.player_count !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  )
}

function ThumbnailCanvas({ data }: { data: Uint8Array | number[] }) {
  const canvasRef = (el: HTMLCanvasElement | null) => {
    if (!el) return
    const ctx = el.getContext('2d')
    if (!ctx) return
    const size = Math.floor(Math.sqrt(Array.isArray(data) ? data.length : data.length))
    if (size === 0) return
    el.width = size
    el.height = size
    const imageData = ctx.createImageData(size, size)
    const pixels = Array.isArray(data) ? data : Array.from(data)
    for (let i = 0; i < pixels.length; i++) {
      const v = pixels[i]
      imageData.data[i * 4] = v
      imageData.data[i * 4 + 1] = v
      imageData.data[i * 4 + 2] = v
      imageData.data[i * 4 + 3] = 255
    }
    ctx.putImageData(imageData, 0, 0)
  }

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', imageRendering: 'pixelated' }}
    />
  )
}
