import { describe, it, expect } from 'vitest'
import {
  formatFileSize,
  formatDate,
  formatDateTime,
  debounce,
  throttle,
  getFileExtension,
  getFileNameWithoutExtension,
  isImageFile,
  isVideoFile,
  isAudioFile,
  truncateText,
  capitalizeFirstLetter,
  camelCaseToTitleCase,
  generateId,
  cloneObject,
  isEmptyObject,
  mergeObjects,
  buildQueryString,
} from '@/utils/helpers'

describe('Utility Functions', () => {
  describe('formatFileSize', () => {
    it('should format 0 bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes')
    })

    it('should format bytes correctly', () => {
      expect(formatFileSize(500)).toBe('500 Bytes')
    })

    it('should format kilobytes correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
      expect(formatFileSize(1536)).toBe('1.5 KB')
    })

    it('should format megabytes correctly', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
      expect(formatFileSize(1572864)).toBe('1.5 MB')
    })

    it('should format gigabytes correctly', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB')
    })

    it('should format terabytes correctly', () => {
      expect(formatFileSize(1099511627776)).toBe('1 TB')
    })
  })

  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2024-01-15')
      const result = formatDate(date)
      expect(result).toContain('Jan')
      expect(result).toContain('15')
      expect(result).toContain('2024')
    })

    it('should handle string date input', () => {
      const result = formatDate('2024-01-15')
      expect(result).toContain('Jan')
      expect(result).toContain('15')
    })
  })

  describe('formatDateTime', () => {
    it('should format date and time correctly', () => {
      const date = new Date('2024-01-15T14:30:00')
      const result = formatDateTime(date)
      expect(result).toContain('Jan')
      expect(result).toContain('15')
      expect(result).toContain('2024')
      expect(result).toContain('2')
      expect(result).toContain('30')
    })
  })

  describe('debounce', () => {
    it('should delay function execution', () => {
      vi.useFakeTimers()
      const fn = vi.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn()
      expect(fn).not.toHaveBeenCalled()

      vi.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('should cancel previous calls on subsequent calls', () => {
      vi.useFakeTimers()
      const fn = vi.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn()
      debouncedFn()
      debouncedFn()

      expect(fn).not.toHaveBeenCalled()

      vi.advanceTimersByTime(100)
      expect(fn).toHaveBeenCalledTimes(1)
    })

    it('should provide cancel method', () => {
      vi.useFakeTimers()
      const fn = vi.fn()
      const debouncedFn = debounce(fn, 100)

      debouncedFn()
      debouncedFn.cancel()

      vi.advanceTimersByTime(100)
      expect(fn).not.toHaveBeenCalled()
    })
  })

  describe('throttle', () => {
    it('should limit function calls', () => {
      vi.useFakeTimers()
      const fn = vi.fn()
      const throttledFn = throttle(fn, 100)

      throttledFn()
      throttledFn()
      throttledFn()

      expect(fn).toHaveBeenCalledTimes(1)

      vi.advanceTimersByTime(100)
      throttledFn()
      expect(fn).toHaveBeenCalledTimes(2)
    })
  })

  describe('getFileExtension', () => {
    it('should return correct extension for simple filename', () => {
      expect(getFileExtension('document.pdf')).toBe('pdf')
    })

    it('should handle multiple dots', () => {
      expect(getFileExtension('archive.tar.gz')).toBe('gz')
    })

    it('should handle uppercase extension', () => {
      expect(getFileExtension('image.PNG')).toBe('png')
    })

    it('should return empty string for file without extension', () => {
      expect(getFileExtension('README')).toBe('')
    })
  })

  describe('getFileNameWithoutExtension', () => {
    it('should remove extension correctly', () => {
      expect(getFileNameWithoutExtension('document.pdf')).toBe('document')
    })

    it('should handle multiple dots', () => {
      expect(getFileNameWithoutExtension('archive.tar.gz')).toBe('archive.tar')
    })

    it('should return full name if no extension', () => {
      expect(getFileNameWithoutExtension('README')).toBe('README')
    })
  })

  describe('isImageFile', () => {
    it('should return true for image extensions', () => {
      expect(isImageFile('photo.jpg')).toBe(true)
      expect(isImageFile('image.jpeg')).toBe(true)
      expect(isImageFile('picture.png')).toBe(true)
      expect(isImageFile('animation.gif')).toBe(true)
      expect(isImageFile('image.webp')).toBe(true)
    })

    it('should return false for non-image extensions', () => {
      expect(isImageFile('video.mp4')).toBe(false)
      expect(isImageFile('document.pdf')).toBe(false)
    })
  })

  describe('isVideoFile', () => {
    it('should return true for video extensions', () => {
      expect(isVideoFile('movie.mp4')).toBe(true)
      expect(isVideoFile('video.mkv')).toBe(true)
      expect(isVideoFile('clip.avi')).toBe(true)
    })

    it('should return false for non-video extensions', () => {
      expect(isVideoFile('audio.mp3')).toBe(false)
      expect(isVideoFile('document.pdf')).toBe(false)
    })
  })

  describe('isAudioFile', () => {
    it('should return true for audio extensions', () => {
      expect(isAudioFile('song.mp3')).toBe(true)
      expect(isAudioFile('track.flac')).toBe(true)
      expect(isAudioFile('podcast.wav')).toBe(true)
    })

    it('should return false for non-audio extensions', () => {
      expect(isAudioFile('video.mp4')).toBe(false)
      expect(isAudioFile('document.pdf')).toBe(false)
    })
  })

  describe('truncateText', () => {
    it('should not truncate short text', () => {
      expect(truncateText('Hello', 10)).toBe('Hello')
    })

    it('should truncate long text', () => {
      expect(truncateText('Hello World', 8)).toBe('Hello Wo...')
    })
  })

  describe('capitalizeFirstLetter', () => {
    it('should capitalize first letter', () => {
      expect(capitalizeFirstLetter('hello')).toBe('Hello')
      expect(capitalizeFirstLetter('world')).toBe('World')
    })

    it('should handle already capitalized word', () => {
      expect(capitalizeFirstLetter('Hello')).toBe('Hello')
    })

    it('should handle single letter', () => {
      expect(capitalizeFirstLetter('h')).toBe('H')
    })
  })

  describe('camelCaseToTitleCase', () => {
    it('should convert camelCase to Title Case', () => {
      expect(camelCaseToTitleCase('camelCase')).toBe('Camel Case')
      expect(camelCaseToTitleCase('myVariableName')).toBe('My Variable Name')
    })

    it('should handle single word', () => {
      expect(camelCaseToTitleCase('Hello')).toBe('Hello')
    })
  })

  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId()
      const id2 = generateId()
      expect(id1).not.toBe(id2)
    })

    it('should include timestamp', () => {
      const id = generateId()
      expect(id.split('-')[0]).toBe(String(Date.now()).slice(-13))
    })
  })

  describe('cloneObject', () => {
    it('should deep clone object', () => {
      const original = { a: 1, b: { c: 2 } }
      const cloned = cloneObject(original)

      expect(cloned).toEqual(original)
      expect(cloned).not.toBe(original)
      expect(cloned.b).not.toBe(original.b)
    })

    it('should handle arrays', () => {
      const original = [1, 2, { a: 3 }]
      const cloned = cloneObject(original)

      expect(cloned).toEqual(original)
      expect(cloned).not.toBe(original)
    })
  })

  describe('isEmptyObject', () => {
    it('should return true for empty object', () => {
      expect(isEmptyObject({})).toBe(true)
    })

    it('should return false for non-empty object', () => {
      expect(isEmptyObject({ a: 1 })).toBe(false)
    })
  })

  describe('mergeObjects', () => {
    it('should merge two objects', () => {
      const target = { a: 1, b: 2 }
      const source = { b: 3, c: 4 }
      const result = mergeObjects(target, source)

      expect(result).toEqual({ a: 1, b: 3, c: 4 })
    })

    it('should handle undefined source', () => {
      const target = { a: 1 }
      const result = mergeObjects(target, {})

      expect(result).toEqual({ a: 1 })
    })
  })

  describe('buildQueryString', () => {
    it('should build query string from object', () => {
      const params = { page: 1, limit: 20, query: 'test' }
      const result = buildQueryString(params)

      expect(result).toContain('page=1')
      expect(result).toContain('limit=20')
      expect(result).toContain('query=test')
    })

    it('should exclude null and undefined values', () => {
      const params = { a: 1, b: null, c: undefined, d: 4 }
      const result = buildQueryString(params)

      expect(result).toContain('a=1')
      expect(result).not.toContain('b=')
      expect(result).not.toContain('c=')
      expect(result).toContain('d=4')
    })
  })
})
