"use client";

import { m } from "framer-motion";
import {
  ArrowRight,
  Bot,
  Boxes,
  CheckCircle2,
  Clock,
  Download,
  FileSpreadsheet,
  History,
  LineChart,
  PackageCheck,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Upload,
} from "lucide-react";

const story = [
  {
    eyebrow: "Файл",
    title: "Сначала StockPilot проверяет структуру.",
    body: "Пользователь видит, какие колонки найдены, чего не хватает и готов ли файл к анализу. Полная аналитика ещё не запускается.",
    icon: FileSpreadsheet,
    preview: "inspect",
  },
  {
    eyebrow: "Мастер импорта",
    title: "Нестандартные названия колонок больше не блокируют работу.",
    body: "Детерминированное сопоставление предлагает связи между колонками, а пользователь подтверждает их вручную перед нормализацией файла.",
    icon: SlidersHorizontal,
    preview: "mapping",
  },
  {
    eyebrow: "Анализ",
    title: "После загрузки виден рабочий итог, а не витрина графиков.",
    body: "Главная отвечает на вопрос: что требует внимания сегодня, где риск дефицита и куда перейти дальше.",
    icon: Sparkles,
    preview: "summary",
  },
  {
    eyebrow: "Закупки",
    title: "Рекомендация превращается в решение.",
    body: "Статус, итоговое количество, комментарий и корректировка под поставщика сохраняются для конкретного анализа.",
    icon: PackageCheck,
    preview: "planning",
  },
  {
    eyebrow: "Надёжность",
    title: "Прогноз объясняет свои ограничения.",
    body: "WAPE, MAE, Bias, надёжность прогноза и предупреждения по данным помогают понять, какие SKU стоит проверить вручную.",
    icon: ShieldCheck,
    preview: "reliability",
  },
  {
    eyebrow: "Поставщики",
    title: "MOQ, упаковка и срок поставки учитываются отдельно от прогноза.",
    body: "StockPilot не меняет исходную рекомендацию, а показывает количество с учётом поставщика и причину корректировки.",
    icon: Boxes,
    preview: "suppliers",
  },
  {
    eyebrow: "Copilot",
    title: "Локальный помощник объясняет, но не принимает решения за пользователя.",
    body: "Ollama qwen2.5:7b получает только компактный контекст анализа и отвечает без внешних AI-провайдеров.",
    icon: Bot,
    preview: "copilot",
  },
  {
    eyebrow: "История и отчёты",
    title: "К анализу можно вернуться позже.",
    body: "Старые запуски, решения закупочного плана, Excel, HTML-дашборд и CSV остаются локальными артефактами.",
    icon: History,
    preview: "reports",
  },
] as const;

export default function LandingPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[color:var(--background)] text-[color:var(--text)]">
      <section className="relative min-h-screen px-5 py-6 md:px-8">
        <LandingBackdrop />
        <div className="relative mx-auto grid min-h-[calc(100vh-3rem)] max-w-[1440px] grid-rows-[auto_1fr_auto]">
          <header className="flex items-center justify-between">
            <div className="text-sm font-semibold">StockPilot AI</div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--surface)]/72 px-3 py-1.5 text-xs text-[color:var(--muted)] shadow-[var(--shadow-sm)] backdrop-blur-2xl">
              <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--success)]" />
              Локально через Ollama
            </div>
          </header>

          <div className="grid items-center gap-10 py-14 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="max-w-4xl">
              <m.div
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.65, ease: [0.2, 0.8, 0.2, 1] }}
                className="mb-6 inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--surface)]/76 px-4 py-2 text-xs font-medium text-[color:var(--muted)] backdrop-blur-2xl"
              >
                <Sparkles className="h-3.5 w-3.5 text-[color:var(--accent)]" />
                Локальное AI-рабочее пространство для операционной команды
              </m.div>
              <m.h1
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.08, duration: 0.75, ease: [0.2, 0.8, 0.2, 1] }}
                className="text-[3.6rem] font-semibold leading-none md:text-[4.8rem] lg:text-[5.4rem]"
              >
                StockPilot AI
              </m.h1>
              <m.p
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.18, duration: 0.72, ease: [0.2, 0.8, 0.2, 1] }}
                className="mt-6 max-w-3xl text-2xl font-medium leading-tight md:text-3xl"
              >
                Локальное AI-рабочее пространство для продаж, запасов и закупок.
              </m.p>
              <m.div
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.28, duration: 0.62, ease: [0.2, 0.8, 0.2, 1] }}
                className="mt-7"
              >
                <a
                  href="/overview"
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-[color:var(--text)] px-6 text-base font-semibold text-[color:var(--background)] shadow-[var(--shadow-soft)] transition hover:-translate-y-0.5"
                >
                  <ArrowRight className="h-4 w-4" />
                  Открыть workspace
                </a>
              </m.div>
              <m.p
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.38, duration: 0.72, ease: [0.2, 0.8, 0.2, 1] }}
                className="mt-7 max-w-2xl text-base leading-7 text-[color:var(--muted)] md:text-lg"
              >
                Загрузите Excel или CSV — StockPilot поможет подготовить файл, оценит запасы, сформирует закупочный план и объяснит рекомендации локально через Ollama.
              </m.p>
            </div>

            <m.div
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: 0.22, duration: 0.85, ease: [0.2, 0.8, 0.2, 1] }}
              className="hidden lg:block"
            >
              <HeroMock />
            </m.div>
          </div>

          <div className="flex items-center justify-between pb-3 text-xs text-[color:var(--muted)]">
            <span>Прокрутите</span>
            <span>Данные остаются локально</span>
          </div>
        </div>
      </section>

      <section className="relative mx-auto max-w-[1440px] px-5 pb-24 md:px-8">
        <div className="absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-[color:var(--line)] to-transparent lg:block" />
        {story.map((step, index) => {
          const Icon = step.icon;
          const isReverse = index % 2 === 1;
          return (
            <m.article
              key={step.title}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: "-22% 0px -18% 0px" }}
              transition={{ duration: 0.76, ease: [0.2, 0.8, 0.2, 1] }}
              className="grid min-h-[86vh] items-center gap-10 py-16 lg:grid-cols-2"
            >
              <div className={isReverse ? "lg:order-2 lg:pl-14" : "lg:pr-14"}>
                <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-[color:var(--surface)]/70 px-3 py-1.5 text-xs text-[color:var(--muted)] shadow-[var(--shadow-sm)] backdrop-blur-xl">
                  <Icon className="h-3.5 w-3.5 text-[color:var(--accent)]" />
                  {String(index + 1).padStart(2, "0")} · {step.eyebrow}
                </div>
                <h2 className="max-w-xl text-4xl font-semibold leading-tight md:text-6xl">{step.title}</h2>
                <p className="mt-5 max-w-lg text-base leading-7 text-[color:var(--muted)]">{step.body}</p>
              </div>
              <m.div
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-20% 0px -20% 0px" }}
                transition={{ delay: 0.12, duration: 0.8, ease: [0.2, 0.8, 0.2, 1] }}
                className={isReverse ? "lg:order-1" : ""}
              >
                <StoryMock kind={step.preview} index={index} />
              </m.div>
            </m.article>
          );
        })}

        <m.section
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
          className="relative overflow-hidden rounded-[2.5rem] border border-[color:var(--line)] bg-[color:var(--surface)]/76 p-8 shadow-[var(--shadow-hard)] backdrop-blur-2xl md:p-12"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,color-mix(in_srgb,var(--accent)_18%,transparent),transparent_34%)]" />
          <div className="relative max-w-3xl">
            <p className="text-sm font-medium text-[color:var(--muted)]">Локально. Из файла. До закупочного решения.</p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight md:text-6xl">Откройте рабочее пространство и пройдите путь на демо-файле.</h2>
            <p className="mt-5 text-base leading-7 text-[color:var(--muted)]">
              StockPilot работает с локальным сервером, Ollama и вашими артефактами анализа. Без внешних AI API и без облачной отправки данных.
            </p>
            <a
              href="/overview"
              className="mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full bg-[color:var(--text)] px-6 text-base font-semibold text-[color:var(--background)] shadow-[var(--shadow-soft)] transition hover:-translate-y-0.5"
            >
              <ArrowRight className="h-4 w-4" />
              Открыть workspace
            </a>
          </div>
        </m.section>
      </section>
    </main>
  );
}

function LandingBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,color-mix(in_srgb,var(--line)_70%,transparent)_1px,transparent_1px),linear-gradient(to_bottom,color-mix(in_srgb,var(--line)_70%,transparent)_1px,transparent_1px)] bg-[size:72px_72px] opacity-30" />
      <div className="absolute left-1/2 top-[-20rem] h-[48rem] w-[72rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,color-mix(in_srgb,var(--accent)_26%,transparent),transparent_62%)] blur-2xl" />
      <div className="absolute bottom-[-22rem] right-[-16rem] h-[42rem] w-[42rem] rounded-full bg-[radial-gradient(circle,color-mix(in_srgb,var(--success)_14%,transparent),transparent_64%)] blur-2xl" />
    </div>
  );
}

function HeroMock() {
  return (
    <div className="relative">
      <div className="absolute inset-8 rounded-[3rem] bg-[color:var(--accent)]/10 blur-3xl" />
      <div className="relative overflow-hidden rounded-[2.25rem] border border-[color:var(--line)] bg-[color:var(--surface)]/78 p-4 shadow-[var(--shadow-hard)] backdrop-blur-2xl">
        <div className="mb-4 flex items-center justify-between rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-3">
          <div>
            <p className="text-sm font-semibold">Закупочный фокус</p>
            <p className="text-xs text-[color:var(--muted)]">пример рабочего экрана · локальный анализ</p>
          </div>
          <span className="rounded-full bg-[color:var(--success-soft)] px-3 py-1 text-xs text-[color:var(--success)]">локально</span>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {[
            ["Срочно докупить", "есть позиции"],
            ["Качество данных", "проверено"],
            ["Предупреждения", "нужно внимание"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-1)] p-4">
              <p className="text-xs text-[color:var(--muted)]">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{value}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-2">
          {[
            ["COF-001", "Кофе арабика 250г", "к заказу"],
            ["TEA-014", "Чай зелёный листовой", "проверить остаток"],
            ["DRY-022", "Сухофрукты ассорти", "избыток"],
          ].map(([sku, name, action]) => (
            <div key={sku} className="grid grid-cols-[5rem_1fr_auto] items-center gap-3 rounded-2xl bg-[color:var(--surface-2)] px-4 py-3 text-sm">
              <span className="font-semibold">{sku}</span>
              <span className="truncate text-[color:var(--muted)]">{name}</span>
              <span className="rounded-full bg-[color:var(--accent-soft)] px-3 py-1 text-xs text-[color:var(--accent)]">{action}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StoryMock({ kind, index }: { kind: (typeof story)[number]["preview"]; index: number }) {
  return (
    <div className="relative">
      <div className="absolute inset-8 rounded-[3rem] bg-[color:var(--accent)]/10 blur-3xl" />
      <div className="relative overflow-hidden rounded-[2.25rem] border border-[color:var(--line)] bg-[color:var(--surface)]/78 p-5 shadow-[var(--shadow-hard)] backdrop-blur-2xl">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold">{mockTitles[kind]}</p>
            <p className="text-xs text-[color:var(--muted)]">шаг {String(index + 1).padStart(2, "0")} · локальный процесс</p>
          </div>
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--danger)]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--warning)]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--success)]" />
          </div>
        </div>
        {kind === "inspect" ? <InspectMock /> : null}
        {kind === "mapping" ? <MappingMock /> : null}
        {kind === "summary" ? <SummaryMock /> : null}
        {kind === "planning" ? <PlanningMock /> : null}
        {kind === "reliability" ? <ReliabilityMock /> : null}
        {kind === "suppliers" ? <SuppliersMock /> : null}
        {kind === "copilot" ? <CopilotMock /> : null}
        {kind === "reports" ? <ReportsMock /> : null}
      </div>
    </div>
  );
}

const mockTitles: Record<(typeof story)[number]["preview"], string> = {
  inspect: "Предварительная проверка файла",
  mapping: "Сопоставление колонок",
  summary: "Рабочая сводка",
  planning: "Закупочные решения",
  reliability: "Прогноз и надёжность",
  suppliers: "Ограничения поставщика",
  copilot: "Локальный Copilot",
  reports: "История и отчёты",
};

function InspectMock() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        {["CSV", "Колонки найдены", "Готово к проверке"].map((item) => (
          <div key={item} className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4 text-sm font-semibold">
            {item}
          </div>
        ))}
      </div>
      <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
        <PreviewRow icon={<CheckCircle2 className="h-4 w-4" />} title="date" value="дата продаж" tone="success" />
        <PreviewRow icon={<CheckCircle2 className="h-4 w-4" />} title="sku" value="артикул товара" tone="success" />
        <PreviewRow icon={<CheckCircle2 className="h-4 w-4" />} title="stock_on_hand" value="остаток на складе" tone="success" />
      </div>
      <div className="rounded-3xl border border-[color:var(--warning)] bg-[color:var(--warning-soft)] p-4 text-sm text-[color:var(--warning)]">
        Предупреждения показываются до запуска полного анализа.
      </div>
    </div>
  );
}

function MappingMock() {
  return (
    <div className="space-y-3">
      {[
        ["date", "Дата продажи", "найдено"],
        ["sku", "Артикул", "найдено"],
        ["revenue", "Сумма", "проверьте"],
        ["stock_on_hand", "Остаток", "найдено"],
      ].map(([field, source, status]) => (
        <div key={field} className="grid grid-cols-[1fr_1fr_auto] items-center gap-3 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-3 text-sm">
          <span className="font-semibold">{field}</span>
          <span className="truncate text-[color:var(--muted)]">{source}</span>
          <span className="rounded-full bg-[color:var(--accent-soft)] px-3 py-1 text-xs text-[color:var(--accent)]">{status}</span>
        </div>
      ))}
    </div>
  );
}

function SummaryMock() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        {[
          ["Дефицит", "есть сигналы"],
          ["Избыток", "проверить"],
          ["Качество", "принято"],
        ].map(([label, value]) => (
          <div key={label} className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
            <p className="text-xs text-[color:var(--muted)]">{label}</p>
            <p className="mt-2 text-lg font-semibold">{value}</p>
          </div>
        ))}
      </div>
      <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <Clock className="h-4 w-4 text-[color:var(--accent)]" />
          Что сделать сегодня
        </div>
        <div className="space-y-2 text-sm text-[color:var(--muted)]">
          <p>Проверить товары с высоким риском дефицита.</p>
          <p>Открыть закупочный план и зафиксировать решения.</p>
          <p>Скачать локальный отчёт для команды.</p>
        </div>
      </div>
    </div>
  );
}

function PlanningMock() {
  return (
    <div className="space-y-3">
      {[
        ["COF-001", "высокий", "к заказу", "новая"],
        ["TEA-014", "средний", "проверить", "принято"],
        ["DRY-022", "избыток", "не закупать", "комментарий"],
      ].map(([sku, risk, qty, status]) => (
        <div key={sku} className="grid grid-cols-[5rem_1fr_1fr_auto] items-center gap-3 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] px-4 py-3 text-sm">
          <span className="font-semibold">{sku}</span>
          <span className="text-[color:var(--muted)]">{risk}</span>
          <span>{qty}</span>
          <span className="rounded-full bg-[color:var(--surface-3)] px-3 py-1 text-xs text-[color:var(--muted)]">{status}</span>
        </div>
      ))}
    </div>
  );
}

function ReliabilityMock() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        {["WAPE", "MAE", "Bias"].map((metric) => (
          <div key={metric} className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
            <p className="text-xs text-[color:var(--muted)]">{metric}</p>
            <div className="mt-3 h-2 rounded-full bg-[color:var(--surface-3)]">
              <div className="h-2 w-2/3 rounded-full bg-[color:var(--accent)]" />
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
          <LineChart className="h-4 w-4 text-[color:var(--accent)]" />
          Распределение надёжности SKU
        </div>
        <div className="flex h-28 items-end gap-3">
          {["bg-[color:var(--success)] h-24", "bg-[color:var(--warning)] h-16", "bg-[color:var(--danger)] h-10"].map((className, i) => (
            <div key={i} className={`w-full rounded-t-2xl ${className}`} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SuppliersMock() {
  return (
    <div className="grid gap-3">
      <PreviewRow icon={<Boxes className="h-4 w-4" />} title="Поставщик" value="срок поставки указан" tone="accent" />
      <PreviewRow icon={<PackageCheck className="h-4 w-4" />} title="MOQ" value="учитывается в количестве" tone="warning" />
      <PreviewRow icon={<CheckCircle2 className="h-4 w-4" />} title="Кратность упаковки" value="округление видно отдельно" tone="success" />
      <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4 text-sm text-[color:var(--muted)]">
        Исходная рекомендация сохраняется, а корректировка поставщика показывается отдельным слоем.
      </div>
    </div>
  );
}

function CopilotMock() {
  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
        <p className="text-sm font-semibold">Вопрос</p>
        <p className="mt-2 text-sm text-[color:var(--muted)]">Какие товары проверить перед закупкой?</p>
      </div>
      <div className="rounded-3xl border border-[color:var(--accent)] bg-[color:var(--accent-soft)] p-4 text-sm text-[color:var(--accent)]">
        Проверьте SKU с низкой надёжностью и позиции, где риск дефицита сочетается с коротким покрытием запасов.
      </div>
      <PreviewRow icon={<Bot className="h-4 w-4" />} title="Источник ответа" value="локальная Ollama" tone="success" />
    </div>
  );
}

function ReportsMock() {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <PreviewRow icon={<Download className="h-4 w-4" />} title="Excel" value="сводка и закупки" tone="accent" />
      <PreviewRow icon={<FileSpreadsheet className="h-4 w-4" />} title="HTML" value="управленческий отчёт" tone="success" />
      <PreviewRow icon={<History className="h-4 w-4" />} title="История" value="открытие старого анализа" tone="warning" />
      <PreviewRow icon={<Upload className="h-4 w-4" />} title="CSV" value="план закупки" tone="accent" />
    </div>
  );
}

function PreviewRow({
  icon,
  title,
  value,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  tone: "success" | "warning" | "accent";
}) {
  const toneClass = {
    success: "bg-[color:var(--success-soft)] text-[color:var(--success)]",
    warning: "bg-[color:var(--warning-soft)] text-[color:var(--warning)]",
    accent: "bg-[color:var(--accent-soft)] text-[color:var(--accent)]",
  };
  return (
    <div className="grid grid-cols-[2.5rem_1fr_auto] items-center gap-3 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-1)] px-3 py-3">
      <div className={`grid h-9 w-9 place-items-center rounded-2xl ${toneClass[tone]}`}>{icon}</div>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{title}</p>
        <p className="truncate text-xs text-[color:var(--muted)]">{value}</p>
      </div>
      <CheckCircle2 className="h-4 w-4 text-[color:var(--muted)]" />
    </div>
  );
}
