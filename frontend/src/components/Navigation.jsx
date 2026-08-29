const NAV_ITEMS = [
  { name: 'Home', icon: '🏠', view: 'home' },
  { name: 'Impact', icon: '📊', view: 'today' },
  { name: 'Ecoling', icon: '🐥', view: 'sprout' },
  { name: 'Calendar', icon: '📅', view: 'history' },
  { name: 'Profile', icon: '👤', view: 'profile' },
];

export default function Navigation({ active, onNavClick }) {
  return (
    <nav className="bottom-nav">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.name}
          className={`nav-item${active === item.view ? ' nav-item--active' : ''}`}
          onClick={() => onNavClick(item.view)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.name}</span>
        </button>
      ))}
    </nav>
  );
}
