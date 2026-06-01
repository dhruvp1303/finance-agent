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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit()
  }

  // Color per agent
  const agentColor = (agent) => {
    const colors = {
      'Orchestrator': '#9b7fe8',
      'Research Agent': '#4a9eff',
      'Financial Agent': '#2ecc8a',
      'Research Tool': '#4a9eff',
      'Financial Tool': '#2ecc8a',
      'System': '#7a8394',
    }
    return colors[agent] || '#c8cdd8'
  }

  const finalAnswer = messages.find((m) => m.type === 'final_answer')

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">ARBOR<span>.</span>RESEARCH</div>
        <div className="status">
          {isRunning ? (
            <><span className="dot live"></span>RUNNING</>
          ) : (
            <><span className="dot idle"></span>IDLE</>
          )}
        </div>
      </header>

      <div className="input-row">
        <span className="prompt">›</span>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a financial research question..."
          disabled={isRunning}
        />
        <button onClick={handleSubmit} disabled={isRunning || !question}>
          {isRunning ? 'RUNNING' : 'RUN'}
        </button>
      </div>

      <div className="main">
        <section className="feed-panel">
          <div className="panel-header">
            <span className="live-dot"></span>
            REASONING TRACE
          </div>
          <div className="feed">
            {messages.length === 0 && (
              <div className="empty">No activity. Submit a query to begin.</div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className="feed-entry" style={{ borderLeftColor: agentColor(msg.agent) }}>
                <div className="agent-label" style={{ color: agentColor(msg.agent) }}>
                  {msg.agent}
                </div>
                <div className="message-text">{msg.message}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="answer-panel">
          <div className="panel-header">ANSWER</div>
          <div className="answer">
            {finalAnswer ? (
              <div className="answer-text">{finalAnswer.message}</div>
            ) : (
              <div className="empty">Waiting for response...</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default App