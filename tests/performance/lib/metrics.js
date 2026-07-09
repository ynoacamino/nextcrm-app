

import { Trend, Rate, Counter } from "k6/metrics";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.2/index.js";

export const responseTime = new Trend("crm_response_time", true);
export const ttfb = new Trend("crm_ttfb", true);
export const errorRate = new Rate("crm_error_rate");
export const opCounter = new Counter("crm_operations");

export function record(res, opType) {
  responseTime.add(res.timings.duration, { op: opType });
  ttfb.add(res.timings.waiting, { op: opType });
  errorRate.add(res.status >= 400, { op: opType });
  opCounter.add(1, { op: opType });
}

export function makeHandleSummary(caseId) {
  return function handleSummary(data) {
    const name = __ENV.OUT || caseId || "perf-run";
    return {
      [`reports/${name}.json`]: JSON.stringify(data, null, 2),
      stdout: textSummary(data, { indent: " ", enableColors: true }),
    };
  };
}
