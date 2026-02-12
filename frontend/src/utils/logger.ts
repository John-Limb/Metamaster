/**
 * Logger utility for debugging and monitoring
 */

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'

const LogLevelValues = {
  DEBUG: 'DEBUG' as LogLevel,
  INFO: 'INFO' as LogLevel,
  WARN: 'WARN' as LogLevel,
  ERROR: 'ERROR' as LogLevel,
}

export interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  data?: any
  context?: string
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 500
  private minLevel: LogLevel = import.meta.env.DEV ? LogLevelValues.DEBUG : LogLevelValues.INFO

  /**
   * Log debug message
   */
  public debug(message: string, data?: any, context?: string): void {
    this.log(LogLevelValues.DEBUG, message, data, context)
  }

  /**
   * Log info message
   */
  public info(message: string, data?: any, context?: string): void {
    this.log(LogLevelValues.INFO, message, data, context)
  }

  /**
   * Log warning message
   */
  public warn(message: string, data?: any, context?: string): void {
    this.log(LogLevelValues.WARN, message, data, context)
  }

  /**
   * Log error message
   */
  public error(message: string, data?: any, context?: string): void {
    this.log(LogLevelValues.ERROR, message, data, context)
  }

  /**
   * Internal log method
   */
  private log(level: LogLevel, message: string, data?: any, context?: string): void {
    // Check if log level should be logged
    if (!this.shouldLog(level)) {
      return
    }

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
      context,
    }

    this.logs.push(entry)

    // Keep only recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      this.logToConsole(entry)
    }
  }

  /**
   * Check if log level should be logged
   */
  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = [LogLevelValues.DEBUG, LogLevelValues.INFO, LogLevelValues.WARN, LogLevelValues.ERROR]
    const minIndex = levels.indexOf(this.minLevel)
    const currentIndex = levels.indexOf(level)
    return currentIndex >= minIndex
  }

  /**
   * Log to console
   */
  private logToConsole(entry: LogEntry): void {
    const prefix = `[${entry.timestamp}] [${entry.level}]${entry.context ? ` [${entry.context}]` : ''}`

    switch (entry.level) {
      case LogLevelValues.DEBUG:
        console.debug(prefix, entry.message, entry.data)
        break
      case LogLevelValues.INFO:
        console.info(prefix, entry.message, entry.data)
        break
      case LogLevelValues.WARN:
        console.warn(prefix, entry.message, entry.data)
        break
      case LogLevelValues.ERROR:
        console.error(prefix, entry.message, entry.data)
        break
    }
  }

  /**
   * Get all logs
   */
  public getLogs(): LogEntry[] {
    return [...this.logs]
  }

  /**
   * Get logs by level
   */
  public getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter((log) => log.level === level)
  }

  /**
   * Get logs by context
   */
  public getLogsByContext(context: string): LogEntry[] {
    return this.logs.filter((log) => log.context === context)
  }

  /**
   * Clear logs
   */
  public clearLogs(): void {
    this.logs = []
  }

  /**
   * Export logs as JSON
   */
  public exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }

  /**
   * Export logs as CSV
   */
  public exportLogsAsCSV(): string {
    const headers = ['Timestamp', 'Level', 'Message', 'Context', 'Data']
    const rows = this.logs.map((log) => [
      log.timestamp,
      log.level,
      log.message,
      log.context || '',
      JSON.stringify(log.data || ''),
    ])

    const csv = [headers, ...rows].map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')

    return csv
  }

  /**
   * Set minimum log level
   */
  public setMinLevel(level: LogLevel): void {
    this.minLevel = level
  }

  /**
   * Log API request
   */
  public logApiRequest(method: string, url: string, data?: any): void {
    this.info(`API Request: ${method} ${url}`, data, 'API')
  }

  /**
   * Log API response
   */
  public logApiResponse(method: string, url: string, status: number, data?: any): void {
    this.info(`API Response: ${method} ${url} (${status})`, data, 'API')
  }

  /**
   * Log API error
   */
  public logApiError(method: string, url: string, error: any): void {
    this.error(`API Error: ${method} ${url}`, error, 'API')
  }

  /**
   * Log performance metric
   */
  public logPerformance(name: string, duration: number): void {
    this.info(`Performance: ${name} took ${duration}ms`, { duration }, 'Performance')
  }
}

export const logger = new Logger()
