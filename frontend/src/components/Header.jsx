export default function Header({ title, onMenu, onAction }) {
  return (
    <div className="header">
      <button className="icon-btn" aria-label="Menu" onClick={onMenu}>☰</button>
      {title && <span className="header-title">{title}</span>}
      <button
        className="icon-btn"
        aria-label="Settings"
        onClick={onAction}
      >
        ⚙️
      </button>
    </div>
  );
}
