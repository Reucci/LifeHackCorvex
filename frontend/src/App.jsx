import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState(() => localStorage.getItem('ecolings_token'))
  const [user, setUser] = useState(null)
  const [dailyQuest, setDailyQuest] = useState(null)
  const [questRefresh, setQuestRefresh] = useState(0)
  const [areas, setAreas] = useState([])
  const [selectedAreaName, setSelectedAreaName] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const userId = user?.id

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

  useEffect(() => {
    if (!token || !userId) return

    fetch(`${API_URL}/weather/areas`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || 'Could not load areas')
        return data.areas
      })
      .then((availableAreas) => {
        setAreas(availableAreas)
        const savedArea = localStorage.getItem(`ecolings_area_${userId}`)
        if (savedArea && availableAreas.some((area) => area.name === savedArea)) {
          setSelectedAreaName(savedArea)
        }
      })
      .catch((error) => setMessage(error.message))
  }, [token, userId])

  useEffect(() => {
    if (!token || !userId || !selectedAreaName || areas.length === 0) return
    const selectedArea = areas.find((area) => area.name === selectedAreaName)
    if (!selectedArea) return

    async function loadQuest() {
      setMessage('')
      try {
        const query = new URLSearchParams({
          latitude: selectedArea.latitude,
          longitude: selectedArea.longitude,
        })
        const response = await fetch(`${API_URL}/quests/current?${query}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || 'Could not load weather')
        setDailyQuest(data)
      } catch (error) {
        setMessage(error.message)
      }
    }
    loadQuest()
  }, [token, userId, selectedAreaName, areas, questRefresh])

  useEffect(() => {
    if (!dailyQuest?.slot_end) return
    const millisecondsUntilNextSlot = Math.max(
      1000,
      new Date(dailyQuest.slot_end).getTime() - Date.now() + 1000,
    )
    const timer = setTimeout(() => {
      setDailyQuest(null)
      setQuestRefresh((value) => value + 1)
    }, millisecondsUntilNextSlot)
    return () => clearTimeout(timer)
  }, [dailyQuest?.slot_end])

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

  async function completeAction(questKey) {
    if (!dailyQuest) return
    setLoading(true)
    setMessage('')
    try {
      const data = await apiRequest('/actions/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quest_id: dailyQuest.quest_id, quest_key: questKey }),
      })
      setUser(data.user)
      setDailyQuest((current) => ({
        ...current,
        completed: true,
        selected_quest_key: data.selected_quest_key,
      }))
      setMessage(`${data.message} You earned ${data.gold_earned} gold.`)
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
      setDailyQuest(null)
      setAreas([])
      setSelectedAreaName('')
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

  const temperature = dailyQuest?.weather.observations.temperature
  const humidity = dailyQuest?.weather.observations.humidity
  const forecast = dailyQuest?.weather.forecast

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

      <section className="weather-card">
        <div className="area-picker">
          <p className="eyebrow">Live local weather</p>
          <label htmlFor="weather-area">Select your area</label>
          <select
            id="weather-area"
            value={selectedAreaName}
            onChange={(event) => {
              const areaName = event.target.value
              setSelectedAreaName(areaName)
              setDailyQuest(null)
              setMessage('')
              if (areaName) localStorage.setItem(`ecolings_area_${userId}`, areaName)
            }}
          >
            <option value="">Choose a Singapore area…</option>
            {areas.map((area) => <option value={area.name} key={area.name}>{area.name}</option>)}
          </select>
          {selectedAreaName && <p className="location-note">Using {selectedAreaName}</p>}
        </div>
        {temperature ? (
          <div className="weather-reading">
            <strong>{temperature.value}°C</strong>
            <span>{forecast?.condition || 'Current observation'}</span>
            <small>
              {temperature.station.name} · {temperature.station.distance_km} km away · {temperature.age_minutes} min old
            </small>
            {humidity && <small>Humidity {humidity.value}% · forecast area {forecast?.area || 'unavailable'}</small>}
            {dailyQuest.weather.warnings.map((warning) => <small className="weather-warning" key={warning}>⚠ {warning}</small>)}
          </div>
        ) : <p>{selectedAreaName ? 'Loading official NEA readings…' : 'Choose your area to load weather.'}</p>}
      </section>

      <section className="action-card">
        <p className="eyebrow">Current two-hour quest</p>
        {dailyQuest ? (
          <>
            <div className="slot-heading">
              <h2>Choose one action</h2>
              <span>Available until {new Date(dailyQuest.slot_end).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
            </div>
            <div className="quest-options">
              {dailyQuest.options.map((quest) => {
                const selected = dailyQuest.selected_quest_key === quest.id
                return (
                  <article className={selected ? 'quest-option selected' : 'quest-option'} key={quest.id}>
                    <div className="quest-heading">
                      <h3>{quest.title}</h3>
                      <span className={`difficulty ${quest.difficulty}`}>{quest.difficulty}</span>
                    </div>
                    <p>{quest.description}</p>
                    <p className="weather-reason">{quest.reason}</p>
                    <button className="primary-button" onClick={() => completeAction(quest.id)} disabled={loading || dailyQuest.completed}>
                      {selected ? 'Completed ✓' : dailyQuest.completed ? 'Other choice completed' : loading ? 'Saving…' : `Choose this · +${quest.points} gold`}
                    </button>
                  </article>
                )
              })}
            </div>
          </>
        ) : <p>{selectedAreaName ? 'Creating two safe choices from your local weather…' : 'Select your area above to receive quests.'}</p>}
        {message && <p className={`message ${dailyQuest ? 'success' : 'error'}`}>{message}</p>}
      </section>

      <p className="source-note">Weather source: NEA via data.gov.sg. Station readings may differ from conditions inside your building.</p>
    </main>
  )
}

export default App
