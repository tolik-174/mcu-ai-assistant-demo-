import fitz  # PyMuPDF
import json
from pathlib import Path

def parse_pdf(pdf_path: str, output_path: str):
    doc = fitz.open(pdf_path)
    data = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        data.append({
            "page": i + 1,
            "text": text.strip()
        })
        if i % 20 == 0:
            print(f"[INFO] Parsed {i}/{len(doc)} pages...")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Parsed {len(data)} pages → {output_path}")
    return data


if __name__ == "__main__":
    parse_pdf(
        "../data/pdf/stm32f103c8.pdf",
        "../data/parsed/stm32f103c8.json"
    )
