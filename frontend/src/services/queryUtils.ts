export function buildPaginationQuery(page?: number, pageSize?: number): string {
  const params = new URLSearchParams()
  if (page && page >= 1) params.append('page', String(page))
  if (pageSize && pageSize > 0) params.append('pageSize', String(pageSize))
  return params.toString()
}
