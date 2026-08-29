import Chicken from '../components/Chicken';
import { weekPoints, savings } from '../utils/store';

export default function Stats({ state, serverBacked = false }) {
  const week = serverBacked ? state.weekPoints : weekPoints(state);
  const localSavings = savings(state);
  const kwh = serverBacked ? state.estimatedKwh : localSavings.kwh;
  const co2 = serverBacked ? state.estimatedCo2 : localSavings.co2;

  return (
    <div className="content">
        <div className="card impact-hero">
          <div className="impact-hero-body">
            <div className="card-title">This Week</div>
            <div className="impact-big">{week} <span className="impact-unit">pts</span></div>
            <div className="impact-sub">Keep it up! 🍃</div>
          </div>
          <Chicken emotion="excited" />
        </div>

        <div className="card impact-row">
          <div>
            <div className="impact-row-value">{state.totalPoints.toLocaleString()} pts</div>
            <div className="impact-row-label">Total Impact · since you started</div>
          </div>
        </div>

        <div className="card impact-row">
          <div>
            <div className="impact-row-value">🔥 {state.longestStreak} days</div>
            <div className="impact-row-label">Longest streak</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">You've helped save</div>
          <div className="savings-grid">
            <div className="savings-box">
              <div className="savings-value">⚡ {kwh} kWh</div>
              <div className="savings-label">Energy</div>
            </div>
            <div className="savings-box">
              <div className="savings-value">☁️ {co2} kg</div>
              <div className="savings-label">CO₂</div>
            </div>
          </div>
          <div className="savings-note">Rough estimate from {state.log.length} logged actions.</div>
        </div>
    </div>
  );
}
