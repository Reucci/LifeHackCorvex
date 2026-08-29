import { useState, useCallback, useEffect } from 'react';
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
import { MOCK_WEATHER, getWeather, pickSuggestion, difficultyFor } from './utils/weather';
import { loadState, completeToday, isDoneToday, petEmotion } from './utils/store';
import { loadAuth, clearAuth, logout as apiLogout } from './utils/auth';
import { fetchState, completeAction } from './utils/api';
import './css/App.css';

const BASE_POINTS = 25;

const EMPTY_STATE = {
  totalPoints: 0,
  streak: 0,
  longestStreak: 0,
  lastCompletedDate: null,
  completedDates: [],
  log: [],
};

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
  const [state, setState] = useState(() =>
    auth && !auth.guest ? EMPTY_STATE : loadState()
  );
  const [weather, setWeather] = useState(MOCK_WEATHER);
  const [toast, setToast] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [celebrate, setCelebrate] = useState(false);

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2400);
  }, []);

  useEffect(() => {
    getWeather().then(setWeather);
  }, []);

  useEffect(() => {
    if (auth && !auth.guest) {
      fetchState(auth.token).then(setState).catch(() => {});
    }
  }, [auth]);

  if (!auth) {
    return (
      <div className="app-container">
        <Login onAuthed={(a) => { setAuth(a); setView('home'); }} />
      </div>
    );
  }

  const suggestion = pickSuggestion(weather);
  const difficulty = difficultyFor(weather);
  const done = isDoneToday(state);
  const emotion = petEmotion(state);
  const points = Math.round(BASE_POINTS * difficulty);

  const handleComplete = async () => {
    if (done) return;
    const payload = {
      habit: suggestion.habit,
      points,
      difficulty,
      weather: { icon: weather.icon, condition: suggestion.label, temp: weather.temp },
    };

    if (auth.guest) {
      setState(completeToday(state, payload));
    } else {
      try {
        const data = await completeAction(auth.token, payload);
        setState(data.state);
      } catch {
        showToast("Couldn't save — check your connection and try again.");
        return;
      }
    }

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
    setState(loadState());
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
