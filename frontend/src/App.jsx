import { useCallback, useEffect, useMemo, useState } from 'react';
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
import Leaderboard from './pages/Leaderboard';
import CameraVerification from './pages/CameraVerification';
import NameEcoling from './components/NameEcoling';
import { MOCK_WEATHER, pickSuggestion, difficultyFor } from './utils/weather';
import { completeToday, isDoneToday, loadState, petMood, resetState } from './utils/store';
import { clearAuth, loadAuth, logout as apiLogout } from './utils/auth';
import { notifyNewQuest, requestNotificationPermission } from './utils/notifications';
import {
  completeQuest, getAreas, getBadges, getCurrentQuest, getHistory, getMe,
  getEcolingMessage, getPreferences, getStats, resetProgress, savePreferences, verifyQuestEvidence,
} from './utils/api';
import './css/App.css';

const SKY_CLASSES = ['sunny', 'partly', 'overcast', 'rainy'];

const skyImage = (sky) => `${process.env.PUBLIC_URL}/images/weather-${sky}.png`;

function skyForWeather(weather, guest) {
  if (guest && SKY_CLASSES.includes(weather?.sky)) return weather.sky;
  const condition = (weather?.forecast?.condition || '').toLowerCase();
  const rainfall = weather?.observations?.rainfall?.value || 0;
  if (rainfall > 0 || /(rain|shower|thunder)/.test(condition)) return 'rainy';
  if (/(fair|sunny|clear)/.test(condition)) return 'sunny';
  if (/(cloud|overcast|fog|haze)/.test(condition)) return 'overcast';
  return 'partly';
}

const HEADER = {
  home: {}, today: { title: 'Your Impact' }, sprout: { title: 'Ecoling' },
  history: { title: 'Calendar' }, profile: { title: 'Me' },
  badges: { title: 'Badges' }, settings: { title: 'Settings' },
  leaderboard: { title: 'Leaderboard' },
};

const EMPTY_STATE = {
  totalPoints: 0, streak: 0, longestStreak: 0, lastCompletedDate: null,
  completedDates: [], log: [], estimatedKwh: 0, estimatedCo2: 0, weekPoints: 0,
};

function serverState(stats, history) {
  return {
    ...EMPTY_STATE, totalPoints: stats.total_gold, streak: stats.current_streak,
    longestStreak: stats.longest_streak, completedDates: history.completed_dates,
    lastCompletedDate: history.completed_dates.at(-1) || null, weekPoints: stats.week_gold,
    estimatedKwh: stats.estimated_kwh, estimatedCo2: stats.estimated_co2_kg,
    log: history.entries.map((entry) => ({
      ...entry,
      difficulty: entry.difficulty === 'hard' ? 1.5 : entry.difficulty === 'medium' ? 1.2 : 1,
      weather: { ...entry.weather, icon: '🌤️' },
    })),
  };
}

export default function App() {
  const [auth, setAuth] = useState(loadAuth);
  const [view, setView] = useState('home');
  const [state, setState] = useState(() => loadAuth()?.guest ? loadState() : EMPTY_STATE);
  const [areas, setAreas] = useState([]);
  const [areaName, setAreaName] = useState('');
  const [quest, setQuest] = useState(null);
  const [badges, setBadges] = useState([]);
  const [prefs, setPrefs] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [celebration, setCelebration] = useState(null);
  const [verificationTask, setVerificationTask] = useState(null);
  const [namePromptDismissed, setNamePromptDismissed] = useState(false);
  const [aiEcolingMessage, setAiEcolingMessage] = useState('');
  const authUserId = auth?.user?.id;

  const showToast = useCallback((message) => {
    setToast(message);
    setTimeout(() => setToast(null), 2400);
  }, []);

  const refreshAccount = useCallback(async () => {
    const [user, history, stats, badgeData, preferences] = await Promise.all([
      getMe(), getHistory(), getStats(), getBadges(), getPreferences(),
    ]);
    setAuth((current) => ({ ...current, user }));
    setState(serverState(stats, history));
    setBadges(badgeData.badges);
    setPrefs(preferences);
  }, []);

  useEffect(() => {
    const expire = () => { setAuth(null); setView('home'); };
    window.addEventListener('ecolings-session-expired', expire);
    return () => window.removeEventListener('ecolings-session-expired', expire);
  }, []);

  useEffect(() => {
    if (!auth?.token || auth.guest) return;
    setBusy(true);
    Promise.all([refreshAccount(), getAreas()])
      .then(([, result]) => {
        setAreas(result.areas);
        const saved = localStorage.getItem(`ecolings-area-${authUserId}`);
        if (saved && result.areas.some((area) => area.name === saved)) setAreaName(saved);
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }, [auth?.token, auth?.guest, authUserId, refreshAccount]);

  const selectedArea = useMemo(() => areas.find((area) => area.name === areaName), [areas, areaName]);

  useEffect(() => {
    if (!selectedArea || auth?.guest) return;
    setBusy(true);
    setError('');
    getCurrentQuest(selectedArea).then(setQuest).catch((err) => setError(err.message)).finally(() => setBusy(false));
  }, [selectedArea, auth?.guest]);

  useEffect(() => {
    if (!quest?.slot_end) return undefined;
    const delay = Math.max(1000, new Date(quest.slot_end).getTime() - Date.now() + 1000);
    const timer = setTimeout(() => {
      if (!selectedArea) return;
      getCurrentQuest(selectedArea).then(setQuest).catch((err) => setError(err.message));
    }, delay);
    return () => clearTimeout(timer);
  }, [quest?.slot_end, selectedArea]);

  useEffect(() => {
    if (!quest?.quest_id || !prefs?.reminders || auth?.guest) return;
    requestNotificationPermission().then((permission) => {
      if (permission === 'granted') {
        notifyNewQuest(quest, authUserId, prefs.quiet_hours ?? prefs.quietHours ?? true);
      }
    });
  }, [quest, prefs?.reminders, prefs?.quiet_hours, prefs?.quietHours, auth?.guest, authUserId]);

  const guestWeather = MOCK_WEATHER;
  const guestSuggestion = pickSuggestion(guestWeather);
  const guestDifficulty = difficultyFor(guestWeather);
  const guestPoints = Math.round(25 * guestDifficulty);
  const sky = skyForWeather(auth?.guest ? guestWeather : quest?.weather, auth?.guest);
  const done = auth?.guest ? isDoneToday(state) : Boolean(quest?.completed);
  const mood = petMood(state);
  const emotion = mood.emotion;
  const ecolingName = prefs?.ecoling_name ?? prefs?.ecolingName ?? '';

  useEffect(() => {
    if (!auth?.token || auth.guest || !ecolingName || !['home', 'sprout'].includes(view)) {
      setAiEcolingMessage('');
      return;
    }
    let active = true;
    const context = view === 'sprout' ? 'care' : done ? 'quest-complete' : 'home';
    getEcolingMessage({ name: ecolingName, mood: emotion, streak: state.streak, context })
      .then((result) => { if (active) setAiEcolingMessage(result.available ? result.message : ''); })
      .catch(() => { if (active) setAiEcolingMessage(''); });
    return () => { active = false; };
  }, [auth?.token, auth?.guest, ecolingName, view, done, emotion, state.streak, quest?.quest_id]);

  if (!auth) return <div className="app-container"><Login onAuthed={(next) => { setAuth(next); setView('home'); }} /></div>;

  const chooseArea = (name) => {
    setAreaName(name); setQuest(null);
    if (name) localStorage.setItem(`ecolings-area-${auth.user.id}`, name);
  };

  const handleComplete = async (questKey) => {
    const task = auth.guest
      ? { action: guestSuggestion.action, icon: guestSuggestion.icon }
      : { action: quest?.options.find((option) => option.id === questKey)?.description || 'Complete your selected task', icon: '🌱' };
    setVerificationTask({ task, questKey });
    setView('verify');
  };

  const handleVerified = async () => {
    const { questKey } = verificationTask || {};
    setVerificationTask(null);
    if (auth.guest) {
      const next = completeToday(state, { habit: guestSuggestion.habit, points: guestPoints, difficulty: guestDifficulty, weather: guestWeather });
      setState(next); setCelebration({ points: guestPoints, difficulty: guestDifficulty });
      setView('home');
      return;
    }
    if (!quest || quest.completed) return;
    setBusy(true);
    try {
      const result = await completeQuest(quest.quest_id, questKey);
      setQuest((current) => ({ ...current, completed: true, selected_quest_key: result.selected_quest_key }));
      setCelebration({ points: result.gold_earned, difficulty: 1 });
      await refreshAccount();
      showToast(`+${result.gold_earned} mint — Ecoling is happy!`);
      setView('home');
    } catch (err) {
      setError(err.message);
      setView('home');
    } finally { setBusy(false); }
  };

  const handleLogout = async () => { await apiLogout(); clearAuth(); setAuth(null); setNamePromptDismissed(false); setView('home'); };
  const handlePrefs = async (next) => {
    if (auth.guest) { setPrefs(next); return; }
    setPrefs(await savePreferences(next));
  };
  const handleReset = async () => {
    if (auth.guest) resetState();
    else await resetProgress();
    window.location.reload();
  };

  const handleVerificationCheck = async (photo) => {
    if (auth.guest) {
      return { verdict: 'uncertain', reason: 'Guest mode uses manual confirmation.', safety_concern: false };
    }
    return verifyQuestEvidence(quest.quest_id, verificationTask.questKey, photo);
  };
  const handleEcolingName = async (name) => {
    await handlePrefs({ ...prefs, ecoling_name: name });
    setNamePromptDismissed(false);
  };
  const headerCfg = HEADER[view] || {};

  return (
    <div className={`app-container weather-bg weather-bg--${sky}`} style={{ backgroundImage: `url("${skyImage(sky)}")` }}>
      {view !== 'verify' && <Header title={headerCfg.title} action={headerCfg.action} onMenu={() => setMenuOpen(true)} onAction={() => setView('settings')} />}
      {view === 'verify' && <CameraVerification task={verificationTask?.task || { action: 'Complete your task', icon: '🌱' }} onCheck={handleVerificationCheck} onVerified={handleVerified} onCancel={() => { setVerificationTask(null); setView('home'); }} />}
      {view === 'home' && <Home guest={auth.guest} ecolingName={ecolingName} ecolingMessage={aiEcolingMessage} weather={auth.guest ? guestWeather : quest?.weather} guestSuggestion={guestSuggestion} guestDifficulty={guestDifficulty} guestPoints={guestPoints} quest={quest} areas={areas} areaName={areaName} onAreaChange={chooseArea} done={done} emotion={emotion} streak={state.streak} totalPoints={state.totalPoints} busy={busy} error={error} onComplete={handleComplete} celebration={celebration} onDismissCelebrate={() => setCelebration(null)} />}
      {view === 'today' && <Stats state={state} serverBacked={!auth.guest} />}
      {view === 'sprout' && <Sprout ecolingName={ecolingName} ecolingMessage={aiEcolingMessage} mood={mood} streak={state.streak} done={done} />}
      {view === 'history' && <History state={state} />}
      {view === 'profile' && <Profile state={state} auth={auth} onNav={setView} badgeCount={badges.filter((badge) => badge.earned).length} prefs={prefs} onReset={handleReset} />}
      {view === 'badges' && <Badges state={state} badges={auth.guest ? null : badges} />}
      {view === 'settings' && <Settings auth={auth} prefs={prefs} onPrefs={handlePrefs} onLogout={handleLogout} onReset={handleReset} />}
      {view === 'leaderboard' && <Leaderboard guest={auth.guest} />}
      {view !== 'verify' && <Navigation active={view} onNavClick={setView} />}
      {view !== 'verify' && <Menu open={menuOpen} onClose={() => setMenuOpen(false)} active={view} onNav={setView} />}
      {view !== 'verify' && <Toast message={toast} />}
      {!auth.guest && prefs && !ecolingName && !namePromptDismissed && (
        <NameEcoling onSave={handleEcolingName} onDismiss={() => setNamePromptDismissed(true)} />
      )}
    </div>
  );
}
