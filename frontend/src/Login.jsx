import { useState } from 'react'
import './App.css'

const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_URL = rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')
  ? rawApiUrl
  : `https://${rawApiUrl.replace(/^\/*/, '')}`

const API_HEADERS_BASE = {
  'ngrok-skip-browser-warning': 'true',
}

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          ...API_HEADERS_BASE,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: form.toString(),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Usuario o contraseña incorrectos')
      }
      const data = await response.json()
      onSuccess(data.access_token)
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>Muppy AI</h1>
          <p>Asistente de Seguros Mapfre</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Usuario
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Usuario"
              required
              autoComplete="username"
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Contraseña"
              required
              autoComplete="current-password"
            />
          </label>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" disabled={loading} className="login-btn">
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
