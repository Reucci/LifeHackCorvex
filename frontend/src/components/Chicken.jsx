// Image files on disk have mixed casing — map emotion -> actual filename.
const IMG = {
  normal: 'normal',
  happy: 'Happy',
  excited: 'Excited',
  sad: 'sad',
};

export default function Chicken({ emotion = 'normal', bubble }) {
  const file = IMG[emotion] || 'normal';
  return (
    <div className="chicken-block">
      {bubble && <div className="speech-bubble">{bubble}</div>}
      <div className={`chicken-scene chicken--${emotion}`}>
        <img
          src={`/images/${file}.png`}
          alt={`Ecoling looking ${emotion}`}
          className="chicken-image"
        />
      </div>
    </div>
  );
}
