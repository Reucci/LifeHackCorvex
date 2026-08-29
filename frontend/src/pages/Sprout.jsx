import Chicken from '../components/Chicken';

export default function Sprout({ ecolingName, mood, streak, done }) {
  const emotion = mood?.emotion || 'normal';
  const currentMood = mood || { label: 'Doing okay', pct: 50 };
  const name = ecolingName || 'Your Ecoling';
  return (
    <div className="content">
        <Chicken emotion={emotion} bubble={`Thank you for taking care of me! Love, ${name} ❤️`} celebrate />

        <div className="card">
          <div className="mood-line">
            <span className="card-title">Mood</span>
            <span className="mood-heart">❤️</span>
          </div>
          <div className="mood-bar">
            <div className="mood-fill" style={{ width: `${currentMood.pct}%` }} />
          </div>
          <div className="mood-label">{currentMood.label}</div>
        </div>

        <div className="card">
          <div className="card-title">About {name}</div>
          <p className="about-text">
            {name} loves fresh air and sunny days. {name} thrives when you complete
            the daily weather suggestion and keep your streak going.
          </p>
          <p className="about-text">
            {done
              ? `You checked in today — ${name} can feel it. 💚`
              : `${name} is waiting for today's action. 🌱`}
            {streak > 0 && ` Current streak: ${streak} day${streak === 1 ? '' : 's'}.`}
          </p>
        </div>
    </div>
  );
}
