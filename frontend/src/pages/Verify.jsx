import { useCallback, useEffect, useRef, useState } from 'react';
import Chicken from '../components/Chicken';
import '../css/verify.css';

// Photo-proof flow: user picked a challenge, now they snap a shot of themselves
// doing it. `onSubmit(dataUrl)` returns a promise of
// { verified, reason, confidence, gold_earned } from the verifying bot.
const CAPTURE_WIDTH = 720;

export default function Verify({ challenge, onSubmit, onVerified, onCancel }) {
  const [phase, setPhase] = useState('camera'); // camera | preview | checking | result
  const [photo, setPhoto] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [camReady, setCamReady] = useState(false);

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const startCamera = useCallback(async () => {
    setError('');
    setCamReady(false);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('This device has no camera access — upload a photo instead.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setCamReady(true);
    } catch {
      setError('Camera permission was blocked — you can upload a photo instead.');
    }
  }, []);

  useEffect(() => {
    if (phase === 'camera') startCamera();
    return stopCamera;
  }, [phase, startCamera, stopCamera]);

  const acceptPhoto = (dataUrl) => {
    stopCamera();
    setPhoto(dataUrl);
    setError('');
    setPhase('preview');
  };

  const capture = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const scale = CAPTURE_WIDTH / video.videoWidth;
    const canvas = document.createElement('canvas');
    canvas.width = CAPTURE_WIDTH;
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    acceptPhoto(canvas.toDataURL('image/jpeg', 0.8));
  };

  const pickFile = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please choose an image file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => acceptPhoto(String(reader.result));
    reader.onerror = () => setError('That photo could not be read.');
    reader.readAsDataURL(file);
  };

  const retake = () => {
    setPhoto(null);
    setResult(null);
    setError('');
    setPhase('camera');
  };

  const submit = async () => {
    setPhase('checking');
    setError('');
    try {
      const outcome = await onSubmit(photo);
      setResult(outcome);
      setPhase('result');
    } catch (err) {
      setError(err.message || 'Could not reach the verifier. Try again.');
      setPhase('preview');
    }
  };

  return (
    <div className="content">
      <div className="card verify-challenge">
        <div className="card-title">Prove it: {challenge.title}</div>
        <div className="verify-challenge-desc">{challenge.description}</div>
        <span className="verify-challenge-points">Snap a photo to earn +{challenge.points} 🍃</span>
      </div>

      {phase === 'result' ? (
        <div className={`card verify-result${result.verified ? '' : ' verify-result--fail'}`}>
          <div className="verify-result-emoji">{result.verified ? '🎉' : '🤔'}</div>
          <div className="verify-result-title">
            {result.verified ? 'Verified!' : 'Not quite'}
          </div>
          <div className="verify-result-reason">{result.reason}</div>
          {result.verified ? (
            <button className="action-btn" onClick={() => onVerified(result)} style={{ marginTop: 16 }}>
              Collect +{result.gold_earned} 🍃
            </button>
          ) : (
            <div className="verify-actions" style={{ marginTop: 16 }}>
              <button className="action-btn" onClick={retake}>Take another photo</button>
              <button className="ghost-btn" onClick={onCancel}>Back to home</button>
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          {error && <div className="verify-error">{error}</div>}

          <div className="verify-stage">
            {phase === 'checking' && (
              <div className="verify-checking">
                <div className="verify-spinner" />
                <span>Checking your photo…</span>
              </div>
            )}
            {phase !== 'checking' && photo && <img src={photo} alt="Your proof" />}
            {phase === 'camera' && (
              <>
                <video ref={videoRef} playsInline muted />
                {!camReady && !error && (
                  <div className="verify-stage-hint">Starting camera…</div>
                )}
              </>
            )}
          </div>

          {phase === 'camera' && (
            <div className="verify-actions">
              <button className="action-btn" onClick={capture} disabled={!camReady}>
                📸 Take photo
              </button>
              <label className="verify-file-btn">
                Upload a photo instead
                <input type="file" accept="image/*" capture="environment" onChange={pickFile} />
              </label>
              <button className="ghost-btn" onClick={onCancel}>Cancel</button>
            </div>
          )}

          {phase === 'preview' && (
            <div className="verify-actions verify-actions--row">
              <button className="ghost-btn" onClick={retake}>Retake</button>
              <button className="action-btn" onClick={submit}>Submit proof</button>
            </div>
          )}
        </div>
      )}

      {phase !== 'result' && (
        <div className="chicken-block">
          <Chicken emotion="normal" bubble="Show me what you did and I'll check it! 🔍" />
        </div>
      )}
    </div>
  );
}
