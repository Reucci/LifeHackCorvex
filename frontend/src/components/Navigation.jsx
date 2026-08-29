import { NAV_ITEMS } from '../utils/navigation';

export default function Navigation({ active, onNavClick }) {
  return (
    <nav className="bottom-nav">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.name}
          className={`nav-item${active === item.view ? ' nav-item--active' : ''}`}
          onClick={() => onNavClick(item.view)}
          type="button"
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.name}</span>
        </button>
      ))}
    </nav>
  );
}
