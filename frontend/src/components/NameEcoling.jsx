import { useState } from 'react';

export default function NameEcoling({ onSave, onDismiss }) {
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed.length < 2) {
      setError('Choose a name with at least 2 characters.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await onSave(trimmed);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="name-ecoling-backdrop" role="presentation">
      <form className="card name-ecoling-card" onSubmit={submit} role="dialog" aria-modal="true" aria-labelledby="name-ecoling-title">
        <div className="name-ecoling-avatar">🐥</div>
        <div className="card-title" id="name-ecoling-title">Name your Ecoling</div>
        <p>Your new companion needs a name. You can change it later in Settings.</p>
        <label className="login-field">
          <span className="login-label">Ecoling name</span>
          <input
            className="login-input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={24}
            placeholder="e.g. Sprig"
            autoFocus
          />
        </label>
        {error && <div className="login-error">{error}</div>}
        <button className="action-btn" type="submit" disabled={busy}>{busy ? 'Saving…' : 'Meet my Ecoling'}</button>
        <button className="ghost-btn" type="button" onClick={onDismiss} disabled={busy}>Maybe later</button>
      </form>
    </div>
  );
}
