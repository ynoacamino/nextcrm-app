

const SCALE = Number(__ENV.DURATION_SCALE || 1);

function min(m) {
  const scaled = Math.max(1, Math.round(m * SCALE));
  return `${scaled}m`;
}
function sec(s) {
  const scaled = Math.max(1, Math.round(s * SCALE));
  return `${scaled}s`;
}

export function baseline() {
  return {
    executor: "constant-vus",
    vus: 1,
    duration: min(5),
    tags: { profile: "baseline" },
  };
}

export function load(vus, durationMin) {
  return {
    executor: "constant-vus",
    vus,
    duration: min(durationMin),
    tags: { profile: "load" },
  };
}

export function stress(startVU, maxVU, durationMin) {
  const rampUp = Math.max(1, Math.round(durationMin * 0.35));
  const hold = Math.max(1, Math.round(durationMin * 0.4));
  const rampDown = Math.max(1, Math.round(durationMin * 0.25));
  return {
    executor: "ramping-vus",
    startVUs: startVU,
    stages: [
      { duration: min(rampUp), target: maxVU },
      { duration: min(hold), target: maxVU },
      { duration: min(rampDown), target: 0 },
    ],
    gracefulRampDown: sec(30),
    tags: { profile: "stress" },
  };
}

export function spike(baseVU, peakVU, holdMin) {
  return {
    executor: "ramping-vus",
    startVUs: baseVU,
    stages: [
      { duration: min(2), target: baseVU }, 
      { duration: sec(60), target: peakVU }, 
      { duration: min(holdMin), target: peakVU }, 
      { duration: sec(30), target: baseVU }, 
      { duration: min(2), target: baseVU }, 
      { duration: sec(30), target: 0 },
    ],
    gracefulRampDown: sec(20),
    tags: { profile: "spike" },
  };
}

export function soak(vus, hours) {
  return {
    executor: "constant-vus",
    vus,
    duration: min(hours * 60),
    tags: { profile: "soak" },
  };
}
