import { useState } from 'react';

const WEEKDAYS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function ymd(y, m, d) {
  return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}

function prettyDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

export default function History({ state }) {
  const now = new Date();
  const todayStr = ymd(now.getFullYear(), now.getMonth(), now.getDate());
  const [cursor, setCursor] = useState({ y: now.getFullYear(), m: now.getMonth() });
  const [selected, setSelected] = useState(null);

  const completed = new Set(state.completedDates);

  const firstDay = new Date(cursor.y, cursor.m, 1);
  const startOffset = (firstDay.getDay() + 6) % 7; // Monday-first
  const daysInMonth = new Date(cursor.y, cursor.m + 1, 0).getDate();

  const cells = [];
  for (let i = 0; i < startOffset; i += 1) cells.push(null);
  for (let d = 1; d <= daysInMonth; d += 1) cells.push(d);

  const prevMonth = () =>
    setCursor((c) => (c.m === 0 ? { y: c.y - 1, m: 11 } : { y: c.y, m: c.m - 1 }));
  const nextMonth = () =>
    setCursor((c) => (c.m === 11 ? { y: c.y + 1, m: 0 } : { y: c.y, m: c.m + 1 }));

  const visible = selected
    ? state.log.filter((e) => e.date === selected)
    : state.log;

  return (
    <div className="content">
        <div className="card calendar-card">
          <div className="calendar-head">
            <button className="cal-nav" onClick={prevMonth}>‹</button>
            <span className="cal-month">{MONTHS[cursor.m]} {cursor.y}</span>
            <button className="cal-nav" onClick={nextMonth}>›</button>
          </div>

          <div className="calendar-grid calendar-weekdays">
            {WEEKDAYS.map((w, i) => (
              <span key={i} className="cal-weekday">{w}</span>
            ))}
          </div>

          <div className="calendar-grid">
            {cells.map((d, i) => {
              if (d === null) return <span key={`b${i}`} className="cal-cell cal-cell--empty" />;
              const iso = ymd(cursor.y, cursor.m, d);
              const isToday = iso === todayStr;
              const isDone = completed.has(iso);
              const isSelected = iso === selected;
              return (
                <button
                  key={iso}
                  className={
                    'cal-cell' +
                    (isToday ? ' cal-cell--today' : '') +
                    (isSelected ? ' cal-cell--selected' : '')
                  }
                  onClick={() => setSelected(isSelected ? null : iso)}
                >
                  <span className="cal-day">{d}</span>
                  {isDone && <span className="cal-leaf">🍃</span>}
                </button>
              );
            })}
          </div>
        </div>

        <div className="log-header">
          <span>{selected ? prettyDate(selected) : 'Recent actions'}</span>
          {selected && (
            <button className="link-btn" onClick={() => setSelected(null)}>Show all</button>
          )}
        </div>

        {visible.length === 0 && (
          <div className="empty-state">No action logged on this day.</div>
        )}

        <div className="history-list">
          {visible.map((entry, i) => (
            <div className="history-item" key={`${entry.date}-${i}`}>
              <div className="history-icon">{entry.weather?.icon || '🍃'}</div>
              <div className="history-body">
                <div className="history-habit">{entry.habit}</div>
                <div className="history-meta">
                  {prettyDate(entry.date)}
                  {entry.weather ? ` · ${entry.weather.condition} ${entry.weather.temp}°C` : ''}
                  {entry.difficulty > 1 ? ` · 🔥 ×${entry.difficulty}` : ''}
                </div>
              </div>
              <div className="history-points">+{entry.points} 🍃</div>
            </div>
          ))}
        </div>
    </div>
  );
}
