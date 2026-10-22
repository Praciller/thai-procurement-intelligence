/** @typedef {{ q: string, province: string, category: string, mode: "keyword" | "semantic" | "hybrid", sort: string, page: number }} RecordsSearchState */

/**
 * @param {RecordsSearchState} current
 * @param {Partial<RecordsSearchState>} changes
 * @returns {RecordsSearchState}
 */
export function updateRecordsSearchState(current, changes) {
  return { ...current, ...changes, page: 1 };
}

/**
 * @param {RecordsSearchState} state
 * @param {number} pageSize
 */
export function buildRecordsQuery(state, pageSize) {
  const params = new URLSearchParams({ page: String(state.page), page_size: String(pageSize), search_mode: state.mode });
  if (state.q.trim()) params.set("q", state.q.trim());
  if (state.province) params.set("province", state.province);
  if (state.category) params.set("category", state.category);
  if (state.mode === "keyword" || !state.q.trim()) params.set("sort", state.sort);
  return `?${params.toString()}`;
}

export function getRecordsPagination(total, page, pageSize, ranked, maxRankedResults) {
  const hasRankedWindowLimit = ranked && total > maxRankedResults;
  const totalPages = Math.max(
    1,
    Math.min(
      Math.ceil(total / pageSize),
      hasRankedWindowLimit ? Math.floor(maxRankedResults / pageSize) : Number.POSITIVE_INFINITY,
    ),
  );
  return {
    totalPages,
    hasRankedWindowLimit,
    nextDisabled: page >= totalPages || (hasRankedWindowLimit && page * pageSize >= maxRankedResults),
  };
}
