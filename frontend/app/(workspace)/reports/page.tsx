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
    desc: "HTML — управленческий отчёт для руководителя. Excel и CSV — рабочие файлы для анализа и закупок.",
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
    primaryTitle: "Основной отчёт",
    workingTitle: "Рабочие файлы",
    htmlNote: "Для владельца бизнеса: сводка, графики, закупки, риски и качество данных.",
    excelNote: "Для аналитика или закупщика: таблицы, фильтры, детализация и рабочие выгрузки.",
    artifacts: [
      {
        title: "HTML-управленческий отчёт",
        description: "Главный презентационный отчёт: executive summary, KPI, графики, риски и закупочный план.",
        ready: "Готов к открытию",
        pending: "Появится после анализа",
      },
      {
        title: "Excel-книга",
        description: "Рабочая книга с таблицами, фильтрами, сводкой и детализацией для закупок.",
        ready: "Готов к скачиванию",
        pending: "Появится после анализа",
      },
      {
        title: "CSV закупочного плана",
        description: "Человекочитаемая таблица рекомендаций для закупочного плана.",
        ready: "Готов к скачиванию",
        pending: "Появится после анализа",
      },
      {
        title: "Raw CSV рекомендаций",
        description: "Техническая выгрузка рекомендаций для дальнейшей обработки.",
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
    desc: "HTML is the management report. Excel and CSV are working files for analysis and procurement.",
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
    primaryTitle: "Primary report",
    workingTitle: "Working files",
    htmlNote: "For business owners: summary, visuals, procurement, risks and data quality.",
    excelNote: "For analysts and buyers: tables, filters, details and working exports.",
    artifacts: [
      {
        title: "HTML management report",
        description: "Primary presentation report with executive summary, KPIs, visuals, risks and purchase plan.",
        ready: "Ready to open",
        pending: "Available after analysis",
      },
      {
        title: "Excel workbook",
        description: "Working workbook with tables, filters, summary and procurement details.",
        ready: "Ready to download",
        pending: "Available after analysis",
      },
      {
        title: "Purchase plan CSV",
        description: "Human-readable recommendation table for procurement work.",
        ready: "Ready to download",
        pending: "Available after analysis",
      },
      {
        title: "Raw recommendations CSV",
        description: "Technical recommendation export for further processing.",
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
      id: "html-dashboard",
      title: artifactCopies[0].title,
      description: artifactCopies[0].description,
      href: state.result?.dashboard_url ? withApiBase(state.result.dashboard_url) : null,
      format: "HTML",
      icon: Globe,
      availability: state.result?.dashboard_url ? artifactCopies[0].ready : artifactCopies[0].pending,
    },
    {
      id: "excel-report",
      title: artifactCopies[1].title,
      description: artifactCopies[1].description,
      href: state.result?.report_url ? withApiBase(state.result.report_url) : null,
      format: "XLSX",
      icon: FileSpreadsheet,
      availability: state.result?.report_url ? artifactCopies[1].ready : artifactCopies[1].pending,
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
      id: "recommendations-raw-csv",
      title: artifactCopies[3].title,
      description: artifactCopies[3].description,
      href: state.result?.recommendations_raw_csv_url ? withApiBase(state.result.recommendations_raw_csv_url) : null,
      format: "CSV",
      icon: Table2,
      availability: state.result?.recommendations_raw_csv_url ? artifactCopies[3].ready : artifactCopies[3].pending,
    },
    {
      id: "abcxyz-csv",
      title: artifactCopies[4].title,
      description: artifactCopies[4].description,
      href: state.result?.abc_xyz_matrix_csv_url ? withApiBase(state.result.abc_xyz_matrix_csv_url) : null,
      format: "CSV",
      icon: FileText,
      availability: state.result?.abc_xyz_matrix_csv_url ? artifactCopies[4].ready : artifactCopies[4].pending,
    },
  ];
  const primaryArtifact = artifacts[0] as ArtifactCard;
  const workingArtifacts = artifacts.slice(1);

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

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-[color:var(--muted)]">{text.primaryTitle}</h2>
          <p className="mt-1 text-sm text-[color:var(--muted)]">{text.htmlNote}</p>
        </div>
        <div className="grid gap-4">
          <ArtifactSurface artifact={primaryArtifact} openText={text.open} downloadText={text.download} />
        </div>
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-[color:var(--muted)]">{text.workingTitle}</h2>
          <p className="mt-1 text-sm text-[color:var(--muted)]">{text.excelNote}</p>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
        {workingArtifacts.map((artifact) => {
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
        </div>
      </section>
    </div>
  );
}

function ArtifactSurface({
  artifact,
  downloadText,
  openText,
}: {
  artifact: ArtifactCard;
  downloadText: string;
  openText: string;
}) {
  const Icon = artifact.icon;
  return (
    <Surface className="p-6">
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
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
            <div className="mt-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-3 text-sm text-[color:var(--muted)]">
              {artifact.availability}
            </div>
          </div>
        </div>
        {artifact.href ? (
          <div className="flex flex-wrap gap-2.5">
            <a href={artifact.href} target="_blank" rel="noreferrer" className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-4 text-sm font-medium text-white shadow-[var(--shadow-sm)] transition-all duration-200 hover:-translate-y-px">
              <ArrowUpRight className="h-4 w-4" />
              {openText}
            </a>
            <a href={artifact.href} target="_blank" rel="noreferrer" className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]">
              <Download className="h-4 w-4" />
              {downloadText}
            </a>
          </div>
        ) : null}
      </div>
    </Surface>
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
