import { resetState } from '../utils/store';

const ROWS = [
  { icon: '📊', label: 'My Stats', view: 'today' },
  { icon: '🏅', label: 'Badges', badge: 'New!' },
  { icon: '🔔', label: 'Reminders', meta: 'ON' },
  { icon: 'ℹ️', label: 'About Ecoling', view: 'sprout' },
  { icon: '⚙️', label: 'Settings' },
];

export default function Profile({ state, onNav }) {
  const level = Math.floor(state.totalPoints / 250) + 1;
  const intoLevel = state.totalPoints % 250;

  const handleReset = () => {
    if (window.confirm('Reset all progress? (demo helper)')) {
      resetState();
      window.location.reload();
    }
  };

  return (
    <div className="content">
        <div className="card profile-card">
          <div className="profile-avatar">🐤</div>
          <div className="profile-info">
            <div className="profile-name">Leafy Friend 🍃</div>
            <div className="profile-level">Level {level}</div>
            <div className="level-bar">
              <div className="level-fill" style={{ width: `${(intoLevel / 250) * 100}%` }} />
            </div>
            <div className="level-caption">{intoLevel} / 250 pts</div>
          </div>
        </div>

        <div className="menu-list">
          {ROWS.map((row) => (
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
