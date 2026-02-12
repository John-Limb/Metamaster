import { clsx, type ClassValue } from 'clsx'

/**
 * Utility function for conditional class names (Tailwind CSS)
 * Combines clsx with tailwind-merge functionality
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}
