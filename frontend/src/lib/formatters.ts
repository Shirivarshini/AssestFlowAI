export function formatCurrency(amount: number, currency = 'INR'): string {
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  });

  return formatter.format(amount);
}

export function formatCompactCurrency(amount: number, currency = 'INR'): string {
  if (amount >= 10000000) {
    return `${(amount / 10000000).toFixed(2)} Cr`;
  }

  if (amount >= 100000) {
    return `${(amount / 100000).toFixed(2)} L`;
  }

  return formatCurrency(amount, currency);
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

export function formatRisk(value: number): string {
  return `${Math.round(value)} / 100`;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
