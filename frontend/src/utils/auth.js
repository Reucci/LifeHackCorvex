// Auth helper. Talks to the FastAPI backend when it's reachable, and falls
// back to a local "guest" session so the prototype always works offline.

const KEY = 'ecolings-auth-v1';

export const API_BASE =
  process.env.REACT_APP_API_BASE || 'http://localhost:8000';

export function loadAuth() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveAuth(auth) {
  try {
    localStorage.setItem(KEY, JSON.stringify(auth));
  } catch {
    /* ignore */
  }
}

export function clearAuth() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

async function authRequest(path, credentials) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
  } catch {
    // Backend not running — signal the caller so it can offer guest mode.
    const err = new Error('offline');
    err.offline = true;
    throw err;
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Something went wrong. Please try again.');
  }
  return data;
}

export async function login({ username, password }) {
  const data = await authRequest('/auth/login', { username, password });
  const auth = { token: data.token, user: data.user, guest: false };
  saveAuth(auth);
  return auth;
}

export async function register({ username, password }) {
  const data = await authRequest('/auth/register', { username, password });
  const auth = { token: data.token, user: data.user, guest: false };
  saveAuth(auth);
  return auth;
}

export function guestLogin(name = 'Leafy Friend') {
  const auth = {
    token: null,
    guest: true,
    user: { username: name },
  };
  saveAuth(auth);
  return auth;
}

export async function logout() {
  const auth = loadAuth();
  if (auth && auth.token) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${auth.token}` },
      });
    } catch {
      /* best effort */
    }
  }
  clearAuth();
}
