import pdfplumber
import json
import re
import os
from tqdm import tqdm


# --- Функція для очищення тексту клітинок ---
def clean_cell(text):
    if not text:
        return ""
    text = re.sub(r"\s*\n\s*", " ", text.strip())
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


# --- Перевірка, чи таблиця належить до STK (пін, конектор і т.д.) ---
def is_stk_table(table_text):
    keywords = [
        "pin", "signal", "function", "connector", "header",
        "port", "gpio", "voltage", "power", "supply"
    ]
    text_low = table_text.lower()
    return any(k in text_low for k in keywords)


# --- Основна функція парсингу STK документації ---
def parse_stk_docs(pdf_path, output_path):
    pdf_name = os.path.basename(pdf_path)
    print(f"[INFO] Витягуємо STK таблиці з {pdf_name}...")

    tables_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(tqdm(pdf.pages, desc=f"📄 {pdf_name}")):
            try:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # нормалізуємо таблицю
                    normalized = [
                        [clean_cell(c) for c in row if c and c.strip()] for row in table
                    ]
                    normalized = [r for r in normalized if any(c.strip() for c in r)]

                    # пропускаємо нерелевантні таблиці
                    joined_text = " ".join(sum(normalized, []))
                    if not is_stk_table(joined_text):
                        continue

                    # створюємо Markdown таблицю
                    header = " | ".join(normalized[0])
                    divider = " | ".join(["---"] * len(normalized[0]))
                    body = "\n".join([" | ".join(r) for r in normalized[1:]])
                    markdown = f"[TABLE] [SOURCE: {pdf_name}]\n| {header} |\n| {divider} |\n{body}"

                    tables_data.append({
                        "source": pdf_name,
                        "page": page_num + 1,
                        "type": "stk_table",
                        "text": markdown
                    })
            except Exception as e:
                print(f"error on page{page_num+1}: {e}")

    # Збереження
    if tables_data:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tables_data, f, ensure_ascii=False, indent=2)
        print(f"[DONE] Збережено {len(tables_data)} STK таблиць → {output_path}")
    else:
        print(f"[WARN] Не знайдено жодної STK таблиці у {pdf_name}")


if __name__ == "__main__":
    input_dir = PDF_DIR
    output_dir = PARSED_DIR

    for file in os.listdir(input_dir):
        for file in os.listdir(input_dir):
            if file.endswith(".pdf"):
                pdf_path = os.path.join(input_dir, file)
                out_path = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_stk.json")
                parse_stk_docs(pdf_path, out_path)

