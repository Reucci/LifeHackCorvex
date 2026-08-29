// FRONTEND MOCK — no weather API yet. Swap `MOCK_WEATHER` / `getWeather()` for a
// real fetch later; the rule table below stays exactly the same.

export const MOCK_WEATHER = {
  temp: 18,
  humidity: 55,
  windSpeed: 6,
  isRaining: false,
  condition: 'Chilly & dry',
  icon: '🌤️',
  place: 'Singapore',
};

// --- The rule table: conditions -> one specific smart action --------------
const RULES = [
  {
    id: 'heat-blinds',
    test: (w) => w.temp >= 30 && w.humidity >= 65,
    label: 'Hot & humid',
    summary: "It's hot and humid today.",
    action: 'Close the blinds early to keep rooms cool before you reach for the AC.',
    habit: 'Closed the blinds',
    icon: '🌡️',
  },
  {
    id: 'cold-layer',
    test: (w) => w.temp <= 8,
    label: 'Cold snap',
    summary: "It's genuinely cold today.",
    action: 'Add a layer and drop the heating by 2°C.',
    habit: 'Turned the heating down',
    icon: '🧣',
  },
  {
    id: 'chilly-window',
    test: (w) => w.temp > 8 && w.temp <= 20 && w.humidity < 70 && !w.isRaining,
    label: 'Chilly & dry',
    summary: "It's chilly and dry today.",
    action: 'Try opening a window instead of using the AC.',
    habit: 'Opened a window instead of AC',
    icon: '🪟',
  },
  {
    id: 'sunny-linedry',
    test: (w) => !w.isRaining && w.windSpeed >= 8 && w.temp >= 18,
    label: 'Sunny & breezy',
    summary: "It's sunny with a good breeze.",
    action: 'Line-dry your laundry today instead of running the dryer.',
    habit: 'Line-dried laundry',
    icon: '👕',
  },
  {
    id: 'mild-walk',
    test: (w) => !w.isRaining && w.temp >= 12 && w.temp <= 26,
    label: 'Mild & clear',
    summary: "It's mild and clear — great for being outside.",
    action: 'Walk or bike for one trip you would normally drive.',
    habit: 'Walked/biked instead of driving',
    icon: '🚲',
  },
  {
    id: 'rainy-batch',
    test: (w) => w.isRaining,
    label: 'Rainy',
    summary: "It's a wet one today.",
    action: 'Batch your cooking — use the oven once for two meals.',
    habit: 'Batch-cooked to save energy',
    icon: '🍲',
  },
];

const DEFAULT_RULE = {
  id: 'default-standby',
  label: 'Calm day',
  summary: 'Nothing extreme in the forecast.',
  action: 'Unplug one device on standby you are not using right now.',
  habit: 'Unplugged a standby device',
  icon: '🔌',
};

export function pickSuggestion(weather = MOCK_WEATHER) {
  const rule = RULES.find((r) => r.test(weather)) || DEFAULT_RULE;
  return {
    id: rule.id,
    label: rule.label,
    summary: rule.summary,
    action: rule.action,
    habit: rule.habit,
    icon: rule.icon,
  };
}

// Difficulty multiplier — a hard day is worth more.
export function difficultyFor(weather = MOCK_WEATHER) {
  if (weather.temp >= 32 || weather.temp <= 5) return 2;
  if (weather.temp >= 30 || weather.temp <= 10) return 1.5;
  if (weather.isRaining) return 1.3;
  return 1;
}
