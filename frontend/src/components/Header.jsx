export default function Header({ title, action, onMenu }) {
  return (
    <div className="header">
      <button className="icon-btn" aria-label="Menu" onClick={onMenu}>☰</button>
      {title && <span className="header-title">{title}</span>}
      <button className="icon-btn" aria-label={action === 'settings' ? 'Settings' : 'Notifications'}>
        {action === 'settings' ? '⚙️' : '🔔'}
      </button>
    </div>
  );
}
