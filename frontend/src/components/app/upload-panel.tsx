"use client";

import { AnimatePresence, m } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Bot,
  Download,
  FileSpreadsheet,
  PlayCircle,
  Send,
  UploadCloud,
  XCircle,
} from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { requestImportAssist } from "@/src/lib/api/copilot";
import { downloadDemoFile } from "@/src/lib/api/upload";
import { API_URL } from "@/src/lib/constants";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import { UiButton } from "@/src/components/app/ui";
import { cn } from "@/src/lib/utils";
import type {
  ImportAssistContext,
  ImportAssistResponse,
  ImportInspectResponse,
  MappingSuggestionItem,
  MappingWarningResponse,
} from "@/src/types/api";

const ACCEPTED_TYPES = {
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
};

const REQUIRED_COLUMNS = [
  ["date", "дата"],
  ["sku", "артикул"],
  ["product_name", "название товара"],
  ["quantity_sold", "сколько продано"],
  ["revenue", "выручка"],
  ["stock_on_hand", "остаток на складе"],
] as const;

const OPTIONAL_COLUMNS = [
  "category",
  "purchase_price",
  "selling_price",
  "supplier",
  "promotion_flag",
] as const;

const STOCKPILOT_FIELDS = [
  ["date", "Дата продажи или остатка"],
  ["sku", "Артикул товара"],
  ["product_name", "Название товара"],
  ["quantity_sold", "Количество проданных единиц"],
  ["revenue", "Выручка по строке"],
  ["stock_on_hand", "Остаток на складе"],
  ["category", "Категория товара"],
  ["purchase_price", "Закупочная цена"],
  ["selling_price", "Цена продажи"],
  ["supplier", "Поставщик"],
  ["promotion_flag", "Признак акции"],
] as const;

const IMPORT_ASSIST_QUICK_QUESTIONS = [
  "Что не так с моим файлом?",
  "Какие колонки обязательны?",
  "Проверь сопоставление колонок",
  "Почему файл не готов к анализу?",
  "Как исправить файл?",
] as const;

export function UploadPanel() {
  const state = useDashboardState();
  const [demoLoading, setDemoLoading] = useState(false);
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState<ImportAssistResponse | null>(null);
  const [copilotError, setCopilotError] = useState("");
  const [isCopilotLoading, setIsCopilotLoading] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      state.handleFileChange(file);
      setCopilotAnswer(null);
      setCopilotError("");
      setCopilotQuestion("");
      await state.inspectFile(file);
    },
    [state]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: ACCEPTED_TYPES,
  });

  async function handleUseDemoFile() {
    setDemoLoading(true);
    try {
      const demoFile = await downloadDemoFile();
      state.handleFileChange(demoFile);
      setCopilotAnswer(null);
      setCopilotError("");
      setCopilotQuestion("");
      await state.inspectFile(demoFile);
      toast.success("Demo-файл загружен для предпросмотра.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Не удалось получить демо-файл.");
    } finally {
      setDemoLoading(false);
    }
  }

  function openTemplate() {
    window.open(`${API_URL}/files/template`, "_blank", "noopener,noreferrer");
  }

  const inspectResult = state.inspectResult;
  const previewColumns = inspectResult?.columns.slice(0, 8) ?? [];
  const sampleRows = inspectResult?.sample_rows.slice(0, 5) ?? [];
  const activeFilename = state.file?.name ?? "preview";
  const wizardColumns = state.mappingSuggestion?.columns ?? inspectResult?.columns ?? [];
  const canAnalyzeDirectly = Boolean(inspectResult?.is_ready_for_analysis && !state.normalizedFile);
  const canAnalyzeNormalized = Boolean(state.normalizedFile);
  const canAnalyze = canAnalyzeDirectly || canAnalyzeNormalized;
  const assistContext = inspectResult ? buildImportAssistContext({
    inspectResult,
    mappingDraft: state.mappingDraft,
    mappingSuggestionWarnings: state.mappingSuggestion?.warnings ?? [],
    mappingValidation: state.mappingValidation,
    normalizedFileName: state.normalizedFile?.name ?? null,
  }) : null;

  async function handleAskCopilot(question: string) {
    if (!assistContext) {
      setCopilotError("Сначала загрузите файл и дождитесь предпросмотра.");
      return;
    }

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setCopilotError("Введите вопрос для AI-помощника.");
      return;
    }

    setIsCopilotLoading(true);
    setCopilotError("");
    setCopilotQuestion(trimmedQuestion);

    try {
      const response = await requestImportAssist({
        question: trimmedQuestion,
        context: assistContext,
      });
      setCopilotAnswer(response);
    } catch (error) {
      setCopilotAnswer(null);
      setCopilotError(
        error instanceof Error
          ? error.message
          : "Локальный AI-помощник недоступен. Проверьте, что Ollama запущена и модель qwen2.5:7b установлена."
      );
    } finally {
      setIsCopilotLoading(false);
    }
  }

  return (
    <section className="rounded-[var(--radius-lg)] border border-[color:var(--border)] bg-[color:var(--surface)] p-5">
      <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold">Загрузка данных</h3>
              {state.file ? (
                <button
                  className="text-xs text-[color:var(--muted)] hover:text-[color:var(--text)]"
                  onClick={() => {
                    state.handleFileChange(null);
                    setCopilotAnswer(null);
                    setCopilotError("");
                    setCopilotQuestion("");
                  }}
                >
                  Удалить файл
                </button>
              ) : null}
        </div>
        <p className="text-sm text-[color:var(--muted)]">
          Загрузите CSV или Excel с ежедневными продажами и остатками. Минимум нужны дата, артикул,
          название товара, продажи, выручка и остаток.
        </p>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-3">
          <div {...getRootProps()}>
            <input {...getInputProps()} />
            <m.div
              animate={isDragActive ? { scale: 1.01 } : { scale: 1 }}
              className={cn(
                "cursor-pointer rounded-xl border border-dashed p-5 text-center transition",
                isDragActive
                  ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                  : "border-[color:var(--border)] bg-[color:var(--surface-muted)] hover:border-[color:var(--border-strong)]"
              )}
            >
              <UploadCloud className="mx-auto mb-2 h-5 w-5 text-[color:var(--muted)]" />
              <p className="text-sm">Перетащите файл или нажмите для выбора</p>
              <p className="mt-1 text-xs text-[color:var(--muted)]">Поддерживаются форматы CSV и XLSX</p>
            </m.div>
          </div>

          <div className="flex flex-wrap gap-2">
            <UiButton
              variant="secondary"
              className="h-9"
              leadingIcon={<Download className="h-4 w-4" />}
              onClick={openTemplate}
            >
              Скачать шаблон
            </UiButton>
            <UiButton
              variant="secondary"
              className="h-9"
              leadingIcon={<PlayCircle className="h-4 w-4" />}
              loading={demoLoading}
              onClick={() => void handleUseDemoFile()}
            >
              Попробовать демо-файл
            </UiButton>
            <UiButton
              variant="secondary"
              className="h-9"
              loading={state.isInspecting}
              leadingIcon={<CheckCircle2 className="h-4 w-4" />}
              onClick={() => void state.inspectFile()}
            >
              {state.isInspecting ? "Проверка структуры..." : "Проверить файл"}
            </UiButton>
            <UiButton
              className="h-9"
              loading={state.isLoading}
              disabled={!canAnalyze}
              leadingIcon={<UploadCloud className="h-4 w-4" />}
              onClick={() => void state.runAnalysis()}
            >
              {state.isLoading ? "Анализ..." : "Запустить анализ"}
            </UiButton>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-1">
          <div className="rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4">
            <p className="text-xs font-semibold uppercase text-[color:var(--muted)]">
              Поддерживаемые форматы
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {["CSV", "XLSX"].map((format) => (
                <span
                  key={format}
                  className="rounded-md border border-[color:var(--border)] bg-[color:var(--surface)] px-2.5 py-1 text-xs font-medium"
                >
                  {format}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4">
            <p className="text-xs font-semibold uppercase text-[color:var(--muted)]">
              Обязательные колонки
            </p>
            <div className="mt-3 grid gap-2">
              {REQUIRED_COLUMNS.map(([name, description]) => (
                <div key={name} className="flex items-start justify-between gap-3 text-sm">
                  <span className="font-medium">{name}</span>
                  <span className="text-right text-[color:var(--muted)]">{description}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4">
            <p className="text-xs font-semibold uppercase text-[color:var(--muted)]">
              Полезные дополнительные колонки
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {OPTIONAL_COLUMNS.map((name) => (
                <span
                  key={name}
                  className="rounded-md border border-[color:var(--border)] bg-[color:var(--surface)] px-2.5 py-1 text-xs font-medium"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {state.file ? (
          <m.div
            key={state.file.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-5 space-y-4 rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 text-sm">
                <FileSpreadsheet className="h-4 w-4 text-[color:var(--muted)]" />
                <span className="font-medium">{state.file.name}</span>
              </div>
              {inspectResult?.is_ready_for_analysis ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-[color:var(--success-soft)] px-2 py-1 text-xs font-medium text-[color:var(--success)]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Файл готов к анализу
                </span>
              ) : state.inspectError ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-[color:var(--danger-soft)] px-2 py-1 text-xs font-medium text-[color:var(--danger)]">
                  <XCircle className="h-3.5 w-3.5" />
                  Не удалось прочитать файл
                </span>
              ) : inspectResult ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-[color:var(--warning-soft)] px-2 py-1 text-xs font-medium text-[color:var(--warning)]">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Нужны исправления перед анализом
                </span>
              ) : null}
            </div>

            {state.inspectError ? (
              <div className="rounded-lg border border-[color:var(--danger)] bg-[color:var(--danger-soft)] p-3 text-sm text-[color:var(--danger)]">
                {state.inspectError}
              </div>
            ) : null}

            {state.error ? (
              <div className="rounded-lg border border-[color:var(--danger)] bg-[color:var(--danger-soft)] p-3 text-sm text-[color:var(--danger)]">
                {state.error}
              </div>
            ) : null}

            {state.mappingError ? (
              <div className="rounded-lg border border-[color:var(--danger)] bg-[color:var(--danger-soft)] p-3 text-sm text-[color:var(--danger)]">
                {state.mappingError}
              </div>
            ) : null}

            {inspectResult ? (
              <div className="space-y-4">
                <p className="text-sm text-[color:var(--muted)]">
                  {canAnalyzeDirectly
                    ? "Файл уже соответствует структуре StockPilot. Можно сразу запускать анализ."
                    : inspectResult.human_readable_summary}
                </p>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <MetaCard label="Строк" value={String(inspectResult.row_count)} />
                  <MetaCard label="Колонок" value={String(inspectResult.column_count)} />
                  <MetaCard
                    label="Период"
                    value={
                      inspectResult.date_range?.min && inspectResult.date_range?.max
                        ? `${inspectResult.date_range.min} - ${inspectResult.date_range.max}`
                        : "Не определён"
                    }
                  />
                  <MetaCard
                    label="SKU"
                    value={inspectResult.sku_count != null ? String(inspectResult.sku_count) : "Не определено"}
                  />
                </div>

                <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
                  <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                    <p className="text-sm font-semibold">Найденные колонки</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {inspectResult.columns.map((column) => (
                        <span
                          key={column}
                          className="rounded-md border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-2.5 py-1 text-xs font-medium"
                        >
                          {column}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                    <p className="text-sm font-semibold">Статус обязательных полей</p>
                    <div className="mt-3 grid gap-2">
                      {Object.entries(inspectResult.required_columns_status).map(([column, status]) => (
                        <div key={column} className="flex items-center justify-between gap-3 text-sm">
                          <span className="font-medium">{column}</span>
                          <span
                            className={cn(
                              "rounded-md px-2 py-1 text-xs font-medium",
                              status.present
                                ? "bg-[color:var(--success-soft)] text-[color:var(--success)]"
                                : "bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
                            )}
                          >
                            {status.present ? "Найдена" : "Не найдена"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                  <p className="text-sm font-semibold">Полезные дополнительные поля</p>
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    {Object.entries(inspectResult.optional_columns_status).map(([column, status]) => (
                      <div key={column} className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium">{column}</span>
                        <span className="text-xs text-[color:var(--muted)]">
                          {status.present ? "Есть в файле" : "Необязательно"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {sampleRows.length > 0 ? (
                  <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                    <p className="text-sm font-semibold">Предпросмотр строк</p>
                    <div className="mt-3 overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-[color:var(--border)] text-left text-[color:var(--muted)]">
                            {previewColumns.map((column) => (
                              <th key={column} className="px-3 py-2 font-medium">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {sampleRows.map((row, index) => (
                            <tr key={`${activeFilename}-${index}`} className="border-b border-[color:var(--border)]">
                              {previewColumns.map((column) => (
                                <td key={`${column}-${index}`} className="px-3 py-2 text-[color:var(--muted)]">
                                  {formatPreviewValue(row[column])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : null}

                {inspectResult.warnings.length > 0 ? (
                  <div className="space-y-3">
                    <p className="text-sm font-semibold">Что нужно исправить перед анализом</p>
                    {inspectResult.warnings.map((warning) => (
                      <div
                        key={`${warning.code}-${warning.field ?? "general"}`}
                        className="rounded-lg border border-[color:var(--warning)] bg-[color:var(--warning-soft)] p-4"
                      >
                        <p className="text-sm font-semibold text-[color:var(--warning)]">{warning.title}</p>
                        <p className="mt-1 text-sm text-[color:var(--warning)]">{warning.message}</p>
                        {warning.suggestion ? (
                          <p className="mt-2 text-sm text-[color:var(--warning)]">{warning.suggestion}</p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}

                {!inspectResult.is_ready_for_analysis ? (
                  <MappingWizard
                    columns={wizardColumns}
                    mappingDraft={state.mappingDraft}
                    mappingSuggestionWarnings={state.mappingSuggestion?.warnings ?? []}
                    mappingValidation={state.mappingValidation}
                    isSuggestingMapping={state.isSuggestingMapping}
                    isValidatingMapping={state.isValidatingMapping}
                    isNormalizingFile={state.isNormalizingFile}
                    normalizedFileName={state.normalizedFile?.name ?? null}
                    onUpdateField={state.updateMappingField}
                    onValidate={() => void state.validateSuggestedMapping()}
                    onNormalize={() => void state.normalizeMappedFile()}
                    onAnalyze={() => void state.runAnalysis()}
                    analyzeDisabled={!state.normalizedFile}
                    analyzeLoading={state.isLoading}
                  />
                ) : null}

                {assistContext ? (
                  <ImportAssistCard
                    question={copilotQuestion}
                    answer={copilotAnswer}
                    error={copilotError}
                    loading={isCopilotLoading}
                    onQuestionChange={setCopilotQuestion}
                    onAsk={(question) => void handleAskCopilot(question)}
                  />
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-[color:var(--muted)]">
                После выбора файла StockPilot покажет структуру, пример строк и статус обязательных колонок до запуска анализа.
              </p>
            )}
          </m.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

function ImportAssistCard({
  question,
  answer,
  error,
  loading,
  onQuestionChange,
  onAsk,
}: {
  question: string;
  answer: ImportAssistResponse | null;
  error: string;
  loading: boolean;
  onQuestionChange: (value: string) => void;
  onAsk: (question: string) => void;
}) {
  return (
    <div className="space-y-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-[color:var(--muted)]" />
          <p className="text-sm font-semibold">AI-помощник по файлу</p>
        </div>
        <p className="text-sm text-[color:var(--muted)]">Ответ формируется локально через Ollama.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {IMPORT_ASSIST_QUICK_QUESTIONS.map((quickQuestion) => (
          <button
            key={quickQuestion}
            className="rounded-md border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-3 py-1.5 text-xs font-medium text-[color:var(--text)] transition hover:border-[color:var(--border-strong)]"
            onClick={() => onAsk(quickQuestion)}
            type="button"
          >
            {quickQuestion}
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          className="h-10 flex-1 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] px-3 text-sm outline-none transition focus:border-[color:var(--accent)]"
          placeholder="Например: что не так с моим файлом?"
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
        />
        <UiButton
          className="h-10"
          loading={loading}
          leadingIcon={<Send className="h-4 w-4" />}
          onClick={() => onAsk(question)}
        >
          {loading ? "Думаем..." : "Спросить"}
        </UiButton>
      </div>

      {error ? (
        <div className="rounded-lg border border-[color:var(--danger)] bg-[color:var(--danger-soft)] p-3 text-sm text-[color:var(--danger)]">{error}</div>
      ) : null}

      {answer ? (
        <div
          className={cn(
            "rounded-lg border p-4 text-sm",
            answer.fallback
              ? "border-[color:var(--warning)] bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
              : "border-[color:var(--border)] bg-[color:var(--surface-muted)] text-[color:var(--text)]"
          )}
        >
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-[color:var(--muted)]">
            <span>{answer.provider}</span>
            <span>•</span>
            <span>{answer.model}</span>
            {answer.fallback ? (
              <>
                <span>•</span>
                <span>Локальный AI-помощник недоступен</span>
              </>
            ) : null}
          </div>
          <p className="whitespace-pre-wrap leading-6">{answer.answer}</p>
        </div>
      ) : null}
    </div>
  );
}

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-3">
      <p className="text-xs font-medium uppercase text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}

function MappingWizard({
  columns,
  mappingDraft,
  mappingSuggestionWarnings,
  mappingValidation,
  isSuggestingMapping,
  isValidatingMapping,
  isNormalizingFile,
  normalizedFileName,
  onUpdateField,
  onValidate,
  onNormalize,
  onAnalyze,
  analyzeDisabled,
  analyzeLoading,
}: {
  columns: string[];
  mappingDraft: Record<string, { source_column: string | null; confidence: number; status: string }>;
  mappingSuggestionWarnings: Array<{
    code: string;
    field?: string | null;
    title: string;
    message: string;
    suggestion?: string | null;
  }>;
  mappingValidation: {
    is_valid: boolean;
    errors: Array<{
      code: string;
      field?: string | null;
      title: string;
      message: string;
      suggestion?: string | null;
    }>;
    warnings: Array<{
      code: string;
      field?: string | null;
      title: string;
      message: string;
      suggestion?: string | null;
    }>;
    human_readable_summary: string;
  } | null;
  isSuggestingMapping: boolean;
  isValidatingMapping: boolean;
  isNormalizingFile: boolean;
  normalizedFileName: string | null;
  onUpdateField: (field: string, sourceColumn: string | null) => void;
  onValidate: () => void;
  onNormalize: () => void;
  onAnalyze: () => void;
  analyzeDisabled: boolean;
  analyzeLoading: boolean;
}) {
  if (isSuggestingMapping) {
    return (
      <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4 text-sm text-[color:var(--muted)]">
        StockPilot подбирает похожие колонки в вашем файле...
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold">Проверьте сопоставление колонок</p>
        <p className="text-sm text-[color:var(--muted)]">
          StockPilot нашёл похожие колонки в вашем файле. Проверьте, что всё сопоставлено правильно,
          прежде чем запускать анализ.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-[color:var(--border)] text-left text-[color:var(--muted)]">
              <th className="px-3 py-2 font-medium">Поле StockPilot</th>
              <th className="px-3 py-2 font-medium">Что означает</th>
              <th className="px-3 py-2 font-medium">Колонка в вашем файле</th>
              <th className="px-3 py-2 font-medium">Уверенность</th>
              <th className="px-3 py-2 font-medium">Статус</th>
            </tr>
          </thead>
          <tbody>
            {STOCKPILOT_FIELDS.map(([field, description]) => {
              const mapping = mappingDraft[field];
              const confidence = mapping?.confidence ?? 0;
              const confidenceText = mapping?.source_column
                ? confidence > 0
                  ? `${Math.round(confidence * 100)}%`
                  : "Ручной выбор"
                : "—";
              const statusText = !mapping?.source_column
                ? "Не найдено"
                : confidence >= 0.85
                  ? "Найдено"
                  : "Нужна проверка";
              const statusClass = !mapping?.source_column
                ? "bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
                : confidence >= 0.85
                  ? "bg-[color:var(--success-soft)] text-[color:var(--success)]"
                  : "bg-[color:var(--warning-soft)] text-[color:var(--warning)]";

              return (
                <tr key={field} className="border-b border-[color:var(--border)]">
                  <td className="px-3 py-2 font-medium">{field}</td>
                  <td className="px-3 py-2 text-[color:var(--muted)]">{description}</td>
                  <td className="px-3 py-2">
                    <select
                      className="w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2 text-sm"
                      value={mapping?.source_column ?? ""}
                      onChange={(event) => onUpdateField(field, event.target.value || null)}
                    >
                      <option value="">Не выбрано</option>
                      {columns.map((column) => (
                        <option key={`${field}-${column}`} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-[color:var(--muted)]">{confidenceText}</td>
                  <td className="px-3 py-2">
                    <span className={cn("rounded-md px-2 py-1 text-xs font-medium", statusClass)}>
                      {statusText}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {mappingSuggestionWarnings.length > 0 ? (
        <div className="space-y-3">
          {mappingSuggestionWarnings.map((warning) => (
            <MessageCard key={`${warning.code}-${warning.field ?? "general"}`} tone="warning" {...warning} />
          ))}
        </div>
      ) : null}

      {mappingValidation ? (
        <div className="space-y-3">
          <div
            className={cn(
              "rounded-lg border p-4 text-sm",
              mappingValidation.is_valid
                ? "border-[color:var(--success)] bg-[color:var(--success-soft)] text-[color:var(--success)]"
                : "border-[color:var(--danger)] bg-[color:var(--danger-soft)] text-[color:var(--danger)]"
            )}
          >
            {mappingValidation.human_readable_summary}
          </div>

          {mappingValidation.errors.map((error) => (
            <MessageCard key={`${error.code}-${error.field ?? "general"}`} tone="error" {...error} />
          ))}
          {mappingValidation.warnings.map((warning) => (
            <MessageCard key={`${warning.code}-${warning.field ?? "general"}`} tone="warning" {...warning} />
          ))}
        </div>
      ) : null}

      {normalizedFileName ? (
        <div className="rounded-lg border border-[color:var(--success)] bg-[color:var(--success-soft)] p-4 text-sm text-[color:var(--success)]">
          Файл готов к анализу: {normalizedFileName}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <UiButton variant="secondary" className="h-9" loading={isValidatingMapping} onClick={onValidate}>
          {isValidatingMapping ? "Проверяем сопоставление..." : "Подтвердить сопоставление"}
        </UiButton>
        <UiButton
          variant="secondary"
          className="h-9"
          loading={isNormalizingFile}
          disabled={!mappingValidation?.is_valid}
          onClick={onNormalize}
        >
          {isNormalizingFile ? "Нормализация..." : "Нормализовать файл"}
        </UiButton>
        <UiButton className="h-9" disabled={analyzeDisabled} loading={analyzeLoading} onClick={onAnalyze}>
          {analyzeLoading ? "Анализ..." : "Запустить анализ"}
        </UiButton>
      </div>

      <div className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4 text-sm text-[color:var(--muted)]">
        Если нужная колонка не найдена автоматически, выберите её вручную. Локальный помощник по файлу может объяснить ошибки проверки и подсказать, что исправить.
      </div>
    </div>
  );
}

function MessageCard({
  tone,
  title,
  message,
  suggestion,
}: {
  tone: "warning" | "error";
  title: string;
  message: string;
  suggestion?: string | null;
}) {
  const styles =
    tone === "warning"
      ? "border-[color:var(--warning)] bg-[color:var(--warning-soft)] text-[color:var(--warning)]"
      : "border-[color:var(--danger)] bg-[color:var(--danger-soft)] text-[color:var(--danger)]";

  return (
    <div className={cn("rounded-lg border p-4", styles)}>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 text-sm opacity-90">{message}</p>
      {suggestion ? <p className="mt-2 text-sm opacity-80">{suggestion}</p> : null}
    </div>
  );
}

function formatPreviewValue(value: string | number | boolean | null | undefined) {
  if (value == null) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

function buildImportAssistContext(params: {
  inspectResult: ImportInspectResponse;
  mappingDraft: Record<string, MappingSuggestionItem>;
  mappingSuggestionWarnings: MappingWarningResponse[];
  mappingValidation: {
    errors: MappingWarningResponse[];
    warnings: MappingWarningResponse[];
  } | null;
  normalizedFileName: string | null;
}): ImportAssistContext {
  const stage = params.mappingValidation
    ? "upload_validation"
    : params.inspectResult.is_ready_for_analysis
      ? "upload_preview"
      : "upload_mapping";

  return {
    stage,
    filename: params.normalizedFileName ?? params.inspectResult.filename,
    columns: params.inspectResult.columns,
    required_columns_status: params.inspectResult.required_columns_status,
    optional_columns_status: params.inspectResult.optional_columns_status,
    suggested_mapping: params.mappingDraft,
    validation_errors: params.mappingValidation?.errors ?? [],
    validation_warnings: params.mappingValidation?.warnings ?? [],
    warnings: [
      ...params.inspectResult.warnings,
      ...params.mappingSuggestionWarnings,
    ],
    is_ready_for_analysis: params.inspectResult.is_ready_for_analysis || Boolean(params.normalizedFileName),
    sample_rows: params.inspectResult.sample_rows.slice(0, 3),
  };
}
