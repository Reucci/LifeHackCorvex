import { earnedCount } from '../utils/badges';
import { loadPrefs } from '../utils/prefs';

export default function Profile({ state, auth, onNav, badgeCount, prefs: serverPrefs, onReset }) {
  const level = Math.floor(state.totalPoints / 250) + 1;
  const intoLevel = state.totalPoints % 250;
  const prefs = serverPrefs || loadPrefs();
  const badges = badgeCount ?? earnedCount(state);

  const rows = [
    { icon: '📊', label: 'My Stats', view: 'today' },
    { icon: '🏅', label: 'Badges', meta: `${badges}`, view: 'badges' },
    {
      icon: '🔔',
      label: 'Reminders',
      meta: prefs.reminders ? 'ON' : 'OFF',
      view: 'settings',
    },
    { icon: 'ℹ️', label: 'About Ecoling', view: 'sprout' },
    { icon: '⚙️', label: 'Settings', view: 'settings' },
  ];

  const handleReset = () => {
    if (window.confirm('Reset all progress? (demo helper)')) {
      onReset();
    }
  };

  return (
    <div className="content">
        <div className="card profile-card">
          <div className="profile-avatar">🐤</div>
          <div className="profile-info">
            <div className="profile-name">
              {prefs.display_name || prefs.displayName} 🍃
            </div>
            <div className="profile-level">
              Level {level}
              {auth?.user?.username && !auth.guest ? ` · @${auth.user.username}` : ''}
            </div>
            <div className="level-bar">
              <div className="level-fill" style={{ width: `${(intoLevel / 250) * 100}%` }} />
            </div>
            <div className="level-caption">{intoLevel} / 250 pts</div>
          </div>
        </div>

        <div className="menu-list">
          {rows.map((row) => (
            <button
              key={row.label}
              className="menu-row"
              onClick={() => row.view && onNav(row.view)}
            >
              <span className="menu-icon">{row.icon}</span>
              <span className="menu-label">{row.label}</span>
              {row.badge && <span className="menu-badge">{row.badge}</span>}
              {row.meta && <span className="menu-meta">{row.meta}</span>}
              <span className="menu-chevron">›</span>
            </button>
          ))}
        </div>

        <button className="ghost-btn" onClick={handleReset}>
          Reset progress (demo)
        </button>
    </div>
  );
}
