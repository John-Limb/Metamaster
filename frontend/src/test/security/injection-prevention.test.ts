/**
 * Security Tests - Injection Attack Prevention
 * Tests to verify protection against SQL injection, NoSQL injection, and command injection
 */

import { describe, it, expect } from 'vitest'
import { z } from 'zod'

// SQL Injection prevention patterns
const SQL_INJECTION_PATTERNS = [
  /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)/i,
  /(--|;|\/\*|\*\/|@@|@)/,
  /(\bOR\b\s+\d+\s*=\s*\d+)/i,
  /(\bAND\b\s+\d+\s*=\s*\d+)/i,
  /('\s*(OR|AND)\s*')/i,
  /(\bEXEC\b|\bEXECUTE\b)/i,
  /(\bXP_\w+)/i,
]

// NoSQL Injection prevention patterns
const NOSQL_INJECTION_PATTERNS = [
  /\$where/i,
  /\$eq/i,
  /\$ne/i,
  /\$gt/i,
  /\$lt/i,
  /\$gte/i,
  /\$lte/i,
  /\$in/i,
  /\$nin/i,
  /\$or/i,
  /\$and/i,
  /\$not/i,
  /\$nor/i,
  /\$exists/i,
  /\$type/i,
  /\$mod/i,
  /\$regex/i,
  /\$text/i,
  /\$search/i,
  /\$geoWithin/i,
  /\$geoIntersects/i,
  /\$near/i,
  /\$box/i,
  /\$center/i,
  /\$polygon/i,
  /\$centerSphere/i,
]

// Command Injection patterns
const COMMAND_INJECTION_PATTERNS = [
  /(\||;|&|\$|`|\(|\)|\{|\}|\[|\]|<|>|\\)/,
  /\b(cat|ls|rm|mkdir|touch|wget|curl|nc|bash|sh|python|perl|ruby|php|node)\b/i,
  /\b(whoami|id|uname|date|time|uptime|free|df|du|ps|top|kill)\b/i,
  /\b(export|PATH|HOME|USER|GROUP|HOSTNAME)\b/i,
  /(\$\{.*\}|\$[a-zA-Z_]+)/,
]

// Input validation schemas
const safeSearchSchema = z
  .string()
  .min(1)
  .max(100)
  .refine((val) => {
    for (const pattern of SQL_INJECTION_PATTERNS) {
      if (pattern.test(val)) {
        return false
      }
    }
    return true
  }, { message: 'Potentially dangerous SQL pattern detected' })

const safeUsernameSchema = z
  .string()
  .min(3)
  .max(50)
  .regex(/^[a-zA-Z0-9_]+$/, { message: 'Username must contain only alphanumeric characters and underscores' })
  .refine((val) => {
    for (const pattern of NOSQL_INJECTION_PATTERNS) {
      if (pattern.test(val)) {
        return false
      }
    }
    return true
  }, { message: 'Potentially dangerous NoSQL pattern detected' })

const safeFilenameSchema = z
  .string()
  .min(1)
  .max(255)
  .regex(/^[a-zA-Z0-9._-]+$/, { message: 'Filename contains invalid characters' })
  .refine((val) => {
    for (const pattern of COMMAND_INJECTION_PATTERNS) {
      if (pattern.test(val)) {
        return false
      }
    }
    return true
  }, { message: 'Potentially dangerous command pattern detected' })

// Sanitization functions
const sanitizeForSQL = (input: string): string => {
  return input
    .replace(/'/g, "''")
    .replace(/\\/g, '\\\\')
    .replace(/\0/g, '')
    .trim()
}

const sanitizeForHTML = (input: string): string => {
  const map: Record<string, string> = {
    '&': '&',
    '<': '<',
    '>': '>',
    '"': '"',
    "'": '&#x27;',
    '/': '&#x2F;',
  }
  return input.replace(/[&<>"'/]/g, (match) => map[match])
}

const sanitizeForCommand = (input: string): string => {
  return input
    .replace(/[;|&`$\\]/g, '')
    .replace(/\.\.\//g, '')
    .trim()
}

describe('Security - Injection Attack Prevention', () => {
  describe('SQL Injection Prevention', () => {
    it('should detect SELECT statement injection', () => {
      const maliciousInput = "'; SELECT * FROM users --"
      const result = safeSearchSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect UNION-based injection', () => {
      const maliciousInput = "' UNION SELECT credit_card FROM users --"
      const result = safeSearchSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect OR-based injection', () => {
      const maliciousInput = "' OR '1'='1"
      const result = safeSearchSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect DROP TABLE injection', () => {
      const maliciousInput = "'; DROP TABLE users --"
      const result = safeSearchSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should accept safe search queries', () => {
      const safeInput = 'search term'
      const result = safeSearchSchema.safeParse(safeInput)
      expect(result.success).toBe(true)
    })

    it('should sanitize quotes for SQL', () => {
      const input = "O'Brien"
      const sanitized = sanitizeForSQL(input)
      expect(sanitized).toBe("O''Brien")
    })

    it('should sanitize backslashes for SQL', () => {
      const input = 'path\\to\\file'
      const sanitized = sanitizeForSQL(input)
      expect(sanitized).toBe('path\\\\to\\\\file')
    })
  })

  describe('NoSQL Injection Prevention', () => {
    it('should detect $where operator injection', () => {
      const maliciousInput = '{"$where": "sleep(1000)"}'
      const result = safeUsernameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect $eq operator injection', () => {
      const maliciousInput = '{"$eq": ["admin", ""]}'
      const result = safeUsernameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect $ne operator injection', () => {
      const maliciousInput = '{"$ne": null}'
      const result = safeUsernameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect $regex operator injection', () => {
      const maliciousInput = '{"$regex": "^.{200}$"}'
      const result = safeUsernameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should accept safe usernames', () => {
      const safeInput = 'john_doe'
      const result = safeUsernameSchema.safeParse(safeInput)
      expect(result.success).toBe(true)
    })
  })

  describe('Command Injection Prevention', () => {
    it('should detect pipe operator injection', () => {
      const maliciousInput = 'file.txt | cat /etc/passwd'
      const result = safeFilenameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect semicolon injection', () => {
      const maliciousInput = 'file.txt; rm -rf /'
      const result = safeFilenameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect backtick injection', () => {
      const maliciousInput = '`whoami`'
      const result = safeFilenameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect dangerous commands', () => {
      const maliciousInput = 'cat /etc/passwd'
      const result = safeFilenameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should detect environment variable injection', () => {
      const maliciousInput = '${HOME}'
      const result = safeFilenameSchema.safeParse(maliciousInput)
      expect(result.success).toBe(false)
    })

    it('should accept safe filenames', () => {
      const safeInput = 'document.pdf'
      const result = safeFilenameSchema.safeParse(safeInput)
      expect(result.success).toBe(true)
    })

    it('should sanitize pipe characters for commands', () => {
      const input = 'file.txt | grep pattern'
      const sanitized = sanitizeForCommand(input)
      expect(sanitized).not.toContain('|')
    })

    it('should sanitize backticks for commands', () => {
      const input = '`ls`'
      const sanitized = sanitizeForCommand(input)
      expect(sanitized).not.toContain('`')
    })

    it('should sanitize path traversal', () => {
      const input = '../../../etc/passwd'
      const sanitized = sanitizeForCommand(input)
      expect(sanitized).not.toContain('../')
    })
  })

  describe('HTML Injection Prevention', () => {
    it('should sanitize HTML tags', () => {
      const maliciousInput = '<script>alert(1)</script>'
      const sanitized = sanitizeForHTML(maliciousInput)
      expect(sanitized).toContain('<script>')
      expect(sanitized).not.toContain('<script>')
    })

    it('should sanitize HTML attributes', () => {
      const maliciousInput = '" onload="alert(1)"'
      const sanitized = sanitizeForHTML(maliciousInput)
      expect(sanitized).not.toContain('onload=')
    })

    it('should preserve safe content', () => {
      const safeInput = 'Hello World!'
      const sanitized = sanitizeForHTML(safeInput)
      expect(sanitized).toBe('Hello World!')
    })
  })

  describe('LDAP Injection Prevention', () => {
    const sanitizeForLDAP = (input: string): string => {
      return input
        .replace(/[()\\;,=]/g, '\\$&')
        .replace(/\*/g, '\\2a')
        .replace(/\0/g, '')
    }

    it('should sanitize LDAP special characters', () => {
      const maliciousInput = 'admin)(cn=*'
      const sanitized = sanitizeForLDAP(maliciousInput)
      expect(sanitized).toBe('admin\\)\\(\\*')
    })

    it('should sanitize null bytes', () => {
      const maliciousInput = 'admin\x00'
      const sanitized = sanitizeForLDAP(maliciousInput)
      expect(sanitized).not.toContain('\x00')
    })

    it('should sanitize wildcard characters', () => {
      const maliciousInput = 'admin*'
      const sanitized = sanitizeForLDAP(maliciousInput)
      expect(sanitized).toBe('admin\\2a')
    })
  })

  describe('XPath Injection Prevention', () => {
    const sanitizeForXPath = (input: string): string => {
      return input
        .replace(/[']/g, "\\'")
        .replace(/["]/g, '\\"')
        .replace(/\[/g, '\\[')
        .replace(/\]/g, '\\]')
    }

    it('should sanitize single quotes', () => {
      const maliciousInput = "admin' or '1'='1"
      const sanitized = sanitizeForXPath(maliciousInput)
      expect(sanitized).toBe("admin\\' or \\'1\\'=\\'1")
    })

    it('should sanitize brackets', () => {
      const maliciousInput = 'admin][test'
      const sanitized = sanitizeForXPath(maliciousInput)
      expect(sanitized).toBe('admin\\]\\[test')
    })
  })
})
