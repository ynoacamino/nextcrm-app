// PRSTRESS — Saturación de creación de actividades (escritura con múltiples inserciones).
//
// META:
//   cases:    PRSTRESS-006
//   endpoint: Server Action createActivity (POST Next-Action)
//   objetivo: punto de saturación de la creación de actividades con vínculos
//             (5 → 30 VU); cada creación implica varias inserciones en transacción.
//   umbral:   escritura STRESS — p95 < 2.5s, p99 < 4s, error < 2% (Diseño §4.3)
//   carga:    rampa 5 → 30 VU, 15 min
//   requiere: pool de accounts en data/entity-ids.json (clave "accounts").

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newActivityArgs } from "../../lib/data.js";

const accounts = idPool("accounts");

export const options = {
  scenarios: { activities_stress: stress(5, 30, 15) },
  thresholds: buildThresholds({ write: PRESETS.stressWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRSTRESS", entity: "activities" };
  const accountId = pick(accounts);
  const links = accountId ? [{ entityType: "account", entityId: accountId }] : [];

  group("PRSTRESS-006 creación de actividad bajo saturación", () => {
    record(
      invokeServerAction("createActivity", ROUTES.accounts, newActivityArgs(links), data.cookie, t),
      "write",
    );
  });

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-activities");
