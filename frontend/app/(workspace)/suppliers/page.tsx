"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Pencil, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageTitle, Surface, UiButton } from "@/src/components/app/ui";
import { useDashboardState } from "@/src/components/app/dashboard-state-provider";
import {
  createSupplierRequest,
  deleteSkuSettingRequest,
  deleteSupplierRequest,
  getSkuSettingsRequest,
  getSuppliersRequest,
  putSkuSettingRequest,
  updateSupplierRequest,
} from "@/src/lib/api/suppliers";
import { formatCompactMoney, formatDateTime, formatNumber } from "@/src/lib/format";
import type { SkuSettingPayload, SupplierPayload } from "@/src/types/api";

const EMPTY_SUPPLIER_FORM: SupplierPayload = {
  name: "",
  contact_name: "",
  email: "",
  phone: "",
  default_lead_time_days: 0,
  min_order_value: null,
  notes: "",
};

const EMPTY_SKU_FORM: SkuSettingPayload & { sku: string } = {
  sku: "",
  product_name: "",
  supplier_id: null,
  purchase_price: null,
  selling_price: null,
  lead_time_days: null,
  moq: null,
  pack_size: null,
  safety_stock_override: null,
  notes: "",
};

export default function SuppliersPage() {
  const dashboard = useDashboardState();
  const queryClient = useQueryClient();
  const [supplierForm, setSupplierForm] = useState(EMPTY_SUPPLIER_FORM);
  const [editingSupplierId, setEditingSupplierId] = useState<string | null>(null);
  const [skuForm, setSkuForm] = useState(EMPTY_SKU_FORM);
  const [showSupplierForm, setShowSupplierForm] = useState(false);
  const [showSkuForm, setShowSkuForm] = useState(false);

  const suppliersQuery = useQuery({
    queryKey: ["suppliers"],
    queryFn: getSuppliersRequest,
  });
  const skuSettingsQuery = useQuery({
    queryKey: ["sku-settings"],
    queryFn: getSkuSettingsRequest,
  });

  const supplierMutation = useMutation({
    mutationFn: (payload: SupplierPayload) =>
      editingSupplierId
        ? updateSupplierRequest(editingSupplierId, payload)
        : createSupplierRequest(payload),
    onSuccess: () => {
      toast.success(editingSupplierId ? "Поставщик обновлён." : "Поставщик добавлен.");
      setSupplierForm(EMPTY_SUPPLIER_FORM);
      setEditingSupplierId(null);
      setShowSupplierForm(false);
      void queryClient.invalidateQueries({ queryKey: ["suppliers"] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Не удалось сохранить поставщика.");
    },
  });

  const deleteSupplierMutation = useMutation({
    mutationFn: (supplierId: string) => deleteSupplierRequest(supplierId),
    onSuccess: () => {
      toast.success("Поставщик удалён.");
      void queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      void queryClient.invalidateQueries({ queryKey: ["sku-settings"] });
    },
  });

  const skuMutation = useMutation({
    mutationFn: (params: { sku: string; payload: SkuSettingPayload }) =>
      putSkuSettingRequest(params.sku, params.payload),
    onSuccess: () => {
      toast.success("Настройки товара сохранены.");
      setSkuForm(EMPTY_SKU_FORM);
      setShowSkuForm(false);
      void queryClient.invalidateQueries({ queryKey: ["sku-settings"] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Не удалось сохранить настройки товара.");
    },
  });

  const deleteSkuMutation = useMutation({
    mutationFn: (sku: string) => deleteSkuSettingRequest(sku),
    onSuccess: () => {
      toast.success("Настройки товара удалены.");
      void queryClient.invalidateQueries({ queryKey: ["sku-settings"] });
    },
  });

  const suppliers = useMemo(() => suppliersQuery.data?.suppliers ?? [], [suppliersQuery.data?.suppliers]);
  const skuSettings = useMemo(() => skuSettingsQuery.data?.items ?? [], [skuSettingsQuery.data?.items]);
  const hasSupplierSetup = suppliers.length > 0 || skuSettings.length > 0;

  const productRows = useMemo(() => {
    const bySku = new Map<string, {
      sku: string;
      product_name: string;
      category: string;
      file_supplier: string | null;
      file_purchase_price: number | null;
      file_selling_price: number | null;
    }>();

    for (const item of dashboard.result?.recommendations ?? []) {
      bySku.set(item.sku, {
        sku: item.sku,
        product_name: item.product_name,
        category: item.category,
        file_supplier: item.supplier ?? null,
        file_purchase_price: item.purchase_price ?? null,
        file_selling_price: item.selling_price ?? null,
      });
    }

    for (const setting of skuSettings) {
      if (!bySku.has(setting.sku)) {
        bySku.set(setting.sku, {
          sku: setting.sku,
          product_name: setting.product_name ?? "Нет данных",
          category: "Нет данных",
          file_supplier: null,
          file_purchase_price: null,
          file_selling_price: null,
        });
      }
    }

    return Array.from(bySku.values()).map((base) => {
      const setting = skuSettings.find((item) => item.sku === base.sku);
      return {
        ...base,
        setting,
      };
    });
  }, [dashboard.result?.recommendations, skuSettings]);

  return (
    <div className="space-y-7">
      <PageTitle
        title="Поставщики"
        description="Локальный справочник поставщиков и компактные настройки SKU для закупочного плана."
      />

      <section className="grid gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        {!hasSupplierSetup ? (
        <Surface className="p-6">
          <div className="space-y-5">
            <div className="inline-flex rounded-3xl bg-[color:var(--accent-soft)] p-3 text-[color:var(--accent)]">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold">Настройте первого поставщика</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[color:var(--muted)]">
                После добавления поставщика можно привязать SKU, задать срок поставки, MOQ и кратность упаковки.
                Эти ограничения появятся в закупочном плане отдельным слоем поверх системной рекомендации.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <SupplierHint title="Срок поставки" body="Помогает оценить, хватит ли остатка до следующей поставки." />
              <SupplierHint title="Минимальный заказ" body="Поднимает количество до допустимого минимума поставщика." />
              <SupplierHint title="Кратность упаковки" body="Округляет закупку до упаковки без изменения исходного прогноза." />
            </div>
            <UiButton
              leadingIcon={<Plus className="h-4 w-4" />}
              onClick={() => {
                setEditingSupplierId(null);
                setSupplierForm(EMPTY_SUPPLIER_FORM);
                setShowSupplierForm(true);
              }}
            >
              Добавить поставщика
            </UiButton>
          </div>
        </Surface>
        ) : (
        <>
        <Surface className="p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Справочник поставщиков</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Срок поставки, минимальная сумма заказа и контактные данные.
              </p>
            </div>
            <UiButton
              variant="secondary"
              leadingIcon={<Plus className="h-4 w-4" />}
              onClick={() => {
                setEditingSupplierId(null);
                setSupplierForm(EMPTY_SUPPLIER_FORM);
                setShowSupplierForm(true);
              }}
            >
              Добавить поставщика
            </UiButton>
          </div>

          {showSupplierForm || editingSupplierId ? (
          <div className="mt-5 space-y-3 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
            <SupplierForm form={supplierForm} onChange={setSupplierForm} />
            <div className="flex gap-2">
              <UiButton
                onClick={() => supplierMutation.mutate(supplierForm)}
                loading={supplierMutation.isPending}
                leadingIcon={<Save className="h-4 w-4" />}
              >
                {editingSupplierId ? "Сохранить изменения" : "Добавить поставщика"}
              </UiButton>
              {editingSupplierId ? (
                <UiButton
                  variant="secondary"
                  onClick={() => {
                    setEditingSupplierId(null);
                    setSupplierForm(EMPTY_SUPPLIER_FORM);
                    setShowSupplierForm(false);
                  }}
                >
                  Отменить
                </UiButton>
              ) : null}
              {!editingSupplierId ? (
                <UiButton
                  variant="secondary"
                  onClick={() => {
                    setSupplierForm(EMPTY_SUPPLIER_FORM);
                    setShowSupplierForm(false);
                  }}
                >
                  Закрыть
                </UiButton>
              ) : null}
            </div>
          </div>
          ) : null}

          {suppliers.length === 0 && !suppliersQuery.isLoading ? (
            <div className="mt-6 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-muted)] p-4">
              <p className="text-sm font-medium">Поставщики пока не добавлены</p>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Добавьте поставщиков, чтобы StockPilot мог группировать закупки и учитывать сроки поставки.
              </p>
            </div>
          ) : (
            <div className="mt-6 space-y-3">
              {suppliers.map((supplier) => (
                <div key={supplier.id} className="rounded-lg border border-[color:var(--border)] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-[color:var(--muted)]" />
                        <p className="font-medium">{supplier.name}</p>
                      </div>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        Срок поставки: {formatNumber(supplier.default_lead_time_days, 0)} дн.
                        {supplier.min_order_value != null
                          ? ` • Минимальная сумма: ${formatCompactMoney(supplier.min_order_value)}`
                          : ""}
                      </p>
                      <p className="mt-1 text-xs text-[color:var(--muted)]">
                        Обновлено {formatDateTime(supplier.updated_at)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="rounded-md border border-[color:var(--border)] p-2"
                        onClick={() => {
                          setEditingSupplierId(supplier.id);
                          setShowSupplierForm(true);
                          setSupplierForm({
                            name: supplier.name,
                            contact_name: supplier.contact_name ?? "",
                            email: supplier.email ?? "",
                            phone: supplier.phone ?? "",
                            default_lead_time_days: supplier.default_lead_time_days,
                            min_order_value: supplier.min_order_value ?? null,
                            notes: supplier.notes ?? "",
                          });
                        }}
                        aria-label={`Редактировать ${supplier.name}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        className="rounded-md border border-[color:var(--danger)] p-2 text-[color:var(--danger)]"
                        onClick={() => deleteSupplierMutation.mutate(supplier.id)}
                        aria-label={`Удалить ${supplier.name}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Surface>

        <Surface className="p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Настройки товара</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Поставщик, закупочная цена, MOQ, кратность упаковки и локальные настройки по SKU.
              </p>
            </div>
            <UiButton
              variant="secondary"
              leadingIcon={<Plus className="h-4 w-4" />}
              onClick={() => {
                setSkuForm(EMPTY_SKU_FORM);
                setShowSkuForm(true);
              }}
            >
              Добавить SKU
            </UiButton>
          </div>

          {showSkuForm || Boolean(skuForm.sku) ? (
          <div className="mt-5 rounded-2xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block text-[color:var(--muted)]">SKU</span>
                <input
                  value={skuForm.sku}
                  onChange={(event) => setSkuForm((current) => ({ ...current, sku: event.target.value }))}
                  className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3"
                />
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-[color:var(--muted)]">Название товара</span>
                <input
                  value={skuForm.product_name ?? ""}
                  onChange={(event) => setSkuForm((current) => ({ ...current, product_name: event.target.value }))}
                  className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3"
                />
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-[color:var(--muted)]">Поставщик</span>
                <select
                  value={skuForm.supplier_id ?? ""}
                  onChange={(event) =>
                    setSkuForm((current) => ({
                      ...current,
                      supplier_id: event.target.value || null,
                    }))
                  }
                  className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3"
                >
                  <option value="">Поставщик не указан</option>
                  {suppliers.map((supplier) => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </label>
              <NumberField label="Закупочная цена" value={skuForm.purchase_price} onChange={(value) => setSkuForm((current) => ({ ...current, purchase_price: value }))} />
              <NumberField label="Цена продажи" value={skuForm.selling_price} onChange={(value) => setSkuForm((current) => ({ ...current, selling_price: value }))} />
              <NumberField label="Срок поставки" value={skuForm.lead_time_days} onChange={(value) => setSkuForm((current) => ({ ...current, lead_time_days: value }))} integer />
              <NumberField label="Минимальный заказ" value={skuForm.moq} onChange={(value) => setSkuForm((current) => ({ ...current, moq: value }))} integer />
              <NumberField label="Кратность упаковки" value={skuForm.pack_size} onChange={(value) => setSkuForm((current) => ({ ...current, pack_size: value }))} integer />
              <NumberField label="Переопределение страхового запаса" value={skuForm.safety_stock_override} onChange={(value) => setSkuForm((current) => ({ ...current, safety_stock_override: value }))} />
              <label className="text-sm md:col-span-2">
                <span className="mb-1 block text-[color:var(--muted)]">Заметка</span>
                <textarea
                  value={skuForm.notes ?? ""}
                  onChange={(event) => setSkuForm((current) => ({ ...current, notes: event.target.value }))}
                  className="min-h-[84px] w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2"
                />
              </label>
            </div>
            <div className="mt-3 flex gap-2">
              <UiButton
                onClick={() => {
                  if (!skuForm.sku.trim()) {
                    toast.error("Укажите SKU товара.");
                    return;
                  }
                  const { sku, ...payload } = skuForm;
                  skuMutation.mutate({ sku, payload });
                }}
                loading={skuMutation.isPending}
                leadingIcon={<Save className="h-4 w-4" />}
              >
                Сохранить настройки товара
              </UiButton>
              <UiButton variant="secondary" onClick={() => {
                setSkuForm(EMPTY_SKU_FORM);
                setShowSkuForm(false);
              }}>
                Закрыть
              </UiButton>
            </div>
          </div>
          ) : null}

          <div className="mt-5 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-[color:var(--surface-muted)] text-left text-[color:var(--muted)]">
                <tr>
                  <th className="px-3 py-2">SKU</th>
                  <th className="px-3 py-2">Товар</th>
                  <th className="px-3 py-2">Поставщик</th>
                  <th className="px-3 py-2">Закупочная цена</th>
                  <th className="px-3 py-2">Срок поставки</th>
                  <th className="px-3 py-2">MOQ</th>
                  <th className="px-3 py-2">Кратность</th>
                  <th className="px-3 py-2">Действия</th>
                </tr>
              </thead>
              <tbody>
                {productRows.map((row) => (
                  <tr key={row.sku} className="border-t border-[color:var(--border)] align-top">
                    <td className="px-3 py-3 font-medium">{row.sku}</td>
                    <td className="px-3 py-3">
                      <div>{row.setting?.product_name ?? row.product_name}</div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">{row.category}</div>
                    </td>
                    <td className="px-3 py-3">
                      <div>{row.setting?.supplier_name ?? row.file_supplier ?? "Поставщик не указан"}</div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">
                        {row.setting?.supplier_name ? "из справочника" : row.file_supplier ? "из файла" : "не указано"}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <div>
                        {row.setting?.purchase_price != null
                          ? formatCompactMoney(row.setting.purchase_price)
                          : row.file_purchase_price != null
                            ? formatCompactMoney(row.file_purchase_price)
                            : "Нет данных"}
                      </div>
                      <div className="mt-1 text-xs text-[color:var(--muted)]">
                        {row.setting?.purchase_price != null ? "из справочника" : row.file_purchase_price != null ? "из файла" : "не указано"}
                      </div>
                    </td>
                    <td className="px-3 py-3">{row.setting?.lead_time_days != null ? `${formatNumber(row.setting.lead_time_days, 0)} дн.` : row.setting?.supplier_default_lead_time_days != null ? `${formatNumber(row.setting.supplier_default_lead_time_days, 0)} дн.` : "Нет данных"}</td>
                    <td className="px-3 py-3">{row.setting?.moq != null ? formatNumber(row.setting.moq, 0) : "Нет данных"}</td>
                    <td className="px-3 py-3">{row.setting?.pack_size != null ? formatNumber(row.setting.pack_size, 0) : "Нет данных"}</td>
                    <td className="px-3 py-3">
                      <div className="flex gap-2">
                        <button
                          className="rounded-md border border-[color:var(--border)] p-2"
                          onClick={() => {
                            setSkuForm({
                              sku: row.sku,
                              product_name: row.setting?.product_name ?? row.product_name,
                              supplier_id: row.setting?.supplier_id ?? null,
                              purchase_price: row.setting?.purchase_price ?? row.file_purchase_price ?? null,
                              selling_price: row.setting?.selling_price ?? row.file_selling_price ?? null,
                              lead_time_days: row.setting?.lead_time_days ?? null,
                              moq: row.setting?.moq ?? null,
                              pack_size: row.setting?.pack_size ?? null,
                              safety_stock_override: row.setting?.safety_stock_override ?? null,
                              notes: row.setting?.notes ?? "",
                            });
                            setShowSkuForm(true);
                          }}
                          aria-label={`Редактировать настройки ${row.sku}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        {row.setting ? (
                          <button
                            className="rounded-md border border-[color:var(--danger)] p-2 text-[color:var(--danger)]"
                            onClick={() => deleteSkuMutation.mutate(row.sku)}
                            aria-label={`Удалить настройки ${row.sku}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
        </>
        )}
      </section>
    </div>
  );
}

function SupplierHint({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-3xl border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-2 text-sm leading-5 text-[color:var(--muted)]">{body}</p>
    </div>
  );
}

function SupplierForm({
  form,
  onChange,
}: {
  form: SupplierPayload;
  onChange: (next: SupplierPayload) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <label className="text-sm">
        <span className="mb-1 block text-[color:var(--muted)]">Название</span>
        <input value={form.name} onChange={(event) => onChange({ ...form, name: event.target.value })} className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-[color:var(--muted)]">Контактное лицо</span>
        <input value={form.contact_name ?? ""} onChange={(event) => onChange({ ...form, contact_name: event.target.value })} className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-[color:var(--muted)]">Email</span>
        <input value={form.email ?? ""} onChange={(event) => onChange({ ...form, email: event.target.value })} className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-[color:var(--muted)]">Телефон</span>
        <input value={form.phone ?? ""} onChange={(event) => onChange({ ...form, phone: event.target.value })} className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3" />
      </label>
      <NumberField label="Срок поставки по умолчанию" value={form.default_lead_time_days} onChange={(value) => onChange({ ...form, default_lead_time_days: Math.max(0, Math.round(value ?? 0)) })} integer />
      <NumberField label="Минимальная сумма заказа" value={form.min_order_value} onChange={(value) => onChange({ ...form, min_order_value: value })} />
      <label className="text-sm md:col-span-2">
        <span className="mb-1 block text-[color:var(--muted)]">Заметки</span>
        <textarea value={form.notes ?? ""} onChange={(event) => onChange({ ...form, notes: event.target.value })} className="min-h-[84px] w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2" />
      </label>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  integer = false,
}: {
  label: string;
  value: number | null | undefined;
  onChange: (value: number | null) => void;
  integer?: boolean;
}) {
  return (
    <label className="text-sm">
      <span className="mb-1 block text-[color:var(--muted)]">{label}</span>
      <input
        type="number"
        step={integer ? 1 : 0.01}
        min={0}
        value={value ?? ""}
        onChange={(event) => {
          const next = event.target.value.trim();
          onChange(next === "" ? null : Number(next));
        }}
        className="h-10 w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--surface)] px-3"
      />
    </label>
  );
}
