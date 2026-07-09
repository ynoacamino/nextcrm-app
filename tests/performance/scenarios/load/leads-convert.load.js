

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { load } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, convertTargetArgs } from "../../lib/data.js";

const targets = idPool("targets");

export const options = {
  scenarios: { leads_convert_load: load(10, 10) },
  thresholds: buildThresholds({ complex: PRESETS.loadComplex }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const t = { op: "complex", suite: "PRLOAD", entity: "leads" };
  const targetId = pick(targets);
  if (!targetId) {
    
    sleep(1);
    return;
  }

  group("PRLOAD-009/010 conversión de lead", () => {
    const res = invokeServerAction(
      "convertTarget",
      ROUTES.leads,
      convertTargetArgs(targetId),
      data.cookie,
      t,
    );
    record(res, "complex");
  });

  sleep(1);
}

export const handleSummary = makeHandleSummary("PRLOAD-leads-convert");
