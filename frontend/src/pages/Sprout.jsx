import Chicken from '../components/Chicken';

const MOOD = {
  excited: { label: 'Full of energy!', pct: 100 },
  happy: { label: 'Happy and cared for', pct: 80 },
  normal: { label: 'Doing okay', pct: 50 },
  sad: { label: 'Feeling neglected', pct: 20 },
};

export default function Sprout({ emotion, streak, done }) {
  const mood = MOOD[emotion] || MOOD.normal;
  return (
    <div className="content">
        <Chicken emotion={emotion} bubble="Thank you for taking care of me! ❤️" />

        <div className="card">
          <div className="mood-line">
            <span className="card-title">Mood</span>
            <span className="mood-heart">❤️</span>
          </div>
          <div className="mood-bar">
            <div className="mood-fill" style={{ width: `${mood.pct}%` }} />
          </div>
          <div className="mood-label">{mood.label}</div>
        </div>

        <div className="card">
          <div className="card-title">About Ecoling</div>
          <p className="about-text">
            Ecoling loves fresh air and sunny days. Ecoling thrives when you complete
            the daily weather suggestion and keep your streak going.
          </p>
          <p className="about-text">
            {done
              ? "You checked in today — Ecoling can feel it. 💚"
              : "Ecoling is waiting for today's action. 🌱"}
            {streak > 0 && ` Current streak: ${streak} day${streak === 1 ? '' : 's'}.`}
          </p>
        </div>
    </div>
  );
}
