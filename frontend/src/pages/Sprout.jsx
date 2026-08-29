import Chicken from '../components/Chicken';
import { careEcolingMessage } from '../utils/ecolingMessages';

export default function Sprout({ ecolingName, ecolingMessage, mood, streak, done }) {
  const emotion = mood?.emotion || 'normal';
  const currentMood = mood || { label: 'Doing okay', pct: 50 };
  const name = ecolingName || 'Your Ecoling';
  const bubble = ecolingMessage || careEcolingMessage({ name, emotion, streak });
  return (
    <div className="content">
        <Chicken emotion={emotion} bubble={bubble} celebrate={emotion === 'happy' || emotion === 'excited'} />

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
