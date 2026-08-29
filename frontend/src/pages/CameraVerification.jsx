import { useEffect, useRef, useState } from 'react';
import Chicken from '../components/Chicken';
import '../css/camera-verification.css';

function inspectPhoto(canvas) {
  const context = canvas.getContext('2d', { willReadFrequently: true });
  const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
  let total = 0;
  let variance = 0;
  const pixels = data.length / 4;

  for (let index = 0; index < data.length; index += 4) {
    const brightness = (data[index] + data[index + 1] + data[index + 2]) / 3;
    total += brightness;
  }

  const average = total / pixels;
  for (let index = 0; index < data.length; index += 4) {
    const brightness = (data[index] + data[index + 1] + data[index + 2]) / 3;
    variance += (brightness - average) ** 2;
  }

  return {
    usable: average > 24 && average < 245 && Math.sqrt(variance / pixels) > 12,
  };
}

export default function CameraVerification({ task, onCheck, onVerified, onCancel }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraError, setCameraError] = useState('');
  const [photo, setPhoto] = useState(null);
  const [checking, setChecking] = useState(false);
  const [checkMessage, setCheckMessage] = useState('');
  const [manualConfirmation, setManualConfirmation] = useState(false);

  useEffect(() => {
    let active = true;
    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError('Camera access is not available in this browser.');
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        videoRef.current.srcObject = stream;
      } catch {
        setCameraError('Camera permission was not granted. Allow camera access and try again.');
      }
    }
    startCamera();
    return () => {
      active = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const takePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;
    const scale = Math.min(1, 1024 / video.videoWidth);
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    const result = inspectPhoto(canvas);
    setPhoto(canvas.toDataURL('image/jpeg', 0.88));
    setCheckMessage(result.usable ? 'Photo looks clear enough to review.' : 'This photo looks too dark, bright, or flat. Try again.');
  };

  const confirmPhoto = async () => {
    setChecking(true);
    setManualConfirmation(false);
    setCheckMessage('Checking your evidence securely…');
    try {
      const result = await onCheck(photo);
      setCheckMessage(result.reason);
      if (result.verdict === 'verified' && !result.safety_concern) {
        await onVerified();
      } else if (result.verdict === 'uncertain' && !result.safety_concern) {
        setManualConfirmation(true);
      }
    } catch (error) {
      setCheckMessage(`${error.message} You can confirm manually if you completed the quest.`);
      setManualConfirmation(true);
    } finally {
      setChecking(false);
    }
  };

  return (
    <main className="camera-page content">
      <div className="camera-heading">
        <button className="camera-back" onClick={onCancel} aria-label="Back to home">←</button>
        <h1>Verification</h1>
      </div>

      <section className="camera-card">
        <div className="camera-task-icon">{task.icon || '🌱'}</div>
        <p className="camera-task-label">Your task</p>
        <h2>{task.action}</h2>
        <p className="camera-instruction">Frame the result in your camera, then take a photo for a quick visual check.</p>
        <p className="camera-privacy">AI review sends this photo securely to OpenAI with response storage disabled. Choose manual confirmation below if you do not want to upload it.</p>

        <div className="camera-frame">
          {photo ? <img src={photo} alt="Captured task evidence" /> : <video ref={videoRef} autoPlay muted playsInline />}
          {!photo && <span className="camera-frame-guide" aria-hidden="true" />}
        </div>
        <canvas ref={canvasRef} className="camera-canvas" />

        {cameraError && <p className="camera-error">{cameraError}</p>}
        {checkMessage && <p className="camera-check">{checkMessage}</p>}

        {photo ? (
          <div className="camera-actions">
            <button className="ghost-btn" onClick={() => { setPhoto(null); setCheckMessage(''); setManualConfirmation(false); }}>Retake</button>
            <button className="action-btn" disabled={checking || checkMessage.includes('too dark')} onClick={confirmPhoto}>
              {checking ? 'Checking…' : 'Verify photo ✓'}
            </button>
          </div>
        ) : (
          <button className="action-btn camera-capture" disabled={Boolean(cameraError)} onClick={takePhoto}>Take photo</button>
        )}
        {manualConfirmation && (
          <button className="ghost-btn camera-manual-confirm" type="button" onClick={onVerified}>
            I confirm I completed this quest
          </button>
        )}
        {photo && !manualConfirmation && !checking && (
          <button
            className="link-btn camera-manual-option"
            type="button"
            onClick={() => {
              setCheckMessage('Your photo was not uploaded. Confirm completion honestly below.');
              setManualConfirmation(true);
            }}
          >
            Review manually instead — do not upload
          </button>
        )}
      </section>
      <Chicken
        emotion={photo ? 'excited' : 'normal'}
        bubble={photo ? 'Show me your proof! Is everything looking good? 🍃' : 'Show me your proof! I’m watching 👀'}
        celebrate={Boolean(photo)}
      />
    </main>
  );
}
