import os
import glob
from pdf_parser import parse_pdf
from table_parser import parse_tables
import os
from pathlib import Path

DATA_DIR = os.getenv("DATA_DIR", "/app/data")

PDF_DIR = Path(DATA_DIR) / "pdf"
PARSED_DIR = Path(DATA_DIR) / "parsed"

def main():
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    if not pdf_files:
        print("[ERROR] У папці data/pdf/ немає PDF.")
        return

    print(f"[START] Знайдено {len(pdf_files)} PDF файлів.\n")

    for path in pdf_files:
        base = os.path.basename(path).replace(".pdf", "")
        text_out = os.path.join(PARSED_DIR, f"{base}.json")
        table_out = os.path.join(PARSED_DIR, f"{base}_tables.json")

        print(f"Парсимо {base}...")
        try:
            parse_pdf(path, text_out)
            parse_tables(path, table_out)
            print(f"Завершено: {base}\n")
        except Exception as e:
            print(f"Помилка при {base}: {e}\n")

    print("[DONE] Усі PDF оброблені.")

if __name__ == "__main__":
    main()
