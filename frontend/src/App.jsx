import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState(() => localStorage.getItem('ecolings_token'))
  const [user, setUser] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function apiRequest(path, options = {}) {
    const headers = { ...options.headers }
    if (token) headers.Authorization = `Bearer ${token}`
    const response = await fetch(`${API_URL}${path}`, { ...options, headers })
    if (response.status === 204) return null
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Something went wrong')
    return data
  }

  useEffect(() => {
    if (!token) return
    fetch(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail)
        return data
      })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('ecolings_token')
        setToken(null)
      })
  }, [token])

  async function handleAuth(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const data = await apiRequest(`/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      localStorage.setItem('ecolings_token', data.token)
      setToken(data.token)
      setUser(data.user)
      setPassword('')
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function completeAction() {
    setLoading(true)
    setMessage('')
    try {
      const data = await apiRequest('/actions/complete', { method: 'POST' })
      setUser(data.user)
      setMessage(data.message)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    try {
      await apiRequest('/auth/logout', { method: 'POST' })
    } finally {
      localStorage.removeItem('ecolings_token')
      setToken(null)
      setUser(null)
      setMessage('')
    }
  }

  if (!user) {
    return (
      <main className="app-shell auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Welcome to</p>
          <h1>Ecolings</h1>
          <p className="subtitle">Small daily actions help your Ecoling thrive.</p>
          <form onSubmit={handleAuth}>
            <label>Username
              <input value={username} onChange={(event) => setUsername(event.target.value)} minLength="3" maxLength="30" pattern="[A-Za-z0-9_-]+" autoComplete="username" required />
            </label>
            <label>Password
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength="8" maxLength="128" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required />
            </label>
            {message && <p className="message error">{message}</p>}
            <button className="primary-button" disabled={loading}>
              {loading ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
            </button>
          </form>
          <button className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setMessage('') }}>
            {mode === 'login' ? 'New here? Create an account' : 'Already have an account? Log in'}
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell dashboard-shell">
      <header>
        <div><p className="eyebrow">Your Ecoling</p><h1>Hello, {user.username}!</h1></div>
        <button className="text-button" onClick={logout}>Log out</button>
      </header>
      <section className="stats" aria-label="Account progress">
        <article><strong>{user.daily_streak}</strong><span>day streak 🔥</span></article>
        <article><strong>{user.gold}</strong><span>gold 🪙</span></article>
        <article><strong>{user.ecoling_state}</strong><span>Ecoling state</span></article>
      </section>
      <section className="action-card">
        <p className="eyebrow">Today’s energy action</p>
        <h2>Close your blinds early</h2>
        <p>Keep direct sunlight out and reduce the need for air conditioning.</p>
        <button className="primary-button" onClick={completeAction} disabled={loading || user.last_completed_date === new Date().toISOString().slice(0, 10)}>
          {user.last_completed_date === new Date().toISOString().slice(0, 10) ? 'Completed today ✓' : loading ? 'Saving…' : 'I did it! +10 gold'}
        </button>
        {message && <p className="message success">{message}</p>}
      </section>
    </main>
  )
}

export default App
