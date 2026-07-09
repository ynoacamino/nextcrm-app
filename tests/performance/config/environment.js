export const BASE_URL = __ENV.BASE_URL || "http://localhost:3001";

export const LOCALE = __ENV.LOCALE || "en";

export const ADMIN_EMAIL = __ENV.ADMIN_EMAIL || "admin@example.com";

export const SESSION_COOKIE = __ENV.SESSION_COOKIE || "";

export const SESSION_COOKIE_NAME = "better-auth.session_token";

export const ROUTES = {
  dashboard: "/crm/dashboard",
  accounts: "/crm/accounts",
  contacts: "/crm/contacts",
  leads: "/crm/leads",
  opportunities: "/crm/opportunities",
  contracts: "/crm/contracts",
};

export function localized(path) {
  return `/${LOCALE}${path}`;
}
