// Badge definitions — all derived from the local care-loop state.

import { savings } from './store';

export const BADGES = [
  {
    id: 'first-step',
    icon: '🌱',
    name: 'First Step',
    desc: 'Log your very first eco action.',
    progress: (s) => ({ have: s.log.length, need: 1 }),
  },
  {
    id: 'getting-started',
    icon: '🍃',
    name: 'Getting Started',
    desc: 'Reach 100 total points.',
    progress: (s) => ({ have: s.totalPoints, need: 100 }),
  },
  {
    id: 'level-two',
    icon: '⭐',
    name: 'Level Up',
    desc: 'Reach Level 2 (250 points).',
    progress: (s) => ({ have: s.totalPoints, need: 250 }),
  },
  {
    id: 'week-warrior',
    icon: '🔥',
    name: 'Week Warrior',
    desc: 'Keep a 7-day streak going.',
    progress: (s) => ({ have: Math.max(s.streak, s.longestStreak || 0), need: 7 }),
  },
  {
    id: 'hot-streak',
    icon: '💥',
    name: 'Hot Streak',
    desc: 'Hit a 14-day streak.',
    progress: (s) => ({ have: s.longestStreak || 0, need: 14 }),
  },
  {
    id: 'dedicated',
    icon: '📅',
    name: 'Dedicated',
    desc: 'Complete an action on 10 different days.',
    progress: (s) => ({ have: s.completedDates.length, need: 10 }),
  },
  {
    id: 'rain-or-shine',
    icon: '🌧️',
    name: 'Rain or Shine',
    desc: 'Complete an action in tough weather.',
    progress: (s) => ({
      have: s.log.some((e) => e.difficulty > 1) ? 1 : 0,
      need: 1,
    }),
  },
  {
    id: 'planet-protector',
    icon: '🌍',
    name: 'Planet Protector',
    desc: 'Save an estimated 5 kg of CO₂.',
    progress: (s) => ({ have: Number(savings(s).co2), need: 5 }),
  },
  {
    id: 'eco-hero',
    icon: '🏆',
    name: 'Eco Hero',
    desc: 'Reach 1,000 total points.',
    progress: (s) => ({ have: s.totalPoints, need: 1000 }),
  },
];

export function badgeStatus(state) {
  return BADGES.map((b) => {
    const { have, need } = b.progress(state);
    const clamped = Math.max(0, Math.min(have, need));
    return {
      ...b,
      have: clamped,
      need,
      earned: have >= need,
      pct: Math.round((clamped / need) * 100),
    };
  });
}

export function earnedCount(state) {
  return badgeStatus(state).filter((b) => b.earned).length;
}
