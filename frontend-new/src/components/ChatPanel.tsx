import { useState, useRef, useEffect } from 'react'
import { useGameStore } from '../stores/game-store'

export function ChatPanel() {
  const chatMessages = useGameStore((s) => s.chatMessages)
  const sendChat = useGameStore((s) => s.sendChat)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    sendChat(text)
    setInput('')
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {chatMessages.map((msg, i) => (
          <div key={i} className="chat-message">
            <span className="chat-player">{msg.player_id.slice(0, 8)}</span>
            <span className="chat-text">{msg.text}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message or command..."
          maxLength={200}
        />
        <button type="submit" className="chat-send-btn">Send</button>
      </form>
    </div>
  )
}
