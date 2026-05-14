from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUTPUT_FILE = Path("data/input/demo_sales_90_days.csv")
RANDOM_SEED = 42


@dataclass(frozen=True)
class Product:
    sku: str
    product_name: str
    category: str
    purchase_price: float
    selling_price: float
    base_daily_demand: float
    start_stock: int


PRODUCTS = [
    Product("COF-001", "Кофе арабика 250г", "Кофе", 250, 420, 5.8, 190),
    Product("COF-002", "Кофе робуста 250г", "Кофе", 190, 340, 3.2, 130),
    Product("COF-003", "Кофе молотый 500г", "Кофе", 380, 690, 2.4, 100),
    Product("TEA-001", "Чай зелёный 100г", "Чай", 160, 330, 2.0, 120),
    Product("TEA-002", "Чай чёрный 100г", "Чай", 150, 310, 2.5, 130),
    Product("TEA-003", "Чай травяной 80г", "Чай", 140, 300, 1.4, 90),
    Product("SYR-001", "Сироп ванильный 1л", "Сиропы", 360, 690, 1.5, 35),
    Product("SYR-002", "Сироп карамельный 1л", "Сиропы", 370, 710, 1.3, 34),
    Product("SYR-003", "Сироп ореховый 1л", "Сиропы", 390, 750, 0.8, 26),
    Product("MIL-001", "Молоко овсяное 1л", "Молоко", 120, 240, 4.4, 140),
    Product("MIL-002", "Молоко миндальное 1л", "Молоко", 160, 310, 2.1, 85),
    Product("MIL-003", "Молоко кокосовое 1л", "Молоко", 170, 330, 1.5, 70),
    Product("SNK-001", "Печенье овсяное", "Снеки", 45, 110, 4.8, 160),
    Product("SNK-002", "Батончик злаковый", "Снеки", 35, 95, 6.2, 230),
    Product("SNK-003", "Круассан миндальный", "Снеки", 70, 170, 3.7, 120),
    Product("ACC-001", "Стакан бумажный 250мл", "Расходники", 3, 8, 20.0, 800),
    Product("ACC-002", "Крышка для стакана", "Расходники", 2, 6, 18.0, 750),
    Product("ACC-003", "Трубочки бумажные", "Расходники", 1, 4, 8.0, 500),
    Product("DES-001", "Десерт чизкейк", "Десерты", 95, 230, 2.8, 90),
    Product("DES-002", "Десерт брауни", "Десерты", 80, 210, 3.1, 105),
]


def main() -> None:
    random.seed(RANDOM_SEED)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    rows = generate_sales_rows(
        start_date=date(2026, 1, 1),
        days=90,
        products=PRODUCTS,
    )

    df = pd.DataFrame(rows)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Демо-датасет создан:")
    print(OUTPUT_FILE)
    print(f"Строк: {len(df)}")
    print(f"Товаров: {df['sku'].nunique()}")
    print(f"Период: {df['date'].min()} — {df['date'].max()}")


def generate_sales_rows(
    start_date: date,
    days: int,
    products: list[Product],
) -> list[dict]:
    rows: list[dict] = []

    stock_by_sku = {product.sku: product.start_stock for product in products}

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        for product in products:
            demand = calculate_daily_demand(
                product=product,
                current_date=current_date,
                day_offset=day_offset,
            )

            current_stock = stock_by_sku[product.sku]
            quantity_sold = min(demand, current_stock)

            stock_by_sku[product.sku] = max(0, current_stock - quantity_sold)

            if should_restock(
                product=product,
                current_stock=stock_by_sku[product.sku],
                day_offset=day_offset,
            ):
                stock_by_sku[product.sku] += calculate_restock_quantity(product)

            revenue = quantity_sold * product.selling_price

            rows.append(
                {
                    "date": current_date.isoformat(),
                    "sku": product.sku,
                    "product_name": product.product_name,
                    "category": product.category,
                    "quantity_sold": quantity_sold,
                    "revenue": round(revenue, 2),
                    "stock_on_hand": stock_by_sku[product.sku],
                    "purchase_price": product.purchase_price,
                    "selling_price": product.selling_price,
                }
            )

    return rows


def calculate_daily_demand(
    product: Product,
    current_date: date,
    day_offset: int,
) -> int:
    weekday = current_date.weekday()

    weekend_factor = 1.25 if weekday in {5, 6} else 1.0

    monthly_growth_factor = 1 + day_offset / 90 * 0.12

    category_factor = get_category_factor(
        category=product.category,
        current_date=current_date,
    )

    random_factor = random.uniform(0.55, 1.45)

    raw_demand = (
        product.base_daily_demand
        * weekend_factor
        * monthly_growth_factor
        * category_factor
        * random_factor
    )

    return max(0, int(round(raw_demand)))


def get_category_factor(
    category: str,
    current_date: date,
) -> float:
    month = current_date.month

    if category in {"Кофе", "Молоко"}:
        return 1.12 if month in {1, 2} else 1.0

    if category in {"Десерты", "Снеки"}:
        return 1.18 if current_date.weekday() in {4, 5, 6} else 1.0

    if category == "Сиропы":
        return 1.08 if month in {2, 3} else 1.0

    return 1.0


def should_restock(
    product: Product,
    current_stock: int,
    day_offset: int,
) -> bool:
    if day_offset < 10:
        return False

    threshold = product.base_daily_demand * 10

    random_restock_block = random.random() < 0.18

    return current_stock < threshold and not random_restock_block


def calculate_restock_quantity(product: Product) -> int:
    base_quantity = product.base_daily_demand * random.randint(22, 38)
    noise = random.uniform(0.85, 1.2)

    return int(round(base_quantity * noise))


if __name__ == "__main__":
    main()
