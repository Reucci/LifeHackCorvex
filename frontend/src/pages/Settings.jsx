import { useEffect, useState } from 'react';
import { loadPrefs, savePrefs } from '../utils/prefs';
import { notificationsSupported, requestNotificationPermission } from '../utils/notifications';

export default function Settings({ auth, prefs: serverPrefs, onPrefs, onLogout, onReset }) {
  const [prefs, setPrefs] = useState(() => serverPrefs || loadPrefs());
  const [savedTick, setSavedTick] = useState(false);

  useEffect(() => {
    if (serverPrefs) setPrefs(serverPrefs);
  }, [serverPrefs]);

  const update = async (patch) => {
    const next = auth?.guest ? savePrefs({ ...prefs, ...patch }) : { ...prefs, ...patch };
    setPrefs(next);
    await onPrefs?.(next);
    setSavedTick(true);
    setTimeout(() => setSavedTick(false), 1200);
  };

  const toggleQuestAlerts = async () => {
    const enabling = !prefs.reminders;
    if (enabling) {
      const permission = await requestNotificationPermission();
      if (permission !== 'granted') return;
    }
    await update({ reminders: enabling });
  };

  const handleReset = () => {
    if (window.confirm('Reset all progress? This clears your streak and history.')) {
      onReset();
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
            value={prefs.display_name ?? prefs.displayName ?? ''}
            onChange={(e) => update(auth?.guest ? { displayName: e.target.value } : { display_name: e.target.value })}
            maxLength={24}
          />
        </label>

        <label className="settings-field">
          <span className="settings-label">Ecoling name</span>
          <input
            className="login-input"
            type="text"
            value={prefs.ecoling_name ?? prefs.ecolingName ?? ''}
            onChange={(e) => update(auth?.guest ? { ecolingName: e.target.value } : { ecoling_name: e.target.value })}
            maxLength={24}
            placeholder="Name your companion"
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
          onClick={toggleQuestAlerts}
          type="button"
          disabled={!notificationsSupported()}
        >
          <span className="settings-label">New quest alerts (every 2 hours)</span>
          <span className={`switch${prefs.reminders ? ' switch--on' : ''}`}>
            <span className="switch-knob" />
          </span>
        </button>

        <button
          className="settings-toggle-row"
          onClick={() => update(auth?.guest
            ? { quietHours: !(prefs.quietHours ?? true) }
            : { quiet_hours: !(prefs.quiet_hours ?? true) })}
          type="button"
        >
          <span className="settings-label">Notifications off for quiet hours (10 PM–8 AM)</span>
          <span className={`switch${(prefs.quiet_hours ?? prefs.quietHours ?? true) ? ' switch--on' : ''}`}>
            <span className="switch-knob" />
          </span>
        </button>

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
