// Genera volumen de datos para las pruebas de rendimiento (smoke).
// Usa el mismo adapter-pg que lib/prisma.ts. NO se commitea.
import { PrismaClient } from "@prisma/client";
import { Pool } from "pg";
import { PrismaPg } from "@prisma/adapter-pg";

const N_ACC = Number(process.env.N_ACC || 3000);
const N_CT = Number(process.env.N_CT || 3000);
const N_LD = Number(process.env.N_LD || 1500);
const N_TG = Number(process.env.N_TG || 500);
const N_OPP = Number(process.env.N_OPP || 500);

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter: new PrismaPg(pool) });

const r = () => Math.random().toString(36).slice(2, 9);

async function main() {
  const admin = await prisma.users.findFirst({ where: { email: "admin@example.com" }, select: { id: true } });
  const uid = admin.id;
  console.log("admin", uid);

  // Accounts
  await prisma.crm_Accounts.createMany({
    data: Array.from({ length: N_ACC }, (_, i) => ({
      v: 0, name: `Perf Account ${i}-${r()}`, createdBy: uid, updatedBy: uid, status: "Active",
    })),
  });
  const accs = await prisma.crm_Accounts.findMany({ where: { createdBy: uid }, select: { id: true }, take: N_ACC });
  console.log("accounts", await prisma.crm_Accounts.count());

  // Contacts (linked to random accounts)
  await prisma.crm_Contacts.createMany({
    data: Array.from({ length: N_CT }, (_, i) => ({
      v: 0, first_name: `Perf${i}`, last_name: `Contact-${r()}`,
      email: `ct${i}-${r()}@perf.test`,
      accountsIDs: accs[i % accs.length]?.id, createdBy: uid, updatedBy: uid, status: true,
    })),
  });
  console.log("contacts", await prisma.crm_Contacts.count());

  // Leads
  await prisma.crm_Leads.createMany({
    data: Array.from({ length: N_LD }, (_, i) => ({
      v: 0, firstName: `Perf${i}`, lastName: `Lead-${r()}`,
      email: `ld${i}-${r()}@perf.test`, createdBy: uid, updatedBy: uid, assigned_to: uid,
    })),
  });
  console.log("leads", await prisma.crm_Leads.count());

  // Targets (para convertTarget) — best-effort
  try {
    await prisma.crm_Targets.createMany({
      data: Array.from({ length: N_TG }, (_, i) => ({
        last_name: `Target-${r()}`, first_name: `Perf${i}`,
        company: `Perf Co ${i}`, email: `tg${i}-${r()}@perf.test`, created_by: uid,
      })),
    });
    console.log("targets", await prisma.crm_Targets.count());
  } catch (e) { console.log("targets SKIP:", e.message.split("\n")[0]); }

  // Opportunities — best-effort
  try {
    await prisma.crm_Opportunities.createMany({
      data: Array.from({ length: N_OPP }, (_, i) => ({
        v: 0, name: `Perf Opp ${i}-${r()}`, account: accs[i % accs.length]?.id,
        createdBy: uid, updatedBy: uid, assigned_to: uid, last_activity_by: uid,
        sales_stage: "PROSPECTING", status: "ACTIVE", type: "New Business",
      })),
    });
    console.log("opportunities", await prisma.crm_Opportunities.count());
  } catch (e) { console.log("opportunities SKIP:", e.message.split("\n")[0]); }

  await prisma.$disconnect();
  await pool.end();
}
main().catch(async (e) => { console.error(e); process.exit(1); });
