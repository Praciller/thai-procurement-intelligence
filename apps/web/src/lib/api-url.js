export const DEFAULT_API_BASE_URL = "http://localhost:8000/api";

function trimTrailingSlash(value) {
  return value.replace(/\/+$/, "");
}

function normalizePath(value) {
  return value.startsWith("/") ? value : `/${value}`;
}

function normalizeOrigin(value) {
  if (!value) return "";
  const withProtocol = /^https?:\/\//.test(value) ? value : `https://${value}`;
  return trimTrailingSlash(withProtocol);
}

export function resolveApiUrl(path, options = {}) {
  const apiBaseUrl = trimTrailingSlash(options.apiBaseUrl || DEFAULT_API_BASE_URL);
  const apiPath = normalizePath(path);

  if (/^https?:\/\//.test(apiBaseUrl)) {
    return `${apiBaseUrl}${apiPath}`;
  }

  if (options.hasWindow) {
    return `${apiBaseUrl}${apiPath}`;
  }

  const origin =
    normalizeOrigin(options.siteUrl) ||
    normalizeOrigin(options.vercelUrl) ||
    "http://localhost:3000";

  return `${origin}${normalizePath(apiBaseUrl)}${apiPath}`;
}
