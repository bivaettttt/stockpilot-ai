from pathlib import Path

TEMPLATE_DIR = Path("data/templates")
TEMPLATE_FILE = TEMPLATE_DIR / "stockpilot_template.csv"


TEMPLATE_CONTENT = """date,sku,product_name,category,quantity_sold,revenue,stock_on_hand,purchase_price,selling_price,supplier,promotion_flag
2026-01-01,COF-001,Кофе арабика 250г,Кофе,5,2100,120,250,420,Поставщик А,false
2026-01-01,TEA-001,Чай зелёный 100г,Чай,3,990,80,160,330,Поставщик Б,false
2026-01-01,SYR-001,Сироп ванильный 1л,Сиропы,2,1380,25,360,690,Поставщик В,true
"""


def ensure_template_file() -> Path:
    """
    Создаёт CSV-шаблон входного файла, если его ещё нет.
    """
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

    if not TEMPLATE_FILE.exists():
        TEMPLATE_FILE.write_text(TEMPLATE_CONTENT, encoding="utf-8")

    return TEMPLATE_FILE
