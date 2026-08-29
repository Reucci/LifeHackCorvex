import { useCallback, useEffect, useState } from 'react';
import { addFriend, getFriends, getLeaderboard, removeFriend } from '../utils/api';

function LeaderboardRow({ entry }) {
  const medal = entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`;
  return (
    <li className={`leaderboard-row${entry.is_current_user ? ' leaderboard-row--current' : ''}`}>
      <span className="leaderboard-rank">{medal}</span>
      <span className="leaderboard-user"><strong>{entry.username}</strong>{entry.is_current_user && <span className="leaderboard-you">You</span>}<small>🔥 {entry.daily_streak} day streak</small></span>
      <span className="leaderboard-gold">{entry.gold.toLocaleString()} 🍃</span>
    </li>
  );
}

export default function Leaderboard({ guest }) {
  const [scope, setScope] = useState('global');
  const [data, setData] = useState(null);
  const [friends, setFriends] = useState([]);
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (guest) return;
    setBusy(true); setError('');
    try {
      const [ranking, friendData] = await Promise.all([getLeaderboard(scope), getFriends()]);
      setData(ranking); setFriends(friendData.friends);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }, [guest, scope]);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async (event) => {
    event.preventDefault();
    if (!username.trim()) return;
    setBusy(true); setError('');
    try { await addFriend(username.trim()); setUsername(''); await load(); }
    catch (err) { setError(err.message); setBusy(false); }
  };

  const handleRemove = async (friendId) => {
    setBusy(true); setError('');
    try { await removeFriend(friendId); await load(); }
    catch (err) { setError(err.message); setBusy(false); }
  };

  if (guest) return <div className="content"><div className="card empty-state">Sign in to join the weekly leaderboards.</div></div>;
  const currentIsVisible = data?.entries.some((entry) => entry.is_current_user);
  return (
    <div className="content">
      <div className="leaderboard-tabs" role="tablist" aria-label="Leaderboard type">
        {['global', 'friends'].map((tab) => <button key={tab} role="tab" aria-selected={scope === tab} className={`leaderboard-tab${scope === tab ? ' leaderboard-tab--active' : ''}`} onClick={() => setScope(tab)}>{tab === 'global' ? '🌍 Global' : '👥 Friends'}</button>)}
      </div>
      {data && <div className="card leaderboard-summary"><span>This week · {data.week_start}–{data.week_end}</span><strong>#{data.current_user.rank}</strong><small>out of {data.total_users} {scope === 'global' ? 'Ecolings' : 'friends'}</small></div>}
      {scope === 'friends' && <div className="card friend-manager">
        <form className="friend-add" onSubmit={handleAdd}><label htmlFor="friend-username" className="card-title">Add a friend by username</label><div><input id="friend-username" className="login-input" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" /><button className="action-btn" disabled={busy}>Add</button></div></form>
        {friends.length > 0 && <ul className="friend-list">{friends.map((friend) => <li key={friend.user_id}><span>{friend.username}</span><button className="link-btn" onClick={() => handleRemove(friend.user_id)} disabled={busy}>Remove</button></li>)}</ul>}
      </div>}
      {error && <div className="login-error">{error}</div>}
      {busy && !data && <div className="card empty-state">Loading rankings…</div>}
      {data && <ol className="card leaderboard-list">{data.entries.map((entry) => <LeaderboardRow key={entry.user_id} entry={entry} />)}{!currentIsVisible && <><li className="leaderboard-divider">Your position</li><LeaderboardRow entry={data.current_user} /></>}</ol>}
    </div>
  );
}
