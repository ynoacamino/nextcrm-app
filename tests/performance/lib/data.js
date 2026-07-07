// Generadores de datos y utilidades de selección aleatoria.
//
// Los payloads reflejan las firmas reales de las Server Actions del CRM
// (actions/crm/**). Cada creación usa __VU/__ITER + un sufijo aleatorio para
// garantizar unicidad entre iteraciones y VUs.

import { SharedArray } from "k6/data";

const SUFFIX = __ENV.RUN_TAG || "perf";

function rid() {
  return `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
}

function unique(prefix) {
  return `${prefix}-${SUFFIX}-vu${__VU}-it${__ITER}-${rid()}`;
}

// createContact(data) — actions/crm/contacts/create-contact.ts
export function newContactArgs(assignedAccount) {
  const id = unique("ct");
  return [
    {
      first_name: `Perf${__VU}`,
      last_name: id,
      email: `${id}@perf.test`,
      mobile_phone: "+15550000000",
      description: "Contacto generado por pruebas de rendimiento",
      assigned_account: assignedAccount || undefined,
    },
  ];
}

// createAccount(data) — actions/crm/accounts/create-account.ts
export function newAccountArgs() {
  const id = unique("acc");
  return [
    {
      name: `Perf Account ${id}`,
      email: `${id}@perf.test`,
      office_phone: "+15550000001",
      website: "https://perf.test",
      industry: "Technology",
      description: "Cuenta generada por pruebas de rendimiento",
    },
  ];
}

// updateAccount(data) — actions/crm/accounts/update-account.ts
export function updateAccountArgs(accountId) {
  return [
    {
      id: accountId,
      description: `Actualizada por perf ${rid()}`,
      industry: "Consulting",
    },
  ];
}

// createOpportunity(data) — actions/crm/opportunities/create-opportunity.ts
export function newOpportunityArgs(accountId, assignedTo) {
  const id = unique("opp");
  return [
    {
      name: `Perf Opportunity ${id}`,
      account: accountId || undefined,
      assigned_to: assignedTo || undefined,
      budget: "50000",
      expected_revenue: "30000",
      currency: "USD",
      sales_stage: "PROSPECTING",
      type: "New Business",
      close_date: new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
      description: "Oportunidad generada por pruebas de rendimiento",
    },
  ];
}

// updateOpportunity(data) — actions/crm/opportunities/update-opportunity.ts
export function updateOpportunityArgs(opportunityId) {
  return [
    {
      id: opportunityId,
      sales_stage: "PROPOSAL",
      next_step: `Perf step ${rid()}`,
      expected_revenue: "25000",
      currency: "USD",
    },
  ];
}

// createActivity(data) — actions/crm/activities/create-activity.ts
export function newActivityArgs(links) {
  return [
    {
      type: "note",
      title: `Perf activity ${unique("act")}`,
      description: "Actividad generada por pruebas de rendimiento",
      date: new Date().toISOString(),
      status: "completed",
      links: links || [],
    },
  ];
}

// addContractLineItem(data) — actions/crm/contract-line-items/add-line-item
export function newLineItemArgs(contractId) {
  return [
    {
      contractId,
      name: `Perf line ${unique("li")}`,
      quantity: "2",
      unit_price: "150.00",
      discount_type: "NONE",
      discount_value: "0",
    },
  ];
}

// convertTarget(targetId) — actions/crm/targets/convert-target.ts
export function convertTargetArgs(targetId) {
  return [targetId];
}

// deleteContact(contactId) — actions/crm/contacts/delete-contact.ts
export function deleteContactArgs(contactId) {
  return [contactId];
}

// getActivitiesByEntity(entityType, entityId) — args posicionales.
export function activitiesByEntityArgs(entityType, entityId) {
  return [entityType, entityId];
}

// Carga un pool de IDs sembrados (data/entity-ids.json) para escenarios que
// necesitan operar sobre entidades existentes (update, convert, line-item...).
// Generar el archivo con scripts/collect-entity-ids.mjs (Diseño §3.4.1).
export function idPool(entity) {
  return new SharedArray(`ids-${entity}`, () => {
    try {
      const raw = open(`../data/entity-ids.json`);
      const parsed = JSON.parse(raw);
      return parsed[entity] || [];
    } catch (_e) {
      console.warn(
        `[data] No se pudo leer data/entity-ids.json para "${entity}". ` +
          `Genera el pool con scripts/collect-entity-ids.mjs.`,
      );
      return [];
    }
  });
}

// Escoge un elemento pseudoaleatorio de un array (o null si está vacío).
export function pick(arr) {
  if (!arr || arr.length === 0) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}
