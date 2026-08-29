import { useState } from 'react';
import { login, register, guestLogin } from '../utils/auth';

export default function Login({ onAuthed }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [offline, setOffline] = useState(false);

  const isRegister = mode === 'register';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setOffline(false);

    if (username.trim().length < 3) {
      setError('Username needs at least 3 characters.');
      return;
    }
    if (password.length < 8) {
      setError('Password needs at least 8 characters.');
      return;
    }

    setBusy(true);
    try {
      const fn = isRegister ? register : login;
      const auth = await fn({ username: username.trim(), password });
      onAuthed(auth);
    } catch (err) {
      if (err.offline) {
        setOffline(true);
        setError("Can't reach the server. You can continue as a guest.");
      } else {
        setError(err.message);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleGuest = () => {
    onAuthed(guestLogin(username.trim() || 'Leafy Friend'));
  };

  return (
    <div className="content login-content">
      <div className="login-brand">
        <div className="login-logo">🌱</div>
        <div className="login-title">Ecolings</div>
        <div className="login-tagline">Small daily habits for a greener planet.</div>
      </div>

      <div className="card login-card">
        <div className="login-tabs">
          <button
            className={`login-tab${!isRegister ? ' login-tab--active' : ''}`}
            onClick={() => { setMode('login'); setError(''); }}
            type="button"
          >
            Log in
          </button>
          <button
            className={`login-tab${isRegister ? ' login-tab--active' : ''}`}
            onClick={() => { setMode('register'); setError(''); }}
            type="button"
          >
            Sign up
          </button>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="login-field">
            <span className="login-label">Username</span>
            <input
              className="login-input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="leafy_friend"
            />
          </label>

          <label className="login-field">
            <span className="login-label">Password</span>
            <input
              className="login-input"
              type="password"
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
          </label>

          {error && <div className="login-error">{error}</div>}

          <button className="action-btn" type="submit" disabled={busy}>
            {busy ? 'One moment…' : isRegister ? 'Create account' : 'Log in'}
          </button>
        </form>

        <button className="ghost-btn login-guest" type="button" onClick={handleGuest}>
          {offline ? 'Continue as guest' : 'Skip for now — try the demo'}
        </button>
      </div>

      <p className="login-fineprint">
        {isRegister
          ? 'Already have an account? '
          : "Don't have an account? "}
        <button
          type="button"
          className="link-btn"
          onClick={() => setMode(isRegister ? 'login' : 'register')}
        >
          {isRegister ? 'Log in' : 'Sign up'}
        </button>
      </p>
    </div>
  );
}
