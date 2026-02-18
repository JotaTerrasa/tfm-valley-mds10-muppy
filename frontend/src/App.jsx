import { useState, useRef, useEffect } from 'react'
import './App.css'
import Login from './Login.jsx'

const AUTH_TOKEN_KEY = 'muppy_token'
const TEMPORARILY_DISABLE_FRONTEND_LOGIN = true
const STRIPE_PAYMENT_EVENT_KEY = 'muppy_stripe_payment_event'
const STRIPE_POSTMESSAGE_TYPE = 'muppy:stripe-payment-success'
const CHAT_SNAPSHOT_KEY = 'muppy_chat_snapshot'
const SESSION_ID_KEY = 'muppy_session_id'
const ENABLE_TEST_PAYMENTS = import.meta.env.VITE_ENABLE_TEST_PAYMENTS === 'true'

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
  const [authRequired, setAuthRequired] = useState(TEMPORARILY_DISABLE_FRONTEND_LOGIN ? false : null)
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY))
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => {
    try {
      const existing = localStorage.getItem(SESSION_ID_KEY)
      if (existing) return existing
    } catch (e) {
      // ignore
    }
    const created = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    try {
      localStorage.setItem(SESSION_ID_KEY, created)
    } catch (e) {
      // ignore
    }
    return created
  })
  const [activeAgent, setActiveAgent] = useState('triage_agent')
  const [connectionStatus, setConnectionStatus] = useState('checking')
  
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const bootstrappedSessionsRef = useRef(new Set())
  const processedCheckoutSessionsRef = useRef(new Set())
  const [paymentReturnNotice, setPaymentReturnNotice] = useState('')
  const [paymentReturnError, setPaymentReturnError] = useState('')

  const [currentPath, setCurrentPath] = useState(() => window.location.pathname)
  const pathname = currentPath
  const isPaymentSuccessRoute = pathname.startsWith('/payment/success')
  const isPaymentCancelRoute = pathname.startsWith('/payment/cancel')
  const isPaymentReturnRoute = isPaymentSuccessRoute || isPaymentCancelRoute

  const restoreInputFocus = () => {
    // Esperamos al siguiente ciclo de render para asegurar que el textarea ya no esté disabled.
    window.requestAnimationFrame(() => {
      inputRef.current?.focus()
    })
  }

  const effectiveToken = TEMPORARILY_DISABLE_FRONTEND_LOGIN ? null : token
  const API_HEADERS = getApiHeaders(effectiveToken)

  useEffect(() => {
    const onPopState = () => setCurrentPath(window.location.pathname)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem(SESSION_ID_KEY, sessionId)
    } catch (e) {
      // ignore
    }
  }, [sessionId])

  const appendBotMessage = (text, agentOverride = activeAgent) => {
    if (!text) return
    const botMessage = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      type: 'bot',
      text,
      timestamp: new Date(),
      agent: agentOverride,
    }
    setMessages((prev) => [...prev, botMessage])
  }

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

  const saveChatSnapshot = () => {
    try {
      const serializableMessages = (messages || []).map((m) => ({
        ...m,
        timestamp: m?.timestamp instanceof Date ? m.timestamp.toISOString() : m?.timestamp,
      }))
      localStorage.setItem(
        CHAT_SNAPSHOT_KEY,
        JSON.stringify({
          ts: Date.now(),
          sessionId,
          activeAgent,
          messages: serializableMessages,
        }),
      )
    } catch (e) {
      // ignore
    }
  }

  const restoreChatSnapshotIfAny = () => {
    try {
      const raw = localStorage.getItem(CHAT_SNAPSHOT_KEY)
      if (!raw) return false
      const snapshot = JSON.parse(raw)
      if (!snapshot?.sessionId) return false

      const restoredMessages = Array.isArray(snapshot.messages)
        ? snapshot.messages.map((m) => ({
          ...m,
          timestamp: m?.timestamp ? new Date(m.timestamp) : new Date(),
        }))
        : []

      setSessionId(snapshot.sessionId)
      if (snapshot.activeAgent) setActiveAgent(snapshot.activeAgent)
      if (restoredMessages.length) setMessages(restoredMessages)

      localStorage.removeItem(CHAT_SNAPSHOT_KEY)
      return true
    } catch (e) {
      return false
    }
  }

  const autoConfirmCheckoutPayment = async (checkoutSessionId) => {
    if (!checkoutSessionId || processedCheckoutSessionsRef.current.has(checkoutSessionId)) return
    processedCheckoutSessionsRef.current.add(checkoutSessionId)

    try {
      let statusData = null
      for (let attempt = 0; attempt < 8; attempt += 1) {
        const statusResponse = await fetch(`${API_URL}/payments/checkout/${encodeURIComponent(checkoutSessionId)}`, {
          headers: { 'ngrok-skip-browser-warning': 'true' },
        })
        if (statusResponse.ok) {
          statusData = await statusResponse.json()
          if (statusData?.paid === true) break
        }
        await sleep(1500)
      }

      if (!statusData?.paid) {
        appendBotMessage('Estamos validando tu pago. Te confirmaremos automáticamente en unos segundos.')
        return
      }

      const targetSessionId = statusData.internal_session_id || sessionId
      if (targetSessionId && targetSessionId !== sessionId) {
        setSessionId(targetSessionId)
      }

      const response = await fetch(`${API_URL}/invoke`, {
        method: 'POST',
        headers: API_HEADERS,
        body: JSON.stringify({
          input: 'Ya he pagado',
          session_id: targetSessionId,
          metadata: {
            source: 'web_frontend',
            payment: {
              auto_confirmation: true,
              checkout_session_id: checkoutSessionId,
            },
          },
        }),
      })

      if (!response.ok) {
        appendBotMessage('Pago detectado. Estamos finalizando la confirmación en el chat.')
        return
      }

      const data = await response.json()
      if (data.structured_data?.active_agent_key) {
        setActiveAgent(data.structured_data.active_agent_key)
      }
      appendBotMessage(data.response || 'Pago confirmado correctamente.')
    } catch (error) {
      appendBotMessage('Pago detectado. Si no ves la confirmación enseguida, escribe "ya he pagado".')
    }
  }

  // Saber si el backend exige login
  useEffect(() => {
    if (TEMPORARILY_DISABLE_FRONTEND_LOGIN) {
      setAuthRequired(false)
      return
    }
    let cancelled = false
    fetch(`${API_URL}/auth/required`, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      .then((r) => r.json())
      .then((data) => { if (!cancelled) setAuthRequired(data.login_required === true) })
      .catch(() => { if (!cancelled) setAuthRequired(false) })
    return () => { cancelled = true }
  }, [])

  // Escuchar confirmación de pago desde pestaña de retorno de Stripe.
  useEffect(() => {
    if (isPaymentReturnRoute) return

    const handleStorage = (event) => {
      if (event.key !== STRIPE_PAYMENT_EVENT_KEY || !event.newValue) return
      try {
        const payload = JSON.parse(event.newValue)
        const checkoutSessionId = payload?.checkout_session_id
        if (checkoutSessionId) {
          autoConfirmCheckoutPayment(checkoutSessionId)
        }
      } catch (error) {
        // noop
      }
    }

    const handleMessage = (event) => {
      if (event.origin !== window.location.origin) return
      if (event.data?.type !== STRIPE_POSTMESSAGE_TYPE) return
      const checkoutSessionId = event.data?.checkout_session_id
      if (checkoutSessionId) {
        autoConfirmCheckoutPayment(checkoutSessionId)
      }
    }

    window.addEventListener('storage', handleStorage)
    window.addEventListener('message', handleMessage)
    return () => {
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener('message', handleMessage)
    }
  }, [isPaymentReturnRoute, sessionId, API_HEADERS])

  // Vista de retorno de Stripe (success/cancel): notifica al chat y cierra la pestaña nueva.
  useEffect(() => {
    if (!isPaymentReturnRoute) return

    const params = new URLSearchParams(window.location.search)
    const checkoutSessionId = params.get('session_id') || ''

    if (isPaymentSuccessRoute) {
      if (!checkoutSessionId) {
        setPaymentReturnError('No se recibió el identificador del pago. Puedes volver al chat.')
        return
      }

      const payload = JSON.stringify({
        checkout_session_id: checkoutSessionId,
        ts: Date.now(),
      })
      localStorage.setItem(STRIPE_PAYMENT_EVENT_KEY, payload)

      setPaymentReturnNotice('Pago completado. Volviendo al chat...')
      // El chat principal escuchará el evento por localStorage y confirmará el pago allí.
      window.setTimeout(() => {
        window.close()
      }, 400)
      return
    }

    if (isPaymentCancelRoute) {
      setPaymentReturnNotice('Pago cancelado. Puedes volver al chat cuando quieras.')
      window.setTimeout(() => {
        window.close()
      }, 500)
    }
  }, [isPaymentReturnRoute, isPaymentSuccessRoute, isPaymentCancelRoute])

  // Auto-scroll al último mensaje (siempre mismo número de hooks)
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleChatClickCapture = (e) => {
    const anchor = e.target?.closest?.('a')
    if (!anchor) return
    const href = anchor.getAttribute('href') || ''
    if (href.includes('/pay/cs_') || href.includes('checkout.stripe.com')) {
      // Abrir SIEMPRE en pestaña nueva via window.open para que luego podamos cerrarla
      // automáticamente desde /payment/success.
      e.preventDefault()
      try {
        window.open(href, '_blank', 'noopener,noreferrer')
      } catch (err) {
        // Fallback: si el navegador bloquea el popup, dejamos que el click normal ocurra.
        window.location.href = href
      }
    }
  }

  const startTestPayment = async () => {
    try {
      const response = await fetch(`${API_URL}/payments/test-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
        body: JSON.stringify({
          session_id: sessionId,
          amount_eur: 1.0,
          description: 'Pago de prueba (1 EUR)',
        }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        const detail = body?.detail || response.statusText
        appendBotMessage(`❌ No se pudo crear el pago de prueba: ${detail}`)
        return
      }
      const data = await response.json()
      const checkoutSessionId = data.checkout_session_id
      const payUrl = `${API_URL}/pay/${checkoutSessionId}`
      appendBotMessage(`Pago de prueba creado. [Abrir enlace](${payUrl})`)
      window.open(payUrl, '_blank', 'noopener,noreferrer')
    } catch (e) {
      appendBotMessage('❌ No se pudo crear el pago de prueba.')
    }
  }

  // Verificar conexión con el backend
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, { headers: API_HEADERS })
        if (response.status === 401) {
          if (!TEMPORARILY_DISABLE_FRONTEND_LOGIN) {
            clearSessionAndGoToLogin()
          } else {
            setConnectionStatus('error')
          }
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
    if (TEMPORARILY_DISABLE_FRONTEND_LOGIN || token != null) {
      checkConnection()
      const interval = setInterval(checkConnection, 30000)
      return () => clearInterval(interval)
    }
  }, [token, API_HEADERS])

  // Mensaje de bienvenida hardcodeado (sin llamada al LLM)
  useEffect(() => {
    if (connectionStatus !== 'connected') return
    if (messages.length > 0) return
    if (bootstrappedSessionsRef.current.has(sessionId)) return

    bootstrappedSessionsRef.current.add(sessionId)

    // Mensaje de bienvenida estático (sin llamada al LLM)
    const welcomeMessage = {
      id: Date.now(),
      type: 'bot',
      text: '¡Hola! Soy tu asistente de seguros Mapfre. ¿En qué puedo ayudarte hoy?',
      timestamp: new Date(),
      agent: 'triage_agent',
      cost: 0,
    }

    setMessages([welcomeMessage])
    inputRef.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, connectionStatus])

  const handleLoginSuccess = (newToken) => {
    localStorage.setItem(AUTH_TOKEN_KEY, newToken)
    window.location.reload()
  }

  const clearSessionAndGoToLogin = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    setToken(null)
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
    setMessages([])
    setConnectionStatus('checking')
    bootstrappedSessionsRef.current.clear()
  }

  const handleLogout = () => {
    clearSessionAndGoToLogin()
    window.location.reload()
  }

  const handleUnauthorized = () => {
    if (TEMPORARILY_DISABLE_FRONTEND_LOGIN) return
    clearSessionAndGoToLogin()
  }

  if (isPaymentReturnRoute) {
    return (
      <div className="app-container login-page">
        <div className="login-card">
          <h2>{isPaymentSuccessRoute ? 'Pago recibido' : 'Pago cancelado'}</h2>
          <p>{paymentReturnNotice || 'Procesando estado del pago...'}</p>
          {paymentReturnError && <p className="login-error">{paymentReturnError}</p>}
        </div>
      </div>
    )
  }

  if (authRequired === true && !token) {
    return <Login key="login" onSuccess={handleLoginSuccess} />
  }

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
  const escapeHtml = (value) => {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
  }

  const rewriteStripeUrlIfNeeded = (url) => {
    if (!url) return url
    // Preferir el redirect backend /pay/<cs_...> para evitar URLs enormes y ser más robustos.
    // (Sigue terminando en Stripe, pero es un enlace más corto y estable.)
    const match = String(url).match(/cs_(?:test|live)_[A-Za-z0-9]+/)
    if (!match) return url
    const checkoutSessionId = match[0]
    return `${API_URL}/pay/${checkoutSessionId}`
  }

  const formatMessage = (text) => {
    if (!text) return ''

    let formatted = escapeHtml(text)

    // Links markdown [texto](url)
    formatted = formatted.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, label, url) => {
      const linkLabel = label === url ? 'Abrir enlace' : label
      const href = rewriteStripeUrlIfNeeded(url)
      return `<a href="${href}" target="_blank" rel="noopener noreferrer">${linkLabel}</a>`
    })

    // URLs en texto plano
    formatted = formatted.replace(/(^|[\s(>])(https?:\/\/[^\s<)]+)/g, (_, prefix, url) => {
      const href = rewriteStripeUrlIfNeeded(url)
      return `${prefix}<a href="${href}" target="_blank" rel="noopener noreferrer">${url}</a>`
    })

    // Negrita
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
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
      restoreInputFocus()
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
      'support_agent': '🆘 Agente de Soporte',
      'cross_sell_agent': '🛒 Agente Ventas Cruzadas'
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
          {ENABLE_TEST_PAYMENTS && (
            <button className="new-chat-btn" onClick={startTestPayment} title="Pago de prueba">
              <span>Pago de prueba</span>
            </button>
          )}
          {authRequired && token && (
            <button type="button" className="logout-btn" onClick={handleLogout} title="Cerrar sesión">
              Cerrar sesión
            </button>
          )}
        </div>
      </header>

      {/* Messages Container */}
      <main className="messages-container" onClickCapture={handleChatClickCapture}>
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
            onMouseDown={(e) => e.preventDefault()}
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
