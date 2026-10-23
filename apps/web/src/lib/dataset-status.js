/**
 * @template T
 * @param {{ ok: true, data: T } | { ok: false, error: string }} result
 * @returns {{ ok: true, data: T } | { ok: false, error: string }}
 */
export function requireKnownDatasetMode(result) {
  if (!result.ok) return result;
  const data = /** @type {{ dataset_mode?: unknown } | null | undefined }} */ (result.data);
  const mode = data && typeof data === "object" ? data.dataset_mode : undefined;
  if (mode !== "synthetic" && mode !== "official_snapshot") {
    return { ok: false, error: "API returned an unsupported dataset mode" };
  }
  return result;
}
