export default function SuggestionCard({
  weather,
  suggestion,
  difficulty,
  points,
  done,
  offline,
  onComplete,
}) {
  return (
    <div className="suggestion-card">
      <div className="suggestion-title">Today's Suggestion</div>

      <div className="weather-info">
        <span className="weather-icon">{weather.icon}</span>
        <span className="weather-item">{weather.temp}°C</span>
        <span className="weather-divider">·</span>
        <span className="weather-item">{suggestion.label}</span>
        <span className="weather-divider">·</span>
        <span className="weather-item">📍 {weather.place}</span>
      </div>

      <div className="suggestion-text">
        {suggestion.summary}
        <br />
        <span className="suggestion-highlight">{suggestion.action}</span>
      </div>

      {difficulty > 1 && (
        <div className="difficulty-tag">
          🔥 Hard-weather day · points ×{difficulty} = {points} 🍃
        </div>
      )}

      <button
        className={`action-btn${done ? ' action-btn--done' : ''}`}
        onClick={onComplete}
        disabled={done}
      >
        {done ? "Done for today ✓" : `I'll do it!  (+${points} 🍃)`}
      </button>

      {offline && (
        <div className="offline-note">Showing sample weather — live data unavailable.</div>
      )}
    </div>
  );
}
