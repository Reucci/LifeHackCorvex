import { useState, useCallback } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import Menu from './components/Menu';
import Toast from './components/Toast';
import Home from './pages/Home';
import History from './pages/History';
import Stats from './pages/Stats';
import Sprout from './pages/Sprout';
import Profile from './pages/Profile';
import Badges from './pages/Badges';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { MOCK_WEATHER, pickSuggestion, difficultyFor } from './utils/weather';
import { loadState, completeToday, isDoneToday, petEmotion } from './utils/store';
import { loadAuth, clearAuth, logout as apiLogout } from './utils/auth';
import './css/App.css';

const BASE_POINTS = 25;

// Frontend mock — replace with real weather later.
const weather = MOCK_WEATHER;
const suggestion = pickSuggestion(weather);
const difficulty = difficultyFor(weather);

const HEADER = {
  home: {},
  today: { title: 'Your Impact' },
  sprout: { title: 'Ecoling' },
  history: { title: 'Calendar' },
  profile: { title: 'Me', action: 'settings' },
  badges: { title: 'Badges' },
  settings: { title: 'Settings' },
};

export default function App() {
  const [auth, setAuth] = useState(loadAuth);
  const [view, setView] = useState('home');
  const [state, setState] = useState(loadState);
  const [toast, setToast] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [celebrate, setCelebrate] = useState(false);

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2400);
  }, []);

  if (!auth) {
    return (
      <div className="app-container">
        <Login onAuthed={(a) => { setAuth(a); setView('home'); }} />
      </div>
    );
  }

  const done = isDoneToday(state);
  const emotion = petEmotion(state);
  const points = Math.round(BASE_POINTS * difficulty);

  const handleComplete = () => {
    if (done) return;
    const next = completeToday(state, {
      habit: suggestion.habit,
      points,
      difficulty,
      weather: { icon: weather.icon, condition: weather.condition, temp: weather.temp },
    });
    setState(next);
    setCelebrate(true);
    showToast(
      difficulty > 1
        ? `+${points} 🍃 — tough weather today, nice work!`
        : `+${points} 🍃 — Ecoling is happy!`
    );
  };

  const handleLogout = async () => {
    await apiLogout();
    clearAuth();
    setAuth(null);
    setView('home');
  };

  const headerCfg = HEADER[view] || {};

  return (
    <div className="app-container">
      <Header
        title={headerCfg.title}
        action={headerCfg.action}
        onMenu={() => setMenuOpen(true)}
        onAction={() => headerCfg.action === 'settings' && setView('settings')}
      />

      {view === 'home' && (
        <Home
          weather={weather}
          suggestion={suggestion}
          difficulty={difficulty}
          points={points}
          done={done}
          emotion={emotion}
          streak={state.streak}
          totalPoints={state.totalPoints}
          onComplete={handleComplete}
          celebrate={celebrate}
          onDismissCelebrate={() => setCelebrate(false)}
        />
      )}
      {view === 'today' && <Stats state={state} />}
      {view === 'sprout' && <Sprout emotion={emotion} streak={state.streak} done={done} />}
      {view === 'history' && <History state={state} />}
      {view === 'profile' && <Profile state={state} auth={auth} onNav={setView} />}
      {view === 'badges' && <Badges state={state} />}
      {view === 'settings' && (
        <Settings auth={auth} onLogout={handleLogout} />
      )}

      <Navigation active={view} onNavClick={setView} />
      <Menu open={menuOpen} onClose={() => setMenuOpen(false)} active={view} onNav={setView} />
      <Toast message={toast} />
    </div>
  );
}
