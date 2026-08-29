function dailySeed(extra = '') {
  const now = new Date();
  return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}-${extra}`;
}

function pick(messages, seed) {
  let hash = 0;
  for (const character of dailySeed(seed)) hash = ((hash * 31) + character.charCodeAt(0)) >>> 0;
  return messages[hash % messages.length];
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export function homeEcolingMessage({ name, done, emotion, streak, questId }) {
  const ecoling = name || 'Your Ecoling';
  const seed = `${questId || 'no-quest'}-${emotion}-${done}-${streak}`;

  if (done) {
    return pick([
      `${ecoling} is doing a tiny victory dance! 🍃`,
      `We did something good today. I'm proud of us! 💚`,
      `That quest made my leaves perk right up! 🌱`,
      `You did it! ${ecoling} looks extra cheerful now. ✨`,
    ], seed);
  }

  if (emotion === 'sad') {
    return pick([
      `I've missed our little eco adventures. Want to try one together? 🌱`,
      `A small action would really brighten my day. 💚`,
      `No pressure — even one tiny green choice helps me feel better. 🍃`,
      `${ecoling} could use some fresh energy. Shall we pick a quest?`,
    ], seed);
  }

  if (emotion === 'excited') {
    return pick([
      `${streak} days together! I feel unstoppable! 🌟`,
      `Our streak has me buzzing with green energy! 🍃`,
      `${ecoling} is ready for another planet-saving adventure!`,
      `Look at us go! What shall we tackle next? 🌍`,
    ], seed);
  }

  return pick([
    `${greeting()}! Let's help the planet together. 🌱`,
    `${ecoling} is wondering which quest you'll choose today.`,
    `Every small choice adds up. Ready when you are! 🍃`,
    `${greeting()}! I saved you a spot on our next eco adventure.`,
  ], seed);
}

export function careEcolingMessage({ name, emotion, streak }) {
  const ecoling = name || 'Your Ecoling';
  const messages = {
    excited: [
      `I have so much energy! Is it the streak, or am I just happy to see you?`,
      `${streak} days strong — we make a brilliant team! ✨`,
      `I think my leaves grew a little today! 🌿`,
    ],
    happy: [
      `Thank you for taking care of me. I feel wonderful! ❤️`,
      `Today's quest was fun. Can we do another one tomorrow?`,
      `Being your Ecoling is a pretty great job. 💚`,
    ],
    sad: [
      `I've been a little quiet, but I'm glad you came to visit.`,
      `Could we do something small for the planet together?`,
      `I don't need much — just a little time with you. 🌱`,
    ],
    normal: [
      `Hello! I was just thinking about our next adventure.`,
      `${ecoling} reporting for eco duty! 🍃`,
      `It's nice to see you. How is your day going?`,
    ],
  };
  return pick(messages[emotion] || messages.normal, `${emotion}-${streak}`);
}
