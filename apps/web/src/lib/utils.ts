import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(value?: string | null) {
  if (!value) return 'Unknown';
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function truncate(value: string, max = 90) {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

export function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return 'Something went wrong.';
}
