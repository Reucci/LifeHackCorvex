// Local persistence for the care loop. Mock/local data — fine for a prototype.

const KEY = 'ecolings-state-v2';

function dateKey(d = new Date()) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
function todayKey() {
  return dateKey();
}
function shiftKey(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return dateKey(d);
}

const EMPTY = {
  totalPoints: 0,
  streak: 0,
  longestStreak: 0,
  lastCompletedDate: null,
  completedDates: [],
  log: [], // { date, habit, points, difficulty, weather:{icon,condition,temp} }
};

// A little sample history so the calendar / stats look alive in the demo.
function seed() {
  const samples = [
    { d: -6, habit: 'Opened a window instead of AC', points: 25, difficulty: 1, weather: { icon: '🌤️', condition: 'Chilly & dry', temp: 18 } },
    { d: -5, habit: 'Line-dried laundry', points: 33, difficulty: 1.3, weather: { icon: '🌧️', condition: 'Rainy', temp: 26 } },
    { d: -4, habit: 'Walked/biked instead of driving', points: 25, difficulty: 1, weather: { icon: '☀️', condition: 'Mild & clear', temp: 24 } },
    { d: -3, habit: 'Closed the blinds', points: 38, difficulty: 1.5, weather: { icon: '🌡️', condition: 'Hot & humid', temp: 31 } },
    { d: -2, habit: 'Unplugged a standby device', points: 25, difficulty: 1, weather: { icon: '☁️', condition: 'Overcast', temp: 22 } },
    { d: -1, habit: 'Turned the heating down', points: 38, difficulty: 1.5, weather: { icon: '❄️', condition: 'Cold snap', temp: 7 } },
  ];
  const log = samples.map((s) => ({
    date: shiftKey(s.d),
    habit: s.habit,
    points: s.points,
    difficulty: s.difficulty,
    weather: s.weather,
  }));
  const completedDates = log.map((e) => e.date);
  return {
    ...EMPTY,
    totalPoints: log.reduce((sum, e) => sum + e.points, 0),
    streak: 6,
    longestStreak: 14,
    lastCompletedDate: shiftKey(-1),
    completedDates,
    log,
  };
}

export function loadState() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) {
      const seeded = seed();
      saveState(seeded);
      return seeded;
    }
    return { ...EMPTY, ...JSON.parse(raw) };
  } catch {
    return seed();
  }
}

export function saveState(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
}

export function isDoneToday(state) {
  return state.lastCompletedDate === todayKey();
}

export function completeToday(state, { habit, points, difficulty, weather }) {
  if (isDoneToday(state)) return state;
  const today = todayKey();
  const continuing = state.lastCompletedDate === shiftKey(-1);
  const streak = continuing ? state.streak + 1 : 1;

  const next = {
    ...state,
    totalPoints: state.totalPoints + points,
    streak,
    longestStreak: Math.max(state.longestStreak || 0, streak),
    lastCompletedDate: today,
    completedDates: [...new Set([...state.completedDates, today])],
    log: [{ date: today, habit, points, difficulty, weather }, ...state.log].slice(0, 90),
  };
  saveState(next);
  return next;
}

function daysSince(date) {
  if (!date) return null;
  const [year, month, day] = date.split('-').map(Number);
  const completed = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((today - completed) / 86_400_000));
}

// Mood is derived from care recency and streak, so it naturally changes over time.
export function petMood(state) {
  const inactiveDays = daysSince(state.lastCompletedDate);
  if (inactiveDays === 0) {
    if (state.streak >= 3) {
      return {
        emotion: 'excited',
        pct: Math.min(100, 88 + state.streak * 2),
        label: `Full of energy from a ${state.streak}-day streak!`,
      };
    }
    return { emotion: 'happy', pct: 82, label: 'Happy and cared for today' };
  }
  if (inactiveDays === 1) {
    return { emotion: 'normal', pct: 60, label: "Doing okay — ready for today's quest" };
  }
  if (inactiveDays !== null) {
    return {
      emotion: 'sad',
      pct: Math.max(15, 45 - (inactiveDays - 2) * 8),
      label: `${inactiveDays} days since your last check-in`,
    };
  }
  return { emotion: 'normal', pct: 50, label: 'Curious and ready to begin' };
}

export function petEmotion(state) {
  return petMood(state).emotion;
}

// --- Stats helpers -------------------------------------------------------
export function weekPoints(state) {
  const weekAgo = shiftKey(-7);
  return state.log
    .filter((e) => e.date > weekAgo)
    .reduce((sum, e) => sum + e.points, 0);
}

export function savings(state) {
  // Rough demo estimates: ~0.9 kWh and ~0.38 kg CO2 saved per completed action.
  const n = state.log.length;
  return {
    kwh: (n * 0.9).toFixed(1),
    co2: (n * 0.38).toFixed(1),
  };
}

export function resetState() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
  return loadState();
}
