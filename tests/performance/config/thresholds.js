

export const PRESETS = {
  
  loadRead: { p95: 500, p99: 1000, err: 0.005 },
  loadWrite: { p95: 800, p99: 1500, err: 0.005 },
  loadComplex: { p95: 1500, p99: 2500, err: 0.005 },
  
  stressRead: { p95: 2000, p99: 3000, err: 0.02 },
  stressWrite: { p95: 2500, p99: 4000, err: 0.02 },
  stressComplex: { p95: 4000, p99: 6000, err: 0.02 },
  
  spike: { p95: 2000, p99: 3000, err: 0.02 },
  
  soak: { p95: 1000, p99: 1500, err: 0.005 },
};

export function buildThresholds(byOp) {
  const thresholds = {
    checks: ["rate>0.99"],
  };
  for (const [op, preset] of Object.entries(byOp)) {
    thresholds[`http_req_duration{op:${op}}`] = [
      `p(95)<${preset.p95}`,
      `p(99)<${preset.p99}`,
    ];
    thresholds[`http_req_failed{op:${op}}`] = [`rate<${preset.err}`];
  }
  return thresholds;
}
