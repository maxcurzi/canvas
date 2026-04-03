import { useEffect } from 'react'
import { useGameStore } from './stores/game-store'
import { Lobby } from './pages/Lobby'
import { GameView } from './pages/GameView'
import './App.css'

const WS_URL = import.meta.env.VITE_WS_URL ?? `ws://${window.location.hostname}:8765/ws`

function App() {
  const connect = useGameStore((s) => s.connect)
  const currentGameId = useGameStore((s) => s.currentGameId)

  useEffect(() => {
    connect(WS_URL)
  }, [connect])

  return (
    <div className="app">
      {currentGameId ? <GameView /> : <Lobby />}
    </div>
  )
}

export default App
