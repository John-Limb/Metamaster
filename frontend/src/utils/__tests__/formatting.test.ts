import { formatBytes, formatDuration, formatCodec } from '../formatting'

describe('formatBytes', () => {
  it('formats terabytes', () => expect(formatBytes(1.5e12)).toBe('1.5 TB'))
  it('formats gigabytes', () => expect(formatBytes(4.2e9)).toBe('4.2 GB'))
  it('formats megabytes', () => expect(formatBytes(300e6)).toBe('300 MB'))
  it('formats raw bytes', () => expect(formatBytes(500)).toBe('500 B'))
  it('formats exactly 1 GB', () => expect(formatBytes(1e9)).toBe('1.0 GB'))
})

describe('formatDuration', () => {
  it('formats hours and minutes', () => expect(formatDuration(7384)).toBe('2h 3m'))
  it('formats minutes only when under an hour', () => expect(formatDuration(195)).toBe('3m'))
  it('returns dash for undefined', () => expect(formatDuration(undefined)).toBe('—'))
  it('returns dash for zero', () => expect(formatDuration(0)).toBe('—'))
  it('returns dash for null', () => expect(formatDuration(null)).toBe('—'))
})

describe('formatCodec', () => {
  it('maps h264 to H.264', () => expect(formatCodec('h264')).toBe('H.264'))
  it('maps hevc to H.265', () => expect(formatCodec('hevc')).toBe('H.265'))
  it('uppercases unknown codecs', () => expect(formatCodec('xyz')).toBe('XYZ'))
  it('returns dash for null', () => expect(formatCodec(null)).toBe('—'))
  it('returns dash for undefined', () => expect(formatCodec(undefined)).toBe('—'))
})
