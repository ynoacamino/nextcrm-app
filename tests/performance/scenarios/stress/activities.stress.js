

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
  scenarios: { activities_stress: stress(5, 15, 15) },
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
