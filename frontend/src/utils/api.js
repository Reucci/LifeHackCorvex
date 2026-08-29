// Backend-backed care-loop state for real (non-guest) accounts. Mirrors the
// same shape/semantics as utils/store.js's local loadState()/completeToday(),
// just persisted server-side instead of localStorage.

import { API_BASE } from './auth';

export async function fetchState(token) {
  const res = await fetch(`${API_BASE}/state`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to load state');
  return res.json();
}

export async function completeAction(token, payload) {
  const res = await fetch(`${API_BASE}/actions/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to complete action');
  return res.json();
}
