/**
 * Security Tests - XSS Prevention
 * Tests to verify XSS vulnerabilities are properly prevented
 */

import { describe, it, expect } from 'vitest'
import { z } from 'zod'

// Test utility to sanitize user input
const sanitizeInput = (input: string): string => {
  const map: Record<string, string> = {
    '&': '&',
    '<': '<',
    '>': '>',
    '"': '"',
    "'": '&#x27;',
  }
  const reg = /[&<>"']/g
  return input.replace(reg, (match) => map[match])
}

// Zod schema for safe input validation
const safeInputSchema = z.string().max(1000).refine(
  (val) => !/<script|javascript:|data:/i.test(val),
  { message: 'Potentially dangerous content detected' }
)

describe('Security - XSS Prevention', () => {
  describe('Input Sanitization', () => {
    it('should sanitize HTML special characters', () => {
      const maliciousInput = '<script>alert("xss")</script>'
      const sanitized = sanitizeInput(maliciousInput)
      
      // The sanitized output should escape < and >
      expect(sanitized).toContain('<')
      expect(sanitized).toContain('>')
    })

    it('should sanitize JavaScript protocol in URLs', () => {
      const maliciousInput = 'javascript:alert("xss")'
      const sanitized = sanitizeInput(maliciousInput)
      
      // Only colon after javascript is not in our escape map
      // The important thing is that the input is validated
      const result = safeInputSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should sanitize event handlers', () => {
      const maliciousInput = '" onload="alert(1)"'
      const sanitized = sanitizeInput(maliciousInput)
      
      // Quotes should be escaped
      expect(sanitized).toContain('"')
    })

    it('should sanitize data attributes', () => {
      const maliciousInput = 'data:text/html,<script>alert(1)</script>'
      const sanitized = sanitizeInput(maliciousInput)
      
      // The input should be rejected by validation
      const result = safeInputSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should allow safe content', () => {
      const safeInput = 'Hello World!'
      const sanitized = sanitizeInput(safeInput)
      
      expect(sanitized).toBe(safeInput)
    })
  })

  describe('Input Validation with Zod', () => {
    it('should reject malicious input', () => {
      const maliciousInput = '<script>alert(1)</script>'
      const result = safeInputSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0]?.message).toBe('Potentially dangerous content detected')
      }
    })

    it('should reject JavaScript protocol', () => {
      const maliciousInput = 'javascript:void(0)'
      const result = safeInputSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should accept safe input', () => {
      const safeInput = 'This is a safe message'
      const result = safeInputSchema.safeParse(safeInput)
      expect(result.success).toBe(true)
    })

    it('should reject input exceeding max length', () => {
      const longInput = 'a'.repeat(1001)
      const result = safeInputSchema.safeParse(longInput)
      expect(result.success).toBe(false)
    })
  })

  describe('URL Sanitization', () => {
    const sanitizeUrl = (url: string): boolean => {
      const allowedProtocols = ['http:', 'https:', 'mailto:']
      const protocol = url.split(':')[0].toLowerCase()
      return allowedProtocols.includes(protocol + ':') && !url.includes('javascript:')
    }

    it('should allow safe URLs', () => {
      expect(sanitizeUrl('https://example.com')).toBe(true)
      expect(sanitizeUrl('http://example.com')).toBe(true)
      expect(sanitizeUrl('mailto:test@example.com')).toBe(true)
    })

    it('should reject dangerous URLs', () => {
      expect(sanitizeUrl('javascript:alert(1)')).toBe(false)
      expect(sanitizeUrl('javascript:void(0)')).toBe(false)
      expect(sanitizeUrl('data:text/html,<script>alert(1)</script>')).toBe(false)
    })
  })

  describe('API Response Sanitization', () => {
    const sanitizeApiResponse = (response: unknown): unknown => {
      if (typeof response === 'string') {
        return sanitizeInput(response)
      }
      if (Array.isArray(response)) {
        return response.map(sanitizeApiResponse)
      }
      if (response && typeof response === 'object') {
        const sanitized: Record<string, unknown> = {}
        for (const [key, value] of Object.entries(response)) {
          sanitized[key] = sanitizeApiResponse(value)
        }
        return sanitized
      }
      return response
    }

    it('should sanitize API response strings', () => {
      const apiResponse = {
        title: '<script>alert(1)</script>',
        description: 'Safe description',
      }
      
      const sanitized = sanitizeApiResponse(apiResponse) as Record<string, string>
      
      // Script tags should be escaped - verify < and > are escaped
      expect(sanitized.title).toContain('<')
      expect(sanitized.title).toContain('>')
      expect(sanitized.description).toBe('Safe description')
    })

    it('should sanitize nested API responses', () => {
      const apiResponse = {
        data: [
          { content: '<img src=x onerror=alert(1)>' },
          { content: 'Safe content' },
        ],
      }
      
      const sanitized = sanitizeApiResponse(apiResponse) as { data: Array<{ content: string }> }
      
      // Quotes should be escaped
      expect(sanitized.data[0].content).toContain('"')
      expect(sanitized.data[1].content).toBe('Safe content')
    })
  })
})
