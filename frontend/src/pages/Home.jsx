import Chicken from '../components/Chicken';
import '../css/home.css';

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning!';
  if (hour < 18) return 'Good afternoon!';
  return 'Good evening!';
}

function StreakLeaves({ streak }) {
  return <div className="streak-leaves">{Array.from({ length: 7 }, (_, index) => <span key={index} className={index < Math.min(streak, 7) ? 'leaf-on' : 'leaf-off'}>🍃</span>)}</div>;
}

function LiveQuestCard({ quest, weather, busy, onStartChallenge }) {
  const temperature = weather?.observations?.temperature?.value;
  const forecast = weather?.forecast;
  return (
    <div className="card suggestion-card">
      <div className="card-title">Current two-hour choices</div>
      <div className="weather-info">
        <span className="weather-icon">🌤️</span>
        <span className="weather-item">{temperature ?? '—'}°C</span>
        <span className="weather-divider">·</span>
        <span className="weather-item">{forecast?.condition || 'Live weather'}</span>
        <span className="weather-divider">·</span>
        <span className="weather-item">📍 {forecast?.area || 'Singapore'}</span>
      </div>
      <div className="quest-choice-list">
        {quest.options.map((option) => {
          const selected = quest.selected_quest_key === option.id;
          return (
            <article className={`quest-choice${selected ? ' quest-choice--selected' : ''}`} key={option.id}>
              <div className="quest-choice-head"><strong>{option.title}</strong><span className={`quest-difficulty quest-difficulty--${option.difficulty}`}>{option.difficulty}</span></div>
              <p>{option.description}</p>
              <small>{option.reason}</small>
              {option.action_window && <div className="quest-window"><strong>Best time:</strong> {option.action_window.label}</div>}
              <button className={`action-btn${quest.completed ? ' action-btn--done' : ''}`} disabled={busy || quest.completed} onClick={() => onStartChallenge(option)}>
                {selected ? 'Completed ✓' : quest.completed ? 'Other choice completed' : `I'll do this — snap proof (+${option.points} 🍃)`}
              </button>
            </article>
          );
        })}
      </div>
      <div className="slot-note">Refreshes at {new Date(quest.slot_end).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</div>
    </div>
  );
}

export default function Home({
  guest, weather, guestSuggestion, guestDifficulty, guestPoints, quest, areas, areaName,
  onAreaChange, done, emotion, streak, totalPoints, busy, error, onStartChallenge, celebration,
  onDismissCelebrate,
}) {
  return (
    <div className="content">
      <Chicken emotion={emotion} bubble={done ? 'Great job! Ecoling is happy! 🍃' : `${greeting()} Let's help the planet together 🌱`} celebrate={done} />
      {celebration ? (
        <div className="card celebrate-card">
          <div className="celebrate-label">You earned</div>
          <div className="celebrate-points">+{celebration.points} <span className="leaf-big">🍃</span></div>
          <div className="streak-box"><div className="streak-box-label">Current Streak</div><div className="streak-box-value">{streak} {streak === 1 ? 'day' : 'days'}</div><StreakLeaves streak={streak} /></div>
          <button className="action-btn" onClick={onDismissCelebrate}>Back to Home</button>
        </div>
      ) : guest ? (
        <div className="card suggestion-card">
          <div className="card-title">Demo suggestion</div>
          <div className="weather-info"><span>{weather.icon}</span><span>{weather.temp}°C · {guestSuggestion.label} · 📍 {weather.place}</span></div>
          <div className="suggestion-text">{guestSuggestion.summary}<br /><span className="suggestion-highlight">{guestSuggestion.action}</span></div>
          <button className={`action-btn${done ? ' action-btn--done' : ''}`} onClick={() => onStartChallenge()} disabled={done}>{done ? 'Done for today ✓' : `I'll do it — snap proof (+${guestPoints} 🍃)`}</button>
          <div className="offline-note">Guest progress stays on this device. Sign in for live weather and synced quests.</div>
        </div>
      ) : (
        <>
          <div className="card area-card">
            <label htmlFor="weather-area" className="card-title">Your Singapore area</label>
            <select id="weather-area" className="login-input" value={areaName} onChange={(event) => onAreaChange(event.target.value)}>
              <option value="">Choose an area…</option>
              {areas.map((area) => <option value={area.name} key={area.name}>{area.name}</option>)}
            </select>
          </div>
          {error && <div className="login-error">{error}</div>}
          {quest ? <LiveQuestCard quest={quest} weather={weather} busy={busy} onStartChallenge={onStartChallenge} /> : <div className="card empty-state">{areaName ? 'Creating weather-safe choices…' : 'Choose your area to receive live quests.'}</div>}
        </>
      )}
      <div className="stat-row"><div className="stat-pill"><span className="stat-value">🔥 {streak}</span><span className="stat-label">day streak</span></div><div className="stat-pill"><span className="stat-value">🍃 {totalPoints}</span><span className="stat-label">total gold</span></div></div>
    </div>
  );
}
