// Lightweight user preferences (display name, reminders, units).
// Local only — fine for the prototype.

const KEY = 'ecolings-prefs-v1';

const DEFAULTS = {
  displayName: 'Leafy Friend',
  reminders: true,
  reminderTime: '18:00',
  units: 'metric', // 'metric' | 'imperial'
  sound: true,
};

export function loadPrefs() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
  } catch {
    return { ...DEFAULTS };
  }
}

export function savePrefs(prefs) {
  const next = { ...DEFAULTS, ...prefs };
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}
