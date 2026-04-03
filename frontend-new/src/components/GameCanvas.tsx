import { useRef, useEffect, useCallback, useState } from 'react'
import { useGameStore } from '../stores/game-store'
import type { Color } from '../lib/protocol'

function paletteToRgba(palette: Color[]): Uint8ClampedArray {
  const rgba = new Uint8ClampedArray(256 * 4)
  for (let i = 0; i < palette.length && i < 256; i++) {
    rgba[i * 4] = palette[i].r
    rgba[i * 4 + 1] = palette[i].g
    rgba[i * 4 + 2] = palette[i].b
    rgba[i * 4 + 3] = 255
  }
  return rgba
}

export function GameCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [zoom, setZoom] = useState(4)
  const width = useGameStore((s) => s.width)
  const height = useGameStore((s) => s.height)
  const pixels = useGameStore((s) => s.pixels)
  const palette = useGameStore((s) => s.palette)
  const click = useGameStore((s) => s.click)
  const lastClickRef = useRef(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || width === 0 || height === 0 || pixels.length === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rgbaPalette = paletteToRgba(palette)
    const imageData = ctx.createImageData(width, height)
    const data = imageData.data

    for (let i = 0; i < pixels.length; i++) {
      const colorIdx = pixels[i]
      data[i * 4] = rgbaPalette[colorIdx * 4]
      data[i * 4 + 1] = rgbaPalette[colorIdx * 4 + 1]
      data[i * 4 + 2] = rgbaPalette[colorIdx * 4 + 2]
      data[i * 4 + 3] = 255
    }

    canvas.width = width
    canvas.height = height
    ctx.putImageData(imageData, 0, 0)
  }, [pixels, width, height, palette])

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const now = Date.now()
      if (now - lastClickRef.current < 100) return
      lastClickRef.current = now

      const canvas = canvasRef.current
      if (!canvas) return
      const rect = canvas.getBoundingClientRect()
      const scaleX = width / rect.width
      const scaleY = height / rect.height
      const x = Math.floor((e.clientX - rect.left) * scaleX)
      const y = Math.floor((e.clientY - rect.top) * scaleY)
      if (x >= 0 && x < width && y >= 0 && y < height) {
        click(x, y)
      }
    },
    [width, height, click],
  )

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    setZoom((z) => Math.max(1, Math.min(40, z + (e.deltaY > 0 ? -1 : 1))))
  }, [])

  if (width === 0 || height === 0) {
    return <div className="game-canvas-placeholder">Waiting for game data...</div>
  }

  return (
    <div className="game-canvas-container" onWheel={handleWheel}>
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        style={{
          width: width * zoom,
          height: height * zoom,
          imageRendering: 'pixelated',
          cursor: 'crosshair',
        }}
      />
      <div className="zoom-indicator">Zoom: {zoom}x</div>
    </div>
  )
}
