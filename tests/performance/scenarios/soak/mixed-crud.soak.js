

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { soak } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { newContactArgs } from "../../lib/data.js";

const HOURS = Number(__ENV.SOAK_HOURS || 4);
const VUS = Number(__ENV.SOAK_VUS || 5);

export const options = {
  scenarios: { mixed_crud_soak: soak(VUS, HOURS) },
  thresholds: buildThresholds({ read: PRESETS.soak, write: PRESETS.soak }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRSOAK", entity: "mixed" };
  const write = { op: "write", suite: "PRSOAK", entity: "mixed" };

  group("PRSOAK-003/004/005 lectura sostenida (accounts)", () => {
    record(readPage(ROUTES.accounts, data.cookie, read, "?page=1"), "read");
  });
  group("PRSOAK-003/004/005 lectura agregada (dashboard)", () => {
    record(readPage(ROUTES.dashboard, data.cookie, read), "read");
  });
  group("PRSOAK-003/004/005 escritura sostenida (createContact)", () => {
    record(
      invokeServerAction("createContact", ROUTES.contacts, newContactArgs(), data.cookie, write),
      "write",
    );
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRSOAK-mixed-crud");
