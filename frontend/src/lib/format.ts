let activeLocale: "ru-RU" | "en-US" = "ru-RU";

export function setFormattingLocale(locale: "ru" | "en") {
  activeLocale = locale === "en" ? "en-US" : "ru-RU";
}

export function formatMoney(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat(activeLocale, {
    style: "currency",
    currency: activeLocale === "en-US" ? "USD" : "RUB",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatCompactMoney(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat(activeLocale, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatNumber(value?: number | null, digits = 1): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat(activeLocale, {
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatPercent(value?: number | null, digits = 1): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return `${new Intl.NumberFormat(activeLocale, {
    maximumFractionDigits: digits,
  }).format(value)}%`;
}

export function formatRisk(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return formatPercent(value * 100, 1);
}

export function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(activeLocale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatShortDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(activeLocale, {
    day: "2-digit",
    month: "short",
  }).format(date);
}
