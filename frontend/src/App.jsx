import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [isRunning, setIsRunning] = useState(false)

  const handleSubmit = () => {
    if (!question || isRunning) return

    setMessages([])
    setIsRunning(true)

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/research")

    ws.onopen = () => {
      ws.send(JSON.stringify({ question }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setMessages((prev) => [...prev, data])
    }

    ws.onclose = () => {
      setIsRunning(false)
    }

    ws.onerror = (err) => {
      console.error("WebSocket error:", err)
      setIsRunning(false)
    }
  }

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', padding: '20px', fontFamily: 'monospace' }}>
      <h1>Multi-Agent Investment Analyst</h1>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a financial question..."
          style={{ flex: 1, padding: '8px', fontSize: '14px' }}
          disabled={isRunning}
        />
        <button
          onClick={handleSubmit}
          disabled={isRunning || !question}
          style={{ padding: '8px 20px' }}
        >
          {isRunning ? 'Running...' : 'Run'}
        </button>
      </div>

      <div style={{ border: '1px solid #ddd', padding: '12px', minHeight: '300px', borderRadius: '4px' }}>
        {messages.length === 0 && <p style={{ color: '#888' }}>No messages yet. Ask a question to begin.</p>}
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: '8px', fontSize: '13px' }}>
            <strong>[{msg.agent}]</strong> {msg.message}
          </div>
        ))}
      </div>
    </div>
  )
}

export default App