

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { stress } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, convertTargetArgs } from "../../lib/data.js";

const targets = idPool("targets");

export const options = {
  scenarios: { leads_convert_stress: stress(10, 50, 15) },
  thresholds: buildThresholds({ complex: PRESETS.stressComplex }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "complex", suite: "PRSTRESS", entity: "leads" };
  const targetId = pick(targets);
  if (!targetId) {
    sleep(0.5);
    return;
  }

  group("PRSTRESS-003 conversión de lead bajo saturación", () => {
    record(
      invokeServerAction("convertTarget", ROUTES.leads, convertTargetArgs(targetId), data.cookie, t),
      "complex",
    );
  });

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSTRESS-leads-convert");
