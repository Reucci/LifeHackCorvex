import { resetState } from '../utils/store';

const ITEMS = [
  { name: 'Home', icon: '🏠', view: 'home' },
  { name: 'Your Impact', icon: '📊', view: 'today' },
  { name: 'Ecoling', icon: '🌱', view: 'sprout' },
  { name: 'History', icon: '📋', view: 'history' },
  { name: 'Leaderboard', icon: '🏆', view: 'leaderboard' },
  { name: 'Me', icon: '👤', view: 'profile' },
];

export default function Menu({ open, onClose, active, onNav }) {
  const go = (view) => {
    onNav(view);
    onClose();
  };

  const handleReset = () => {
    if (window.confirm('Reset all progress? (demo helper)')) {
      resetState();
      window.location.reload();
    }
  };

  return (
    <>
      <div
        className={`drawer-scrim${open ? ' drawer-scrim--open' : ''}`}
        onClick={onClose}
      />
      <aside className={`drawer${open ? ' drawer--open' : ''}`}>
        <div className="drawer-head">
          <span className="drawer-logo">🌱 Ecolings</span>
          <button className="drawer-close" aria-label="Close menu" onClick={onClose}>✕</button>
        </div>

        <nav className="drawer-nav">
          {ITEMS.map((item) => (
            <button
              key={item.view}
              className={`drawer-item${active === item.view ? ' drawer-item--active' : ''}`}
              onClick={() => go(item.view)}
            >
              <span className="drawer-item-icon">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="drawer-foot">
          <button className="ghost-btn" onClick={handleReset}>Reset progress (demo)</button>
        </div>
      </aside>
    </>
  );
}
