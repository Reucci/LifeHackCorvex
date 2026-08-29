import { API_BASE, clearAuth, loadAuth } from './auth';

export async function apiRequest(path, options = {}) {
  const auth = loadAuth();
  const headers = { ...options.headers };
  if (auth?.token) headers.Authorization = `Bearer ${auth.token}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    const error = new Error('Cannot reach the Ecolings server.');
    error.offline = true;
    throw error;
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    clearAuth();
    window.dispatchEvent(new Event('ecolings-session-expired'));
  }
  if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
  return data;
}

export const getMe = () => apiRequest('/users/me');
export const getAreas = () => apiRequest('/weather/areas');
export const getHistory = () => apiRequest('/quests/history');
export const getStats = () => apiRequest('/users/me/stats');
export const getBadges = () => apiRequest('/users/me/badges');
export const getPreferences = () => apiRequest('/users/me/preferences');

export function getCurrentQuest(area) {
  const query = new URLSearchParams({
    latitude: area.latitude,
    longitude: area.longitude,
  });
  return apiRequest(`/quests/current?${query}`);
}

export const completeQuest = (questId, questKey) => apiRequest('/actions/complete', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ quest_id: questId, quest_key: questKey }),
});

// Submit a proof photo (data: URL). The bot checks it against the quest and,
// if it passes, the quest is completed and gold is awarded server-side.
export const verifyQuest = (questId, questKey, image) => apiRequest('/actions/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ quest_id: questId, quest_key: questKey, image }),
});

export const savePreferences = (preferences) => apiRequest('/users/me/preferences', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(preferences),
});

export const resetProgress = () => apiRequest('/users/me/progress', { method: 'DELETE' });
