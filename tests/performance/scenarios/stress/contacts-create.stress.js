// PRSTRESS — Saturación de creación de contactos (escritura bajo carga creciente).
//
// META:
//   cases:    PRSTRESS-002, PRSTRESS-008
//   endpoint: Server Action createContact (POST Next-Action)
//   objetivo: punto de saturación de la creación de contactos (10 → 100 VU) y
//             tasa de error durante el aumento de carga.
//   umbral:   escritura STRESS — p95 < 2.5s, p99 < 4s, error < 2% (Diseño §4.3)
//   carga:    rampa 10 → 100 VU, 15 min

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

export const options = {
  scenarios: { contacts_create_stress: stress(10, 100, 15) },
  thresholds: buildThresholds({ write: PRESETS.stressWrite }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRSTRESS", entity: "contacts" };

  group("PRSTRESS-002/008 creación de contacto bajo saturación", () => {
    record(
      invokeServerAction("createContact", ROUTES.contacts, newContactArgs(), data.cookie, t),
      "write",
    );
  });

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-contacts-create");
