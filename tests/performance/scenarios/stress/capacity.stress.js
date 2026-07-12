

import { group } from "k6";
import { ROUTES } from "../../config/environment.js";
import { PRESETS, buildThresholds } from "../../config/thresholds.js";
import { authenticate } from "../../lib/auth.js";
import { readPage } from "../../lib/client.js";
import { record, makeHandleSummary } from "../../lib/metrics.js";

const TARGET_RPS = Number(__ENV.TARGET_RPS || 100);
const SCALE = Number(__ENV.DURATION_SCALE || 1);
const m = (x) => `${Math.max(1, Math.round(x * SCALE))}m`;

export const options = {
  scenarios: {
    capacity_stress: {
      executor: "ramping-arrival-rate",
      startRate: 25,
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 50,
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
