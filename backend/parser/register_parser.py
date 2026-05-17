import re
import pdfplumber
import json
import os
from tqdm import tqdm

def parse_registers(pdf_path, output_path):
    pdf_name = os.path.basename(pdf_path)
    print(f"[INFO] Parsing full register descriptions from {pdf_name}...")

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages, desc=f"📄 {pdf_name}"):
            t = page.extract_text()
            if t:
                full_text += t + "\n---PAGE---\n"

    # 🧠 Пошук тільки справжніх регістрів
    # приклад: "APB1 peripheral reset register (RCC_APB1RSTR)"
    pattern = re.compile(r'([A-Za-z0-9\s\-_/]+register)\s*\(([A-Z]{2,6}_[A-Z0-9]{2,8})\)', re.M)
    matches = list(pattern.finditer(full_text))

    registers = []
    print(f"[INFO] Found {len(matches)} register headers")

    for i, match in enumerate(matches):
        title = match.group(1).strip()
        name = match.group(2).strip()

        # фільтр — пропускаємо загальні заголовки типу "RCC registers"
        if title.lower().strip() in ["rcc registers", "adc registers", "gpio registers"]:
            continue

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section = full_text[start:end].strip()

        addr = re.search(r'Address offset\s*[:=]\s*([0-9A-Fx]+)', section, re.I)
        reset = re.search(r'Reset value\s*[:=]\s*([0-9A-Fx ]+)', section, re.I)
        access = re.search(r'Access\s*[:=]\s*([^\n]+)', section, re.I)

        # 🔹 Витягуємо усі біти (навіть якщо вони з нового рядка)
        bits = re.findall(r'(Bit\s+[0-9:]+\s+[A-Z0-9_]+\s*:[^\n]+(?:\n(?!Bit).+?)*)', section, re.S)

        # 🔹 Витягуємо таблиці (якщо є)
        table = []
        for line in re.findall(r'\|.*?\|', section):
            cols = [c.strip() for c in line.split("|") if c.strip()]
            if len(cols) >= 2:
                table.append(cols)

        registers.append({
            "name": name,
            "title": title,
            "address_offset": addr.group(1) if addr else None,
            "reset_value": reset.group(1) if reset else None,
            "access": access.group(1).strip() if access else None,
            "bits": bits,
            "tables": table,
            "description": section,
            "source": pdf_name
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registers, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Extracted {len(registers)} registers → {output_path}")


if __name__ == "__main__":
    input_dir = PDF_DIR
    output_dir = PARSED_DIR

    os.makedirs(output_dir, exist_ok=True)

    for file in os.listdir(input_dir):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, file)
            out_path = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_registers.json")
            parse_registers(pdf_path, out_path)
