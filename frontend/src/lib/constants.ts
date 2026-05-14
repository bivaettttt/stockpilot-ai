export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const priorityLabelsByLocale: Record<"ru" | "en", Record<string, string>> = {
  ru: {
    critical: "Критический",
    high: "Высокий",
    medium: "Средний",
    low: "Низкий",
    info: "Информация",
  },
  en: {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
    info: "Info",
  },
};

const actionLabelsByLocale: Record<"ru" | "en", Record<string, string>> = {
  ru: {
    urgent: "Срочно",
    planned: "Планово",
    monitor: "Мониторинг",
    no_action: "Без действия",
  },
  en: {
    urgent: "Urgent",
    planned: "Planned",
    monitor: "Monitor",
    no_action: "No action",
  },
};

export function getPriorityLabels(locale: "ru" | "en") {
  return priorityLabelsByLocale[locale];
}

export function getActionLabels(locale: "ru" | "en") {
  return actionLabelsByLocale[locale];
}
