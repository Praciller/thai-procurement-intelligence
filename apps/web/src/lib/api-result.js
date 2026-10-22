/**
 * @template T
 * @param {() => Promise<T>} request
 * @returns {Promise<{ ok: true, data: T } | { ok: false, error: string }>}
 */
export async function asApiResult(request) {
  try {
    return { ok: true, data: await request() };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "API request failed",
    };
  }
}
