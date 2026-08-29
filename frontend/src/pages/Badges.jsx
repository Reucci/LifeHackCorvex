import { badgeStatus } from '../utils/badges';

export default function Badges({ state, badges: serverBadges }) {
  const badges = serverBadges || badgeStatus(state);
  const earned = badges.filter((badge) => badge.earned).length;

  return (
    <div className="content">
      <div className="card badges-summary">
        <div className="badges-summary-value">{earned} / {badges.length}</div>
        <div className="badges-summary-label">badges earned</div>
      </div>

      <div className="badge-grid">
        {badges.map((b) => (
          <div
            key={b.id}
            className={`badge-tile${b.earned ? ' badge-tile--earned' : ''}`}
          >
            <div className="badge-icon">{b.icon}</div>
            <div className="badge-name">{b.name}</div>
            <div className="badge-desc">{b.desc}</div>
            {b.earned ? (
              <div className="badge-status badge-status--done">Earned ✓</div>
            ) : (
              <>
                <div className="badge-bar">
                  <div className="badge-fill" style={{ width: `${b.pct}%` }} />
                </div>
                <div className="badge-status">
                  {b.have} / {b.need}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
