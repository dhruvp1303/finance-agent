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

const ws = new WebSocket("ws://18.118.132.229:8001/ws/research")
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

  const agentColor = (agent) => {
    const colors = {
      'Orchestrator': '#6c5ce7',
      'Research Agent': '#0ea5e9',
      'Financial Agent': '#10b981',
      'Research Tool': '#0ea5e9',
      'Financial Tool': '#10b981',
      'System': '#7a8394',
    }
    return colors[agent] || '#1a1d29'
  }

  const AgentIcon = ({ agent }) => {
    const color = agentColor(agent)
    const iconStyle = { width: 14, height: 14, color }

    if (agent === 'Orchestrator') {
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <circle cx="5" cy="6" r="2"/>
          <circle cx="19" cy="6" r="2"/>
          <circle cx="5" cy="18" r="2"/>
          <circle cx="19" cy="18" r="2"/>
        </svg>
      )
    }
    if (agent === 'Research Agent') {
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      )
    }
    if (agent === 'Financial Agent') {
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="1" x2="12" y2="23"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      )
    }
    if (agent === 'Research Tool' || agent === 'Financial Tool') {
      return (
        <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
        </svg>
      )
    }
    // System
    return (
      <svg style={iconStyle} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>
    )
  }

  const finalAnswer = messages.find((m) => m.type === 'final_answer')

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">
          <span className="logo-text">Multi-Agent Investment Analyst</span>
        </div>
        <div className={`status ${isRunning ? 'running' : ''}`}>
          {isRunning ? 'RUNNING' : 'IDLE'}
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
          <div className="panel-header">REASONING TRACE</div>
          <div className="feed">
            {messages.length === 0 && (
              <div className="empty">No activity. Submit a query to begin.</div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className="feed-entry">
                <div className="agent-label" style={{ color: agentColor(msg.agent) }}>
                  <AgentIcon agent={msg.agent} />
                  <span>{msg.agent}</span>
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