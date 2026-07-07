// Perfiles de carga reutilizables (Diseño §4.1 / Plan §5.1).
//
// Todos usan `ramping-vus` salvo el perfil de carga estable, que usa
// `constant-vus`. Las duraciones se pueden acortar para pruebas de humo con
// -e DURATION_SCALE=0.1 (útil en CI y validación local).

const SCALE = Number(__ENV.DURATION_SCALE || 1);

function min(m) {
  const scaled = Math.max(1, Math.round(m * SCALE));
  return `${scaled}m`;
}
function sec(s) {
  const scaled = Math.max(1, Math.round(s * SCALE));
  return `${scaled}s`;
}

// Nivel 0 — Baseline / humo: 1 VU, 5 min (§4.1).
export function baseline() {
  return {
    executor: "constant-vus",
    vus: 1,
    duration: min(5),
    tags: { profile: "baseline" },
  };
}

// Nivel 1 — LOAD: carga estable de `vus` durante `durationMin` minutos.
// Lecturas 50 VU, escrituras 20 VU (§4.1).
export function load(vus, durationMin) {
  return {
    executor: "constant-vus",
    vus,
    duration: min(durationMin),
    tags: { profile: "load" },
  };
}

// Nivel 2 — STRESS: rampa progresiva de `startVU` hasta `maxVU` y regreso,
// para localizar el punto de saturación (§4.1).
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

// Nivel 3 — SPIKE: pico repentino de `baseVU` → `peakVU` en 1 min, sostenido,
// y caída, midiendo también la recuperación (§4.1 / §5.3).
export function spike(baseVU, peakVU, holdMin) {
  return {
    executor: "ramping-vus",
    startVUs: baseVU,
    stages: [
      { duration: min(2), target: baseVU }, // calentamiento
      { duration: sec(60), target: peakVU }, // pico repentino (1 min)
      { duration: min(holdMin), target: peakVU }, // sostenido
      { duration: sec(30), target: baseVU }, // caída
      { duration: min(2), target: baseVU }, // ventana de recuperación
      { duration: sec(30), target: 0 },
    ],
    gracefulRampDown: sec(20),
    tags: { profile: "spike" },
  };
}

// Nivel 4 — SOAK: carga sostenida de `vus` durante `hours` horas (§4.1).
// La duración por defecto es de 4 h; usar -e DURATION_SCALE para acortar.
export function soak(vus, hours) {
  return {
    executor: "constant-vus",
    vus,
    duration: min(hours * 60),
    tags: { profile: "soak" },
  };
}
