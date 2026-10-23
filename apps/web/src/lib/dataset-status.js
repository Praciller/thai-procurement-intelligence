/**
 * @template T
 * @param {{ ok: true, data: T } | { ok: false, error: string }} result
 * @returns {{ ok: true, data: T } | { ok: false, error: string }}
 */
export function requireKnownDatasetMode(result) {
  if (!result.ok) return result;
  const mode = /** @type {{ dataset_mode?: unknown }} */ (result.data).dataset_mode;
  if (mode !== "synthetic" && mode !== "official_snapshot") {
    return { ok: false, error: "API returned an unsupported dataset mode" };
  }
  return result;
}
