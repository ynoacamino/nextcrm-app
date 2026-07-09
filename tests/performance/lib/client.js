

import http from "k6/http";
import { check } from "k6";
import { BASE_URL, localized } from "../config/environment.js";
import { actionId } from "../action-ids.js";

export function invokeServerAction(actionName, pagePath, args, cookie, tags = {}) {
  const mergedTags = Object.assign({ action: actionName }, tags);
  const res = http.post(`${BASE_URL}${localized(pagePath)}`, JSON.stringify(args), {
    headers: {
      "Content-Type": "text/plain;charset=UTF-8",
      Accept: "text/x-component",
      "Next-Action": actionId(actionName),
      Cookie: cookie,
    },
    tags: mergedTags,
  });
  check(res, {
    [`${actionName}: status 2xx/3xx`]: (r) => r.status >= 200 && r.status < 400,
    [`${actionName}: sin error de servidor`]: (r) => r.status < 500,
  });
  return res;
}

export function readPage(pagePath, cookie, tags = {}, query = "") {
  const mergedTags = Object.assign({}, tags);
  const res = http.get(`${BASE_URL}${localized(pagePath)}${query}`, {
    headers: { Cookie: cookie, Accept: "text/html" },
    tags: mergedTags,
  });
  check(res, {
    [`GET ${pagePath}: status 200`]: (r) => r.status === 200,
    [`GET ${pagePath}: sin error de servidor`]: (r) => r.status < 500,
  });
  return res;
}
