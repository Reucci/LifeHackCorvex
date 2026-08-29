import { useState } from 'react';
import { loadPrefs, savePrefs } from '../utils/prefs';
import { resetState } from '../utils/store';

export default function Settings({ auth, onPrefs, onLogout }) {
  const [prefs, setPrefs] = useState(loadPrefs);
  const [savedTick, setSavedTick] = useState(false);

  const update = (patch) => {
    const next = savePrefs({ ...prefs, ...patch });
    setPrefs(next);
    onPrefs?.(next);
    setSavedTick(true);
    setTimeout(() => setSavedTick(false), 1200);
  };

  const handleReset = () => {
    if (window.confirm('Reset all progress? This clears your streak and history.')) {
      resetState();
      window.location.reload();
    }
  };

  return (
    <div className="content">
      <div className="card settings-group">
        <div className="card-title">Profile</div>

        <label className="settings-field">
          <span className="settings-label">Display name</span>
          <input
            className="login-input"
            type="text"
            value={prefs.displayName}
            onChange={(e) => update({ displayName: e.target.value })}
            maxLength={24}
          />
        </label>

        <div className="settings-row">
          <span className="settings-label">Account</span>
          <span className="settings-value">
            {auth?.guest ? 'Guest' : auth?.user?.username || '—'}
          </span>
        </div>
      </div>

      <div className="card settings-group">
        <div className="card-title">Reminders</div>

        <button
          className="settings-toggle-row"
          onClick={() => update({ reminders: !prefs.reminders })}
          type="button"
        >
          <span className="settings-label">Daily reminder</span>
          <span className={`switch${prefs.reminders ? ' switch--on' : ''}`}>
            <span className="switch-knob" />
          </span>
        </button>

        {prefs.reminders && (
          <label className="settings-field">
            <span className="settings-label">Reminder time</span>
            <input
              className="login-input"
              type="time"
              value={prefs.reminderTime}
              onChange={(e) => update({ reminderTime: e.target.value })}
            />
          </label>
        )}

        <button
          className="settings-toggle-row"
          onClick={() => update({ sound: !prefs.sound })}
          type="button"
        >
          <span className="settings-label">Sound effects</span>
          <span className={`switch${prefs.sound ? ' switch--on' : ''}`}>
            <span className="switch-knob" />
          </span>
        </button>
      </div>

      <div className="card settings-group">
        <div className="card-title">Units</div>
        <div className="settings-segment">
          {['metric', 'imperial'].map((u) => (
            <button
              key={u}
              type="button"
              className={`settings-seg${prefs.units === u ? ' settings-seg--active' : ''}`}
              onClick={() => update({ units: u })}
            >
              {u === 'metric' ? '°C · kg' : '°F · lb'}
            </button>
          ))}
        </div>
      </div>

      {savedTick && <div className="settings-saved">Saved ✓</div>}

      <button className="ghost-btn" type="button" onClick={onLogout}>
        Log out
      </button>
      <button className="ghost-btn settings-danger" type="button" onClick={handleReset}>
        Reset progress
      </button>

      <p className="settings-version">Ecolings · prototype build</p>
    </div>
  );
}
