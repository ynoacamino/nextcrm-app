/**
 * Performance data seed — creates bulk CRM entities for perf tests.
 * Gatillado por PERF_SEED=true en seed.ts principal.
 * Idempotente: verifica conteo antes de crear.
 */
import type { PrismaClient } from "@prisma/client";
import { faker } from "@faker-js/faker";

const TARGET = Number(process.env.PERF_SEED_COUNT || 100);
const BATCH = 50;

async function count(model: { count: (args?: any) => Promise<number> }): Promise<number> {
  return model.count();
}

export async function seedPerfData(prisma: PrismaClient, ownerId: string) {
  console.log(`[perf-seed] target: ${TARGET} per entity`);

  // --- Accounts ---
  const accExisting = await count(prisma.crm_Accounts);
  if (accExisting < TARGET) {
    const need = TARGET - accExisting;
    console.log(`[perf-seed] accounts: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Accounts.createMany({
        data: Array.from({ length: n }, () => ({
          v: 0,
          name: faker.company.name(),
          email: faker.internet.email(),
          office_phone: faker.phone.number(),
          website: faker.internet.url(),
          description: faker.lorem.sentence(),
          status: "Active",
          type: "Customer",
          billing_city: faker.location.city(),
          billing_country: faker.location.countryCode(),
          assigned_to: ownerId,
          createdBy: ownerId,
        })),
      });
    }
  }
  const allAccounts = await prisma.crm_Accounts.findMany({ select: { id: true } });
  const accountIds = allAccounts.map((a) => a.id);
  console.log(`[perf-seed] accounts: ${accountIds.length} total`);

  // --- Contacts ---
  const ctExisting = await count(prisma.crm_Contacts);
  if (ctExisting < TARGET) {
    const need = TARGET - ctExisting;
    console.log(`[perf-seed] contacts: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Contacts.createMany({
        data: Array.from({ length: n }, () => ({
          v: 0,
          first_name: faker.person.firstName(),
          last_name: faker.person.lastName(),
          email: faker.internet.email(),
          mobile_phone: faker.phone.number(),
          position: faker.person.jobTitle(),
          accountsIDs: faker.helpers.arrayElement(accountIds),
          assigned_to: ownerId,
          createdBy: ownerId,
          status: true,
        })),
      });
    }
  }
  const allContacts = await prisma.crm_Contacts.findMany({ select: { id: true } });
  console.log(`[perf-seed] contacts: ${allContacts.length} total`);

  // --- Leads ---
  const ldExisting = await count(prisma.crm_Leads);
  if (ldExisting < TARGET) {
    const need = TARGET - ldExisting;
    console.log(`[perf-seed] leads: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Leads.createMany({
        data: Array.from({ length: n }, () => ({
          v: 0,
          firstName: faker.person.firstName(),
          lastName: faker.person.lastName(),
          email: faker.internet.email(),
          phone: faker.phone.number(),
          company: faker.company.name(),
          jobTitle: faker.person.jobTitle(),
          description: faker.lorem.sentence(),
          assigned_to: ownerId,
          createdBy: ownerId,
        })),
      });
    }
  }
  const allLeads = await prisma.crm_Leads.findMany({ select: { id: true } });
  console.log(`[perf-seed] leads: ${allLeads.length} total`);

  // --- Opportunities ---
  const oppExisting = await count(prisma.crm_Opportunities);
  if (oppExisting < TARGET) {
    const stage = await prisma.crm_Opportunities_Sales_Stages.findFirst({ select: { id: true } });
    const oppType = await prisma.crm_Opportunities_Type.findFirst({ select: { id: true } });
    const need = TARGET - oppExisting;
    console.log(`[perf-seed] opportunities: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Opportunities.createMany({
        data: Array.from({ length: n }, () => ({
          v: 0,
          name: faker.commerce.productName(),
          description: faker.lorem.sentence(),
          account: faker.helpers.arrayElement(accountIds),
          assigned_to: ownerId,
          createdBy: ownerId,
          sales_stage: stage?.id,
          type: oppType?.id,
          budget: Number(faker.commerce.price({ min: 1000, max: 100000 })),
          expected_revenue: Number(faker.commerce.price({ min: 500, max: 50000 })),
          currency: "USD",
          status: "ACTIVE" as const,
        })),
      });
    }
  }
  const allOpps = await prisma.crm_Opportunities.findMany({ select: { id: true } });
  console.log(`[perf-seed] opportunities: ${allOpps.length} total`);

  // --- Contracts ---
  const ct2Existing = await count(prisma.crm_Contracts);
  if (ct2Existing < TARGET) {
    const need = TARGET - ct2Existing;
    console.log(`[perf-seed] contracts: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Contracts.createMany({
        data: Array.from({ length: n }, () => ({
          v: 0,
          title: `${faker.commerce.productName()} Contract`,
          description: faker.lorem.sentence(),
          account: faker.helpers.arrayElement(accountIds),
          assigned_to: ownerId,
          createdBy: ownerId,
          value: Number(faker.commerce.price({ min: 1000, max: 100000 })),
          currency: "USD",
          status: "NOTSTARTED" as const,
        })),
      });
    }
  }
  const allContracts = await prisma.crm_Contracts.findMany({ select: { id: true } });
  console.log(`[perf-seed] contracts: ${allContracts.length} total`);

  // --- Targets ---
  const tgExisting = await count(prisma.crm_Targets);
  if (tgExisting < TARGET) {
    const need = TARGET - tgExisting;
    console.log(`[perf-seed] targets: creating ${need}`);
    for (let i = 0; i < need; i += BATCH) {
      const n = Math.min(BATCH, need - i);
      await prisma.crm_Targets.createMany({
        data: Array.from({ length: n }, () => ({
          first_name: faker.person.firstName(),
          last_name: faker.person.lastName(),
          email: faker.internet.email(),
          mobile_phone: faker.phone.number(),
          company: faker.company.name(),
          position: faker.person.jobTitle(),
          status: true,
          created_by: ownerId,
        })),
      });
    }
  }
  const allTargets = await prisma.crm_Targets.findMany({ select: { id: true } });
  console.log(`[perf-seed] targets: ${allTargets.length} total`);

  console.log("[perf-seed] done");
}
