import Chicken from '../components/Chicken';
import '../css/home.css';

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning!';
  if (h < 18) return 'Good afternoon!';
  return 'Good evening!';
}

function StreakLeaves({ streak }) {
  const filled = Math.min(streak, 7);
  return (
    <div className="streak-leaves">
      {Array.from({ length: 7 }, (_, i) => (
        <span key={i} className={i < filled ? 'leaf-on' : 'leaf-off'}>🍃</span>
      ))}
    </div>
  );
}

export default function Home({
  weather,
  suggestion,
  difficulty,
  points,
  done,
  emotion,
  streak,
  totalPoints,
  onComplete,
  celebrate,
  onDismissCelebrate,
}) {
  const showCelebrate = done && celebrate;

  return (
    <div className="content">
      <Chicken
        emotion={emotion}
        bubble={done ? 'Great job! Ecoling is happy! 🍃' : `${greeting()} Let's help the planet together 🌱`}
        celebrate={done}
      />

      {showCelebrate ? (
        <div className="card celebrate-card">
          <div className="celebrate-label">You earned</div>
          <div className="celebrate-points">
            +{points} <span className="leaf-big">🍃</span>
          </div>
          {difficulty > 1 && (
            <div className="celebrate-bonus">Hard day bonus! 🔥 ×{difficulty}</div>
          )}
          <div className="streak-box">
            <div className="streak-box-label">Current Streak</div>
            <div className="streak-box-value">{streak} {streak === 1 ? 'day' : 'days'}</div>
            <StreakLeaves streak={streak} />
          </div>
          <button className="action-btn" onClick={onDismissCelebrate}>
            Back to Home
          </button>
        </div>
      ) : (
        <>
          <div className="card suggestion-card">
            <div className="card-title">Today's Suggestion</div>

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
              <span className="inline-leaf"> 🍃</span>
            </div>

            {difficulty > 1 && (
              <div className="difficulty-tag">🔥 Hard-weather day · +{points} 🍃 (×{difficulty})</div>
            )}

            <button
              className={`action-btn${done ? ' action-btn--done' : ''}`}
              onClick={onComplete}
              disabled={done}
            >
              {done ? 'Done for today ✓' : "I'll do it!"}
            </button>
          </div>

          <div className="stat-row">
            <div className="stat-pill">
              <span className="stat-value">🔥 {streak}</span>
              <span className="stat-label">day streak</span>
            </div>
            <div className="stat-pill">
              <span className="stat-value">🍃 {totalPoints}</span>
              <span className="stat-label">total impact</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
