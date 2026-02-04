import { useState, useRef, useEffect } from 'react'
import './App.css'
import Login from './Login.jsx'

const AUTH_TOKEN_KEY = 'muppy_token'

// Iconos SVG inline para no necesitar dependencias extra
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
)

const BotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2"></rect>
    <circle cx="12" cy="5" r="2"></circle>
    <path d="M12 7v4"></path>
    <line x1="8" y1="16" x2="8" y2="16"></line>
    <line x1="16" y1="16" x2="16" y2="16"></line>
  </svg>
)

const UserIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
)

const NewChatIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
)

// Asegurar URL absoluta (evita 404 cuando en Vercel falta https://)
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_URL = rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')
  ? rawApiUrl
  : `https://${rawApiUrl.replace(/^\/*/, '')}`

// Header para ngrok (plan gratuito): evita la página intersticial y deja pasar la petición al backend
function getApiHeaders(token) {
  const headers = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

function App() {
  const [authRequired, setAuthRequired] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY))
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [activeAgent, setActiveAgent] = useState('triage_agent')
  const [connectionStatus, setConnectionStatus] = useState('checking')
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const bootstrappedSessionsRef = useRef(new Set())

  const API_HEADERS = getApiHeaders(token)

  // Saber si el backend exige login
  useEffect(() => {
    let cancelled = false
    fetch(`${API_URL}/auth/required`, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      .then((r) => r.json())
      .then((data) => { if (!cancelled) setAuthRequired(data.login_required === true) })
      .catch(() => { if (!cancelled) setAuthRequired(false) })
    return () => { cancelled = true }
  }, [])

  // Auto-scroll al último mensaje (siempre mismo número de hooks)
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Verificar conexión con el backend
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, { headers: API_HEADERS })
        if (response.status === 401) {
          handleUnauthorized()
          return
        }
        if (response.ok) {
          setConnectionStatus('connected')
        } else {
          setConnectionStatus('error')
        }
      } catch (error) {
        setConnectionStatus('error')
      }
    }
    checkConnection()
    const interval = setInterval(checkConnection, 30000)
    return () => clearInterval(interval)
  }, [token])

  // Auto-inicio: el triage “empieza a escribir” al abrir chat o al reiniciar
  useEffect(() => {
    if (connectionStatus !== 'connected') return
    if (bootstrappedSessionsRef.current.has(sessionId)) return

    bootstrappedSessionsRef.current.add(sessionId)

    const autoStart = async () => {
      if (isLoading) return
      setIsLoading(true)
      try {
        const response = await fetch(`${API_URL}/invoke`, {
          method: 'POST',
          headers: API_HEADERS,
          body: JSON.stringify({
            input: 'Hola',
            session_id: sessionId,
            metadata: {
              source: 'web_frontend',
              auto_start: true,
            },
          }),
        })

        if (response.status === 401) {
          handleUnauthorized()
          return
        }
        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}))
          const detail = Array.isArray(errBody.detail) ? errBody.detail.map(d => d.msg || JSON.stringify(d)).join(', ') : (errBody.detail || response.statusText)
          throw new Error(detail)
        }
        const data = await response.json()

        if (data.structured_data?.active_agent_key) {
          setActiveAgent(data.structured_data.active_agent_key)
        } else {
          setActiveAgent('triage_agent')
        }

        const botMessage = {
          id: Date.now(),
          type: 'bot',
          text: data.response || 'Hola, ¿en qué puedo ayudarte?',
          timestamp: new Date(),
          agent: data.structured_data?.active_agent_key || 'triage_agent',
          cost: data.request_cost,
        }

        setMessages([botMessage])
      } catch (error) {
        if (error.message === 'Requiere autenticación' || error.message?.includes('Token')) {
          handleUnauthorized()
          return
        }
        console.error('Error:', error)
        const message = error.message || 'Error desconocido'
        setMessages([
          {
            id: Date.now(),
            type: 'bot',
            text: `❌ ${message}`,
            timestamp: new Date(),
            isError: true,
          },
        ])
      } finally {
        setIsLoading(false)
        inputRef.current?.focus()
      }
    }

    autoStart()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, connectionStatus])

  const handleLoginSuccess = (newToken) => {
    localStorage.setItem(AUTH_TOKEN_KEY, newToken)
    // Recarga para montar el chat con token y que los efectos (conexión, auto-inicio) se ejecuten
    window.location.reload()
  }

  const handleLogout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    setToken(null)
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
    setMessages([])
    setConnectionStatus('checking')
    bootstrappedSessionsRef.current.clear()
    // Recarga para mostrar la pantalla de login
    window.location.reload()
  }

  const handleUnauthorized = () => {
    handleLogout()
  }

  // Mostrar login si el backend lo exige y no hay token
  if (authRequired === true && !token) {
    return <Login key="login" onSuccess={handleLoginSuccess} />
  }

  // Cargando estado de auth (solo un instante)
  if (authRequired === null && !token) {
    return (
      <div className="app-container login-page">
        <div className="login-card">
          <p>Cargando...</p>
        </div>
      </div>
    )
  }

  // Formatear texto con markdown básico
  const formatMessage = (text) => {
    if (!text) return ''
    
    // Negrita
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Cursiva
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Saltos de línea
    formatted = formatted.replace(/\n/g, '<br/>')
    // Listas
    formatted = formatted.replace(/• /g, '• ')
    
    return formatted
  }

  // Enviar mensaje al backend
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_URL}/invoke`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify({
          input: userMessage.text,
          session_id: sessionId,
          metadata: {
            source: 'web_frontend'
          }
        })
      })

      if (response.status === 401) {
        handleUnauthorized()
        return
      }
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}))
        const detail = Array.isArray(errBody.detail) ? errBody.detail.map(d => d.msg || JSON.stringify(d)).join(', ') : (errBody.detail || response.statusText)
        throw new Error(detail)
      }

      const data = await response.json()
      
      // Actualizar agente activo si cambió
      if (data.structured_data?.active_agent_key) {
        setActiveAgent(data.structured_data.active_agent_key)
      }

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: data.response || 'Lo siento, no pude procesar tu mensaje.',
        timestamp: new Date(),
        agent: data.structured_data?.active_agent_key || activeAgent,
        cost: data.request_cost
      }

      setMessages(prev => [...prev, botMessage])

    } catch (error) {
      if (error.message === 'Requiere autenticación' || error.message?.includes('Token')) {
        handleUnauthorized()
        return
      }
      console.error('Error:', error)
      const message = error.message || 'Error desconocido'
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: `❌ ${message}`,
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  // Manejar Enter para enviar
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Nueva conversación
  const startNewChat = () => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
    setActiveAgent('triage_agent')
    setMessages([])
  }

  // Obtener nombre amigable del agente
  const getAgentName = (agentKey) => {
    const agents = {
      'triage_agent': '🎯 Asistente General',
      'quote_agent': '💰 Agente de Cotizaciones',
      'contract_agent': '📝 Agente de Contratación',
      'support_agent': '🆘 Agente de Soporte'
    }
    return agents[agentKey] || '🤖 Asistente'
  }

  return (
    <div key={token || 'chat'} className="app-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="logo-container">
            <div className="logo-icon">
              <BotIcon />
            </div>
            <div className="logo-text">
              <h1>Muppy AI</h1>
              <span className="subtitle">Asistente de Seguros Mapfre</span>
            </div>
          </div>
        </div>
        
        <div className="header-center">
          <div className={`agent-badge ${activeAgent}`}>
            {getAgentName(activeAgent)}
          </div>
        </div>

        <div className="header-right">
          <div className={`connection-status ${connectionStatus}`}>
            <span className="status-dot"></span>
            {connectionStatus === 'connected' ? 'Conectado' : 
             connectionStatus === 'checking' ? 'Verificando...' : 'Desconectado'}
          </div>
          <button className="new-chat-btn" onClick={startNewChat} title="Nueva conversación">
            <NewChatIcon />
            <span>Nueva conversación</span>
          </button>
          {authRequired && token && (
            <button type="button" className="logout-btn" onClick={handleLogout} title="Cerrar sesión">
              Cerrar sesión
            </button>
          )}
        </div>
      </header>

      {/* Messages Container */}
      <main className="messages-container">
        <div className="messages-wrapper">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.type} ${message.isError ? 'error' : ''}`}
            >
              <div className="message-avatar">
                {message.type === 'bot' ? <BotIcon /> : <UserIcon />}
              </div>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.type === 'bot' ? 'Muppy' : 'Tú'}
                  </span>
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString('es-ES', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
                <div 
                  className="message-text"
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
                />
                {message.cost && (
                  <div className="message-meta">
                    <span className="cost-badge">💰 ${message.cost.toFixed(4)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="message bot loading">
              <div className="message-avatar">
                <BotIcon />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Container */}
      <footer className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje aquí..."
            disabled={isLoading || connectionStatus === 'error'}
            rows={1}
          />
          <button 
            className="send-btn" 
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading || connectionStatus === 'error'}
          >
            <SendIcon />
          </button>
        </div>
        <div className="input-footer">
          <span className="session-id">Session: {sessionId.slice(0, 20)}...</span>
          <span className="powered-by">Powered by LangGraph & FastAPI</span>
        </div>
      </footer>
    </div>
  )
}

export default App
