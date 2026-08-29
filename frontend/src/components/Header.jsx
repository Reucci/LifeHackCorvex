export default function Header({ title, action, onMenu, onAction }) {
  return (
    <div className="header">
      <button className="icon-btn" aria-label="Menu" onClick={onMenu}>☰</button>
      {title && <span className="header-title">{title}</span>}
      <button
        className="icon-btn"
        aria-label={action === 'settings' ? 'Settings' : 'Notifications'}
        onClick={onAction}
      >
        {action === 'settings' ? '⚙️' : '🔔'}
      </button>
    </div>
  );
}
