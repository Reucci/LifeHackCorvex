import { NAV_ITEMS } from '../utils/navigation';

export default function Menu({ open, onClose, active, onNav }) {
  const go = (view) => {
    onNav(view);
    onClose();
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
          {NAV_ITEMS.map((item) => (
            <button
              key={item.view}
              className={`drawer-item${active === item.view ? ' drawer-item--active' : ''}`}
              onClick={() => go(item.view)}
              type="button"
            >
              <span className="drawer-item-icon">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

      </aside>
    </>
  );
}
