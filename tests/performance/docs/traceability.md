# Matriz de trazabilidad — Casos PR → Script k6 → Server Action → Métrica

Deriva de la §6 del *Diseño de Casos de Prueba de Rendimiento*. Relaciona cada
identificador `PR<TIPO>-NNN` con el archivo k6 que lo implementa, la Server
Action / endpoint ejercitado y la métrica principal.

## LOAD (25 casos)

| Caso | Script | Server Action / Endpoint | Métrica |
|------|--------|--------------------------|---------|
| PRLOAD-001,002,003 | `scenarios/load/accounts-list.load.js` | getAccounts (GET /crm/accounts) | Tiempo respuesta, Throughput, Error rate |
| PRLOAD-023,024,025 | `scenarios/load/accounts-list.load.js` | getAccounts (orden/paginación) | Tiempo respuesta |
| PRLOAD-004,005 | `scenarios/load/contacts-list.load.js` | getContactsByAccountId / getLeads | Tiempo respuesta, Throughput |
| PRLOAD-006,007,008 | `scenarios/load/contacts-create.load.js` | createContact | Tiempo respuesta, Throughput, Error rate |
| PRLOAD-020 | `scenarios/load/contacts-create.load.js` | deleteContact | Tiempo respuesta |
| PRLOAD-009,010 | `scenarios/load/leads-convert.load.js` | convertTarget | Tiempo respuesta, Throughput |
| PRLOAD-015,016 | `scenarios/load/leads-search.load.js` | getLeads (búsqueda nombre/email) | Tiempo respuesta |
| PRLOAD-011 | `scenarios/load/opportunities.load.js` | updateOpportunity | Tiempo respuesta |
| PRLOAD-017 | `scenarios/load/opportunities.load.js` | getOpportunity (listado por etapa) | Tiempo respuesta |
| PRLOAD-012 | `scenarios/load/dashboard.load.js` | Dashboard (resúmenes agregados) | Tiempo respuesta |
| PRLOAD-013 | `scenarios/load/activities.load.js` | createActivity | Tiempo respuesta |
| PRLOAD-014 | `scenarios/load/activities.load.js` | getActivitiesByEntity | Tiempo respuesta |
| PRLOAD-018 | `scenarios/load/accounts-crud.load.js` | createAccount | Tiempo respuesta |
| PRLOAD-019 | `scenarios/load/accounts-crud.load.js` | updateAccount | Tiempo respuesta |
| PRLOAD-022 | `scenarios/load/accounts-crud.load.js` | getAccountById + getActivitiesByEntity | Tiempo respuesta |
| PRLOAD-021 | `scenarios/load/contracts-lineitem.load.js` | addContractLineItem | Tiempo respuesta |

## STRESS (16 casos)

| Caso | Script | Server Action / Endpoint | Métrica |
|------|--------|--------------------------|---------|
| PRSTRESS-001,007,009,014,015 | `scenarios/stress/accounts-list.stress.js` | getAccounts | Saturación, Error rate, Degradación, Recuperación |
| PRSTRESS-002,008 | `scenarios/stress/contacts-create.stress.js` | createContact | Saturación, Error rate |
| PRSTRESS-003 | `scenarios/stress/leads-convert.stress.js` | convertTarget | Saturación |
| PRSTRESS-004 | `scenarios/stress/opportunities.stress.js` | getOpportunity | Saturación |
| PRSTRESS-010 | `scenarios/stress/opportunities.stress.js` | createOpportunity | Degradación |
| PRSTRESS-005 | `scenarios/stress/dashboard.stress.js` | Dashboard | Saturación |
| PRSTRESS-006 | `scenarios/stress/activities.stress.js` | createActivity | Saturación |
| PRSTRESS-011,012,013,016 | `scenarios/stress/capacity.stress.js` | getAccounts (arrival-rate) | Throughput máx (RPS) + recursos (Grafana) |

## SPIKE (8 casos)

| Caso | Script | Server Action / Endpoint | Métrica |
|------|--------|--------------------------|---------|
| PRSPIKE-001,003,005,007 | `scenarios/spike/accounts-list.spike.js` | getAccounts | 5xx, Recuperación, p95, Error rate |
| PRSPIKE-002,008 | `scenarios/spike/contacts-create.spike.js` | createContact | 5xx, Error rate |
| PRSPIKE-004 | `scenarios/spike/mixed.spike.js` | getAccounts + createOpportunity | Manejo de pico combinado |
| PRSPIKE-006 | `scenarios/spike/mixed.spike.js` | createOpportunity | p95 durante pico |

## SOAK (9 casos)

| Caso | Script | Server Action / Endpoint | Métrica |
|------|--------|--------------------------|---------|
| PRSOAK-001,006,007,008 | `scenarios/soak/accounts-list.soak.js` | getAccounts | Degradación, Throughput, Timeouts, Errores BD |
| PRSOAK-002 | `scenarios/soak/contacts-create.soak.js` | createContact | Degradación |
| PRSOAK-003,004,005,009 | `scenarios/soak/mixed-crud.soak.js` | Mezcla CRUD | Memoria Next.js/PG, Conexiones PG, Memoria monitoreo (Grafana) |

**Total: 58 casos** — PRLOAD 25 · PRSTRESS 16 · PRSPIKE 8 · PRSOAK 9.
