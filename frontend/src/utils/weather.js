// Live weather via Open-Meteo (free, key-less, CORS-friendly). We ask the browser
// for the user's location; if that is denied or the request fails we fall back to
// MOCK_WEATHER so the rest of the app keeps working unchanged.

export const MOCK_WEATHER = {
  temp: 18,
  humidity: 55,
  windSpeed: 6,
  isRaining: false,
  condition: 'Chilly & dry',
  icon: '🌤️',
  place: 'Singapore',
  sky: 'partly', // one of: sunny | partly | overcast | rainy  -> drives the background
  offline: true,
};

// WMO weather codes -> the four background "moods" we have artwork for.
// https://open-meteo.com/en/docs  (weather_code table)
function skyFromCode(code) {
  if (code === 0 || code === 1) return 'sunny';
  if (code === 2) return 'partly';
  if (code === 3 || code === 45 || code === 48) return 'overcast';
  if (code >= 71 && code <= 77) return 'overcast'; // snow -> use the grey scene
  if (code >= 85 && code <= 86) return 'overcast'; // snow showers
  return 'rainy'; // 51-67 drizzle/rain, 80-82 showers, 95-99 thunderstorm
}

const CODE_TEXT = {
  0: ['Clear sky', '☀️'],
  1: ['Mainly clear', '🌤️'],
  2: ['Partly cloudy', '⛅'],
  3: ['Overcast', '☁️'],
  45: ['Foggy', '🌫️'],
  48: ['Freezing fog', '🌫️'],
  51: ['Light drizzle', '🌦️'],
  53: ['Drizzle', '🌦️'],
  55: ['Heavy drizzle', '🌧️'],
  61: ['Light rain', '🌦️'],
  63: ['Rain', '🌧️'],
  65: ['Heavy rain', '🌧️'],
  71: ['Light snow', '🌨️'],
  73: ['Snow', '🌨️'],
  75: ['Heavy snow', '❄️'],
  80: ['Rain showers', '🌦️'],
  81: ['Rain showers', '🌧️'],
  82: ['Violent showers', '⛈️'],
  95: ['Thunderstorm', '⛈️'],
  96: ['Thunderstorm', '⛈️'],
  99: ['Thunderstorm', '⛈️'],
};

function describeCode(code) {
  return CODE_TEXT[code] || ['Current weather', '🌡️'];
}

function getPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation unavailable'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      timeout: 8000,
      maximumAge: 30 * 60 * 1000,
    });
  });
}

// Rough location from IP — no permission prompt. Used when geolocation is denied.
async function getPositionByIP() {
  const res = await fetch('https://ipapi.co/json/');
  if (!res.ok) throw new Error(`IP lookup ${res.status}`);
  const d = await res.json();
  if (typeof d.latitude !== 'number') throw new Error('IP lookup: no coords');
  return { coords: { latitude: d.latitude, longitude: d.longitude } };
}

// Fetches live weather for the user's location. Always resolves — never throws —
// so callers can do `getWeather().then(setWeather)` without a catch.
export async function getWeather() {
  try {
    let coords;
    try {
      ({ coords } = await getPosition());
    } catch {
      ({ coords } = await getPositionByIP());
    }
    const { latitude, longitude } = coords;
    const url =
      'https://api.open-meteo.com/v1/forecast' +
      `?latitude=${latitude.toFixed(3)}&longitude=${longitude.toFixed(3)}` +
      '&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code' +
      '&wind_speed_unit=ms&timezone=auto';

    const res = await fetch(url);
    if (!res.ok) throw new Error(`Weather API ${res.status}`);
    const data = await res.json();
    const c = data.current || {};
    const [condition, icon] = describeCode(c.weather_code);

    return {
      temp: Math.round(c.temperature_2m),
      humidity: Math.round(c.relative_humidity_2m),
      windSpeed: Math.round(c.wind_speed_10m),
      isRaining: (c.precipitation ?? 0) > 0,
      condition,
      icon,
      place: (data.timezone || '').split('/').pop().replace(/_/g, ' ') || 'Your area',
      sky: skyFromCode(c.weather_code),
      offline: false,
    };
  } catch {
    return { ...MOCK_WEATHER };
  }
}

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
