import { buildPaginationQuery } from '../queryUtils'

describe('buildPaginationQuery', () => {
  it('returns empty string when no args', () => expect(buildPaginationQuery()).toBe(''))
  it('returns page param only', () => expect(buildPaginationQuery(2)).toBe('page=2'))
  it('returns pageSize param only', () => expect(buildPaginationQuery(undefined, 20)).toBe('pageSize=20'))
  it('returns both params', () => expect(buildPaginationQuery(3, 10)).toBe('page=3&pageSize=10'))
  it('ignores page < 1', () => expect(buildPaginationQuery(0, 10)).toBe('pageSize=10'))
  it('ignores pageSize <= 0', () => expect(buildPaginationQuery(1, 0)).toBe('page=1'))
})
