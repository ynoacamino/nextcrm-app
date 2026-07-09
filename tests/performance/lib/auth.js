

import http from "k6/http";
import { fail } from "k6";
import {
  ADMIN_EMAIL,
  BASE_URL,
  SESSION_COOKIE,
  SESSION_COOKIE_NAME,
} from "../config/environment.js";

function cookieHeaderFromResponse(res) {
  const jar = res.cookies || {};
  const secure = `__Secure-${SESSION_COOKIE_NAME}`;
  const entry = jar[SESSION_COOKIE_NAME] || jar[secure];
  if (!entry || entry.length === 0) return null;
  const name = jar[SESSION_COOKIE_NAME] ? SESSION_COOKIE_NAME : secure;
  return `${name}=${entry[0].value}`;
}

function signInWithOtp(email) {
  
  const sendRes = http.post(
    `${BASE_URL}/api/auth/email-otp/send-verification-otp`,
    JSON.stringify({ email, type: "sign-in" }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (sendRes.status !== 200) {
    fail(`[auth] send-verification-otp falló para ${email}: HTTP ${sendRes.status}`);
  }

  let otp = null;
  for (let i = 0; i < 20 && !otp; i++) {
    const otpRes = http.get(`${BASE_URL}/api/auth/test-otp?email=${encodeURIComponent(email)}`);
    if (otpRes.status === 200) {
      otp = (otpRes.json() || {}).otp || null;
    }
    if (!otp) http.get(`${BASE_URL}/api/auth/test-otp?email=${encodeURIComponent(email)}`); 
  }
  if (!otp) {
    fail(`[auth] no se capturó OTP para ${email}. ¿El servidor corre con NODE_ENV != production?`);
  }

  const verifyRes = http.post(
    `${BASE_URL}/api/auth/sign-in/email-otp`,
    JSON.stringify({ email, otp }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (verifyRes.status !== 200) {
    fail(`[auth] sign-in/email-otp falló para ${email}: HTTP ${verifyRes.status} — ${verifyRes.body}`);
  }

  const cookie = cookieHeaderFromResponse(verifyRes);
  if (!cookie) {
    fail(`[auth] sign-in devolvió 200 pero no se encontró la cookie ${SESSION_COOKIE_NAME}.`);
  }
  return cookie;
}

export function authenticate(email = ADMIN_EMAIL) {
  if (SESSION_COOKIE) {
    return SESSION_COOKIE.startsWith(SESSION_COOKIE_NAME) || SESSION_COOKIE.includes("=")
      ? SESSION_COOKIE
      : `${SESSION_COOKIE_NAME}=${SESSION_COOKIE}`;
  }
  return signInWithOtp(email);
}
