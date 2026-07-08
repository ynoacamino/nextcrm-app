// PRSPIKE — Pico de tráfico sobre la creación de contactos (escritura).
//
// META:
//   cases:    PRSPIKE-002, PRSPIKE-008
//   endpoint: Server Action createContact (POST Next-Action)
//   objetivo: verificar ausencia de errores 5xx y medir la tasa de error de
//             escritura ante un pico repentino (10 → 80 VU en 1 min).
//   umbral:   SPIKE — p95 < 2s, p99 < 3s, error < 2% (Diseño §4.3)
//   carga:    10 → 80 VU en 1 min, sostenido 5 min

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { spike } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

export const options = {
  scenarios: { contacts_create_spike: spike(10, 80, 5) },
  thresholds: buildThresholds({ write: PRESETS.spike }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRSPIKE", entity: "contacts" };
  group("PRSPIKE-002/008 creación de contacto durante pico", () => {
    record(
      invokeServerAction("createContact", ROUTES.contacts, newContactArgs(), data.cookie, t),
      "write",
    );
  });
  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSPIKE-contacts-create");
