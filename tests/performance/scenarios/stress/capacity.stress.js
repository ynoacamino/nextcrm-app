// PRSTRESS — Capacidad máxima de throughput y estabilidad de recursos.
//
// META:
//   cases:    PRSTRESS-011, PRSTRESS-012, PRSTRESS-013, PRSTRESS-016
//   endpoint: GET /crm/accounts (carga por tasa de llegada) — getAccounts
//   objetivo: empujar el sistema por TASA DE LLEGADA (RPS) en lugar de por VUs
//             para medir el throughput máximo sostenible (PRSTRESS-016) y
//             observar la estabilidad al ~80% de capacidad de conexiones de
//             PostgreSQL (011), CPU (012) y memoria (013) de la aplicación.
//   umbral:   lectura STRESS — p95 < 2s, error < 2% (Diseño §4.3)
//   carga:    rampa de 50 → 400 RPS (ajustable con -e TARGET_RPS).
//   nota:     las métricas de infraestructura (conexiones, CPU, memoria) se leen
//             de Prometheus/Grafana correlacionadas con la ventana de esta
//             ejecución (Diseño §4.4). k6 aporta el RPS efectivo y la latencia.

import { group } from "k6";
import { ROUTES } from "../../config/environment.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

const TARGET_RPS = Number(__ENV.TARGET_RPS || 400);
const SCALE = Number(__ENV.DURATION_SCALE || 1);
const m = (x) => `${Math.max(1, Math.round(x * SCALE))}m`;

export const options = {
  scenarios: {
    capacity_stress: {
      executor: "ramping-arrival-rate",
      startRate: 50,
      timeUnit: "1s",
      preAllocatedVUs: 100,
      maxVUs: 600,
      stages: [
        { duration: m(3), target: Math.round(TARGET_RPS * 0.25) },
        { duration: m(3), target: Math.round(TARGET_RPS * 0.5) },
        { duration: m(4), target: TARGET_RPS },
        { duration: m(3), target: TARGET_RPS },
        { duration: m(2), target: 0 },
      ],
      tags: { profile: "stress" },
    },
  },
  thresholds: buildThresholds({ read: PRESETS.stressRead }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "read", suite: "PRSTRESS", entity: "accounts" };
  group("PRSTRESS-016 throughput máximo (RPS)", () => {
    record(readPage(ROUTES.accounts, data.cookie, t), "read");
  });
}

export const handleSummary = makeHandleSummary("PRSTRESS-capacity");
