"use client";

import { useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Download, FileText, FolderOpen, History, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { formatDateTime, formatNumber } from "@/src/lib/format";
import { API_URL } from "@/src/lib/constants";
import { cn } from "@/src/lib/utils";

export default function HistoryPage() {
  const router = useRouter();
  const state = useDashboardState();
  const [openingRunId, setOpeningRunId] = useState<string | null>(null);

  async function handleOpenAnalysis(runId: string, destination: "/overview" | "/reports" = "/overview") {
    setOpeningRunId(runId);
    try {
      await state.openHistoryRun(runId);
      router.push(destination);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Не удалось открыть сохранённый результат анализа."
      );
    } finally {
      setOpeningRunId(null);
    }
  }

  if (!state.isHistoryLoading && state.history.length === 0) {
    return (
      <div className="space-y-6">
        <PageTitle title="История анализов" description="Сохранённые локальные результаты и отчёты." />
        <Surface className="p-6 md:p-7">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-md bg-[color:var(--surface-muted)] px-3 py-1.5 text-sm text-[color:var(--muted)]">
              <History className="h-4 w-4" />
              История пока пуста
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">История анализов пока пуста</h2>
              <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)]">
                Загрузите файл продаж и остатков, чтобы StockPilot сохранил результат анализа и позволил вернуться к нему позже.
              </p>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <UiButton href="/overview#upload-panel">Загрузить файл</UiButton>
              <a
                href={`${API_URL}/files/demo`}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
              >
                <Sparkles className="h-4 w-4" />
                Попробовать демо-файл
              </a>
            </div>
          </div>
        </Surface>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageTitle title="История анализов" description="Открывайте прошлые запуски, отчёты и сохранённые решения." />

      <div className="flex flex-wrap gap-2">
        <input
          value={state.historyFileFilter}
          onChange={(e) => state.setHistoryFileFilter(e.target.value)}
          className="h-10 min-w-[240px] rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-sm"
          placeholder="Фильтр по имени файла"
        />
        <select
          value={state.historyStatusFilter}
          onChange={(e) => state.setHistoryStatusFilter(e.target.value)}
          className="h-10 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-sm"
        >
          <option value="all">Все статусы</option>
          <option value="success">Завершено</option>
          <option value="failed">Ошибка</option>
        </select>
      </div>

      <div className="grid gap-4">
        {state.isHistoryLoading
          ? Array.from({ length: 5 }).map((_, index) => (
              <Surface key={index} className="p-5">
                <div className="space-y-3">
                  <div className="h-5 w-48 animate-pulse rounded bg-[color:var(--surface-muted)]" />
                  <div className="h-4 w-72 animate-pulse rounded bg-[color:var(--surface-muted)]" />
                  <div className="h-4 w-full animate-pulse rounded bg-[color:var(--surface-muted)]" />
                </div>
              </Surface>
            ))
          : state.history.map((item) => {
              const fileCount = [item.report_url, item.dashboard_url, item.recommendations_csv_url, item.abc_xyz_matrix_csv_url].filter(Boolean).length;
              const isOpening = openingRunId === item.id;
              return (
                <Surface key={item.id} className="p-5">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge tone={item.status === "success" ? "success" : "critical"}>
                          {item.status === "success" ? "Завершено" : "Ошибка"}
                        </StatusBadge>
                        {item.has_saved_decisions ? <StatusBadge tone="neutral">Сохранённые решения</StatusBadge> : null}
                        {item.has_result_snapshot ? <StatusBadge tone="neutral">Результат доступен</StatusBadge> : null}
                      </div>
                      <div>
                        <h2 className="text-base font-semibold">{item.original_filename}</h2>
                        <p className="mt-1 text-sm text-[color:var(--muted)]">
                          Запуск {formatDateTime(item.created_at)}
                        </p>
                      </div>
                      <div className="grid gap-2 text-sm text-[color:var(--muted)] sm:grid-cols-2 xl:grid-cols-4">
                        <Meta label="Период данных" value={item.summary_metrics.date_range_days ? `${formatNumber(item.summary_metrics.date_range_days, 0)} дн.` : "Нет данных"} />
                        <Meta label="SKU" value={item.summary_metrics.unique_products ? formatNumber(item.summary_metrics.unique_products, 0) : "Нет данных"} />
                        <Meta label="Строк" value={item.data_quality?.total_rows ? formatNumber(item.data_quality.total_rows, 0) : "Нет данных"} />
                        <Meta label="Отчёты" value={fileCount > 0 ? `${fileCount} файла` : "Нет файлов"} />
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <UiButton
                        onClick={() => void handleOpenAnalysis(item.id)}
                        loading={isOpening}
                        disabled={!item.has_result_snapshot}
                        leadingIcon={<FolderOpen className="h-4 w-4" />}
                      >
                        Открыть анализ
                      </UiButton>
                      <UiButton
                        variant="secondary"
                        onClick={() => void handleOpenAnalysis(item.id, "/reports")}
                        disabled={!item.has_result_snapshot}
                        leadingIcon={<FileText className="h-4 w-4" />}
                      >
                        Открыть отчёты
                      </UiButton>
                      {item.report_url ? (
                        <a
                          href={withApiBase(item.report_url)}
                          target="_blank"
                          rel="noreferrer"
                          className={cn(
                            "inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-4 text-sm font-medium text-[color:var(--text)] transition-all duration-200 hover:border-[color:var(--border-strong)] hover:bg-[color:var(--surface-muted)]"
                          )}
                        >
                          <Download className="h-4 w-4" />
                          Скачать отчёт
                        </a>
                      ) : null}
                    </div>
                  </div>
                </Surface>
              );
            })}
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-[color:var(--muted)]">
          {state.historyPagination
            ? `Страница ${state.historyPagination.page} из ${Math.max(state.historyPagination.total_pages, 1)}`
            : "Нет данных"}
        </div>
        <div className="flex gap-2">
          <button
            className="h-9 rounded-lg border border-[color:var(--border)] px-3 text-sm disabled:opacity-50"
            onClick={() => state.setHistoryPage(Math.max(1, state.historyPage - 1))}
            disabled={state.historyPage === 1}
          >
            Назад
          </button>
          <button
            className="h-9 rounded-lg border border-[color:var(--border)] px-3 text-sm disabled:opacity-50"
            onClick={() => state.setHistoryPage(state.historyPage + 1)}
            disabled={
              !state.historyPagination || state.historyPage >= state.historyPagination.total_pages
            }
          >
            Дальше
          </button>
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-3 py-2">
      <p className="text-xs uppercase">{label}</p>
      <p className="mt-1 font-medium text-[color:var(--text)]">{value}</p>
    </div>
  );
}

function StatusBadge({
  children,
  tone,
}: {
  children: ReactNode;
  tone: "success" | "critical" | "neutral";
}) {
  const toneClass =
    tone === "success"
      ? "border-[color:var(--success)] bg-[color:var(--success-soft)] text-[color:var(--success)]"
      : tone === "critical"
        ? "border-[color:var(--danger)] bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
        : "border-[color:var(--border)] bg-[color:var(--surface-muted)] text-[color:var(--muted)]";
  return <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", toneClass)}>{children}</span>;
}

function withApiBase(url: string) {
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  return `${API_URL}${url}`;
}
