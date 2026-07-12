

import { group, sleep } from "k6";
import { ROUTES } from "../../config/environment.js";
import { spike } from "../../config/scenarios.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage, invokeServerAction } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";
import { idPool, pick, newOpportunityArgs } from "../../lib/data.js";

const accounts = idPool("accounts");

export const options = {
  scenarios: { mixed_spike: spike(5, 25, 3) },
  thresholds: buildThresholds({ read: PRESETS.spike, write: PRESETS.spike }),
};

export function setup() {
  return { cookie: authenticate() };
}

export default function (data) {
  const read = { op: "read", suite: "PRSPIKE", entity: "accounts" };
  const write = { op: "write", suite: "PRSPIKE", entity: "opportunities" };

  if (Math.random() < 0.7) {
    group("PRSPIKE-004 lectura durante pico combinado", () => {
      record(readPage(ROUTES.accounts, data.cookie, read), "read");
    });
  } else {
    group("PRSPIKE-006 creación de oportunidad durante pico", () => {
      const accountId = pick(accounts);
      record(
        invokeServerAction(
          "createOpportunity",
          ROUTES.opportunities,
          newOpportunityArgs(accountId),
          data.cookie,
          write,
        ),
        "write",
      );
    });
  }

  sleep(0.5);
}

export const handleSummary = makeHandleSummary("PRSPIKE-mixed");
