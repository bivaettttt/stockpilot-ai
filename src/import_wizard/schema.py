from __future__ import annotations

from dataclasses import dataclass

from src.domain.constants import OPTIONAL_COLUMNS, REQUIRED_COLUMNS

CANONICAL_COLUMN_ORDER = [*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]

CANONICAL_FIELD_DESCRIPTIONS = {
    "date": "Дата продажи или остатка",
    "sku": "Артикул товара",
    "product_name": "Название товара",
    "quantity_sold": "Количество проданных единиц",
    "revenue": "Выручка по строке",
    "stock_on_hand": "Остаток на складе",
    "category": "Категория товара",
    "purchase_price": "Закупочная цена",
    "selling_price": "Цена продажи",
    "supplier": "Поставщик",
    "promotion_flag": "Признак акции или промо",
}

CANONICAL_FIELD_LABELS = {
    "date": "Дата",
    "sku": "Артикул",
    "product_name": "Название товара",
    "quantity_sold": "Продажи",
    "revenue": "Выручка",
    "stock_on_hand": "Остаток",
    "category": "Категория",
    "purchase_price": "Закупочная цена",
    "selling_price": "Цена продажи",
    "supplier": "Поставщик",
    "promotion_flag": "Промо",
}

COLUMN_SYNONYMS = {
    "date": [
        "date",
        "дата",
        "дата продажи",
        "день",
        "sale_date",
        "sales_date",
        "order_date",
        "transaction_date",
    ],
    "sku": [
        "sku",
        "артикул",
        "код товара",
        "товарный код",
        "product_code",
        "item_code",
        "item_id",
        "номенклатура",
    ],
    "product_name": [
        "product_name",
        "product",
        "name",
        "товар",
        "название",
        "название товара",
        "наименование",
        "наименование товара",
    ],
    "quantity_sold": [
        "quantity_sold",
        "qty",
        "quantity",
        "sold",
        "units_sold",
        "продано",
        "продажи шт",
        "количество",
        "кол во",
        "кол-во",
        "количество продано",
        "реализовано",
    ],
    "revenue": [
        "revenue",
        "sales",
        "amount",
        "total",
        "выручка",
        "сумма",
        "оборот",
        "продажи руб",
        "сумма продаж",
    ],
    "stock_on_hand": [
        "stock_on_hand",
        "stock",
        "inventory",
        "on_hand",
        "остаток",
        "остатки",
        "остаток на складе",
        "склад",
        "наличие",
    ],
    "category": [
        "category",
        "категория",
        "группа",
        "группа товара",
    ],
    "purchase_price": [
        "purchase_price",
        "cost",
        "себестоимость",
        "закупочная цена",
        "цена закупки",
        "закупка",
    ],
    "selling_price": [
        "selling_price",
        "price",
        "retail_price",
        "цена",
        "цена продажи",
        "розничная цена",
    ],
    "supplier": [
        "supplier",
        "поставщик",
        "vendor",
    ],
    "promotion_flag": [
        "promotion_flag",
        "promo",
        "promotion",
        "акция",
        "промо",
        "скидка",
    ],
}


@dataclass(frozen=True)
class MappingCandidate:
    canonical_field: str
    source_column: str | None
    confidence: float
    status: str

