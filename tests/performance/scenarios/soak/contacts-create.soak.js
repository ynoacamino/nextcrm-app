

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { soak } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

const HOURS = Number(__ENV.SOAK_HOURS || 4);
const VUS = Number(__ENV.SOAK_VUS || 20);

export const options = {
  scenarios: { contacts_create_soak: soak(VUS, HOURS) },
  thresholds: buildThresholds({ write: PRESETS.soak }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "write", suite: "PRSOAK", entity: "contacts" };
  group("PRSOAK-002 creación de contacto sostenida", () => {
    record(
      invokeServerAction("createContact", ROUTES.contacts, newContactArgs(), data.cookie, t),
      "write",
    );
  });
  sleep(1);
}

export const handleSummary = makeHandleSummary("PRSOAK-contacts-create");
