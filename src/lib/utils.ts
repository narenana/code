import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(price)
}

export function checkCompatibility(
  specA: string | number | undefined,
  specB: string | number | undefined
): boolean {
  if (specA === undefined || specB === undefined) return false
  return String(specA).trim().toLowerCase() === String(specB).trim().toLowerCase()
}
