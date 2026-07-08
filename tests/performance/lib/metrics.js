// Métricas personalizadas y reporte de resumen.
//
// Recolectadas según Diseño §4.4: tiempo de respuesta (p50/p95/p99),
// throughput (RPS lo da k6 vía iterations/http_reqs), tasa de error y TTFB.

import { Trend, Rate, Counter } from "k6/metrics";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.2/index.js";

// Duración de respuesta por operación (además de la métrica http nativa,
// útil para dashboards y para separar lectura/escritura/complejas).
export const responseTime = new Trend("crm_response_time", true);
export const ttfb = new Trend("crm_ttfb", true);
export const errorRate = new Rate("crm_error_rate");
export const opCounter = new Counter("crm_operations");

// Registra las métricas transversales de un response de k6.
export function record(res, opType) {
  responseTime.add(res.timings.duration, { op: opType });
  ttfb.add(res.timings.waiting, { op: opType });
  errorRate.add(res.status >= 400, { op: opType });
  opCounter.add(1, { op: opType });
}

// handleSummary compartido: escribe un JSON con métricas crudas y un resumen
// de texto, siguiendo la convención de reportes del repo (scripts de reporte
// de las pruebas de integración). El nombre del archivo se toma de -e OUT o
// del tag del escenario.
export function makeHandleSummary(caseId) {
  return function handleSummary(data) {
    const name = __ENV.OUT || caseId || "perf-run";
    return {
      [`reports/${name}.json`]: JSON.stringify(data, null, 2),
      stdout: textSummary(data, { indent: " ", enableColors: true }),
    };
  };
}
