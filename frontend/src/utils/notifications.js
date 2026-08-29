const notificationKey = (userId) => `ecolings-notified-quest-${userId}`;

export function notificationsSupported() {
  return typeof window !== 'undefined' && 'Notification' in window;
}

export async function requestNotificationPermission() {
  if (!notificationsSupported()) return 'unsupported';
  if (Notification.permission !== 'default') return Notification.permission;
  return Notification.requestPermission();
}

export function isQuietHours(date = new Date()) {
  const hour = date.getHours();
  return hour >= 22 || hour < 8;
}

export function notifyNewQuest(quest, userId, quietHoursEnabled = true) {
  if (!quest?.quest_id || !userId || !notificationsSupported() || Notification.permission !== 'granted') {
    return false;
  }

  if (quietHoursEnabled && isQuietHours()) return false;

  const key = notificationKey(userId);
  if (localStorage.getItem(key) === String(quest.quest_id)) return false;

  const titles = (quest.options || []).map((option) => option.title).filter(Boolean);
  const notification = new Notification('New EcoLings quest!', {
    body: titles.length ? `Your new choices: ${titles.join(' or ')}` : 'A new two-hour quest is ready.',
    tag: `ecolings-quest-${quest.quest_id}`,
  });
  notification.onclick = () => {
    window.focus();
    notification.close();
  };
  localStorage.setItem(key, String(quest.quest_id));
  return true;
}
