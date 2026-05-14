"use client";

import {
  ArrowUpRight,
  Download,
  FileSpreadsheet,
  FileText,
  Globe,
  History,
  Info,
  Table2,
} from "lucide-react";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { useI18n } from "@/src/i18n/provider";
import { formatDateTime, formatNumber } from "@/src/lib/format";
import { API_URL } from "@/src/lib/constants";

type ArtifactCard = {
  id: string;
  title: string;
  description: string;
  href: string | null;
  format: string;
  icon: React.ComponentType<{ className?: string }>;
  availability: string;
};

const copy = {
  ru: {
    title: "Отчёты",
    desc: "Локальные файлы текущего анализа: Excel-отчёт, HTML-дашборд и CSV-таблицы.",
    available: "Доступных артефактов",
    lastRun: "Последний запуск",
    file: "Файл запуска",
    status: "Статус",
    noData: "Нет данных",
    ready: "Артефакты готовы",
    needsAnalysis: "Нужен анализ",
    startFirst: "Сначала запустите анализ",
    startText: "После анализа здесь появятся реальные локальные файлы: Excel-отчёт, HTML-дашборд и CSV-выгрузки.",
    goHome: "Перейти на главную",
    openHistory: "Открыть историю",
    download: "Скачать",
    open: "Открыть",
    afterAnalysis: "Нет файла",
    artifacts: [
      {
        title: "Excel-отчёт",
        description: "Основной локальный отчёт по текущему анализу с таблицами и сводкой.",
        ready: "Готов к скачиванию",
        pending: "Появится после анализа",
      },
      {
        title: "HTML-дашборд",
        description: "Локальный HTML-артефакт с визуализацией текущего анализа.",
        ready: "Готов к открытию",
        pending: "Появится после анализа",
      },
      {
        title: "CSV рекомендаций",
        description: "Таблица с рекомендациями по SKU для закупочного плана.",
        ready: "Готов к скачиванию",
        pending: "Появится после анализа",
      },
      {
        title: "Матрица ABC/XYZ",
        description: "CSV с сегментацией товаров и управленческими действиями.",
        ready: "Готов к скачиванию",
        pending: "Появится после анализа",
      },
    ],
  },
  en: {
    title: "Reports",
    desc: "Local artifacts for the current analysis without simulated export jobs.",
    available: "Available artifacts",
    lastRun: "Last run",
    file: "Run file",
    status: "Status",
    noData: "No data",
    ready: "Artifacts ready",
    needsAnalysis: "Analysis needed",
    startFirst: "Run an analysis first",
    startText: "After analysis, real local files appear here: Excel report, HTML dashboard and CSV exports.",
    goHome: "Go to home",
    openHistory: "Open history",
    download: "Download",
    open: "Open",
    afterAnalysis: "Available after analysis",
    artifacts: [
      {
        title: "Excel report",
        description: "Main local report for the current analysis with tables and summary.",
        ready: "Ready to download",
        pending: "Available after analysis",
      },
      {
        title: "HTML dashboard",
        description: "Local HTML artifact with current analysis visualization.",
        ready: "Ready to open",
        pending: "Available after analysis",
      },
      {
        title: "Recommendations CSV",
        description: "SKU recommendation table for the purchase plan.",
        ready: "Ready to download",
        pending: "Available after analysis",
      },
      {
        title: "ABC/XYZ matrix",
        description: "CSV with product segmentation and management actions.",
        ready: "Ready to download",
        pending: "Available after analysis",
      },
    ],
  },
} as const;

export default function ReportsPage() {
  const state = useDashboardState();
  const { locale } = useI18n();
  const text = copy[locale];
  const hasAnalysis = Boolean(state.result);
  const artifactCopies = text.artifacts;

  const artifacts: ArtifactCard[] = [
    {
      id: "excel-report",
      title: artifactCopies[0].title,
      description: artifactCopies[0].description,
      href: state.result?.report_url ? withApiBase(state.result.report_url) : null,
      format: "XLSX",
      icon: FileSpreadsheet,
      availability: state.result?.report_url ? artifactCopies[0].ready : artifactCopies[0].pending,
    },
    {
      id: "html-dashboard",
      title: artifactCopies[1].title,
      description: artifactCopies[1].description,
      href: state.result?.dashboard_url ? withApiBase(state.result.dashboard_url) : null,
      format: "HTML",
      icon: Globe,
      availability: state.result?.dashboard_url ? artifactCopies[1].ready : artifactCopies[1].pending,
    },
    {
      id: "recommendations-csv",
      title: artifactCopies[2].title,
      description: artifactCopies[2].description,
      href: state.result?.recommendations_csv_url ? withApiBase(state.result.recommendations_csv_url) : null,
      format: "CSV",
      icon: Table2,
      availability: state.result?.recommendations_csv_url ? artifactCopies[2].ready : artifactCopies[2].pending,
    },
    {
      id: "abcxyz-csv",
      title: artifactCopies[3].title,
      description: artifactCopies[3].description,
      href: state.result?.abc_xyz_matrix_csv_url ? withApiBase(state.result.abc_xyz_matrix_csv_url) : null,
      format: "CSV",
      icon: FileText,
      availability: state.result?.abc_xyz_matrix_csv_url ? artifactCopies[3].ready : artifactCopies[3].pending,
    },
  ];

  return (
    <div className="space-y-7">
      <PageTitle
        title={text.title}
        description={text.desc}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ReportStat
          label={text.available}
          value={formatNumber(artifacts.filter((artifact) => artifact.href).length, 0)}
        />
        <ReportStat
          label={text.lastRun}
          value={state.activeAnalysisCreatedAt ? formatDateTime(state.activeAnalysisCreatedAt) : text.noData}
        />
        <ReportStat
          label={text.file}
          value={state.activeAnalysisFilename ?? text.noData}
        />
        <ReportStat
          label={text.status}
          value={hasAnalysis ? text.ready : text.needsAnalysis}
        />
      </section>

      {!hasAnalysis ? (
        <Surface className="p-6">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-5 w-5 text-[color:var(--muted)]" />
            <div>
              <h2 className="text-base font-semibold">{text.startFirst}</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                {text.startText}
              </p>
              <div className="mt-4 flex flex-wrap gap-2.5">
                <UiButton href="/overview">{text.goHome}</UiButton>
                <UiButton href="/history" variant="secondary" leadingIcon={<History className="h-4 w-4" />}>
                  {text.openHistory}
                </UiButton>
              </div>
            </div>
          </div>
        </Surface>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-2">
        {artifacts.map((artifact) => {
          const Icon = artifact.icon;
          return (
            <Surface key={artifact.id} className="p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-2.5">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-base font-semibold">{artifact.title}</h2>
                      <span className="rounded-md bg-[color:var(--surface-muted)] px-2 py-1 text-xs font-medium text-[color:var(--muted)]">
                        {artifact.format}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-[color:var(--muted)]">{artifact.description}</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3 text-sm text-[color:var(--muted)]">
                {artifact.availability}
              </div>

              <div className="mt-4 flex flex-wrap gap-2.5">
                {artifact.href ? (
                  <a
                    href={artifact.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-4 text-sm font-medium text-white shadow-[var(--shadow-sm)] transition-all duration-200 hover:-translate-y-px"
                  >
                    <Download className="h-4 w-4" />
                    {text.download}
                  </a>
                ) : null}
                {artifact.id === "html-dashboard" && artifact.href ? (
                  <a
                    href={artifact.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
                  >
                    <ArrowUpRight className="h-4 w-4" />
                    {text.open}
                  </a>
                ) : null}
              </div>
            </Surface>
          );
        })}
      </section>
    </div>
  );
}

function ReportStat({ label, value }: { label: string; value: string }) {
  return (
    <Surface className="p-5">
      <p className="text-xs font-medium uppercase text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-sm font-semibold leading-6">{value}</p>
    </Surface>
  );
}

function withApiBase(url: string) {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  return `${API_URL}${url}`;
}
