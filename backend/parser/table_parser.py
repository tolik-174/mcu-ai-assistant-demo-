import pdfplumber
import json
import re
import os
from tqdm import tqdm

def clean_cell(text):
    """Очищає вміст однієї клітинки таблиці"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def normalize_table_structure(table):
    """Вирівнює таблицю після парсингу PDF"""
    max_cols = max(len(row) for row in table)
    normalized = []
    for row in table:
        merged = [clean_cell(c) for c in row]
        while len(merged) < max_cols:
            merged.append("")
        normalized.append(merged)
    return [r for r in normalized if any(c.strip() for c in r)]

def fix_table_rows(markdown: str) -> str:
    """
    Склеює рядки, які pdfplumber розірвав усередині однієї таблиці.
    Також виправляє рядки з меншою кількістю колонок.
    """
    lines = [l for l in markdown.split("\n") if l.strip()]
    fixed = []

    for line in lines:
        if not line.strip():
            continue

        # Порахувати кількість колонок
        cols = [c.strip() for c in line.split("|") if c.strip()]
        col_count = len(cols)

        # Якщо рядок починається з порожніх колонок або має <3 значення → це продовження
        if re.match(r"^\|\s*\|", line) or col_count < 3:
            if fixed:
                fixed[-1] = fixed[-1].rstrip() + " " + " ".join(cols)
            else:
                fixed.append(line)
        else:
            fixed.append(line)

    return "\n".join(fixed)

def validate_table(table):
    """Відсікає некорисні таблиці"""
    flat = " ".join(sum(table, []))
    if not any(k in flat.lower() for k in ["pin", "register", "bit", "usart", "adc", "control", "gpio", "cr1", "parameter", "symbol"]):
        return False
    if len(table) < 2 or len(table[0]) < 2:
        return False
    return True

def extract_fallback_tables(page_text, pdf_name):
    """Fallback для таблиць, які pdfplumber не побачив"""
    tables = []
    table_blocks = re.findall(r'(\|.*?\|(?:\n\|.*?\|)+)', page_text, re.DOTALL)
    for tb in table_blocks:
        tables.append({
            "source": pdf_name,
            "page": None,
            "type": "table",
            "text": f"[TABLE] [SOURCE: {pdf_name}]\n{tb.strip()}"
        })
    return tables

def extract_tables(pdf_path, output_path):
    pdf_name = os.path.basename(pdf_path)
    tables_data = []
    print(f"[INFO] Витягуємо таблиці з {pdf_name}...")

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(tqdm(pdf.pages, desc=f"📄 {pdf_name}")):
            try:
                tables = page.extract_tables()
                page_text = page.extract_text() or ""

                # 🧩 Fallback пошук (на випадок, якщо не знайдено таблиць)
                if not tables:
                    fallback_tables = extract_fallback_tables(page_text, pdf_name)
                    tables_data.extend(fallback_tables)
                    continue

                for table in tables:
                    if not table:
                        continue
                    normalized = normalize_table_structure(table)
                    if not validate_table(normalized):
                        continue

                    max_cols = max(len(row) for row in normalized)
                    header = " | ".join(normalized[0])
                    divider = " | ".join(["---"] * max_cols)
                    body = "\n".join([" | ".join(r) for r in normalized[1:]])

                    markdown = f"| {header} |\n| {divider} |\n{body}"
                    markdown = fix_table_rows(markdown)

                    tables_data.append({
                        "source": pdf_name,
                        "page": page_num + 1,
                        "type": "table",
                        "text": f"[TABLE] [SOURCE: {pdf_name}]\n{markdown}"
                    })

            except Exception as e:
                print(f"Помилка на сторінці {page_num+1}: {e}")

    if tables_data:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)
        print(f"[DONE] Збережено {len(tables_data)} таблиць → {output_path}")
    else:
        print(f"[WARN] Таблиці не знайдено у {pdf_name}")

if __name__ == "__main__":
    input_dir = PDF_DIR
    output_dir = PARSED_DIR

    for file in os.listdir(input_dir):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, file)
            out_path = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_tables.json")
            extract_tables(pdf_path, out_path)
