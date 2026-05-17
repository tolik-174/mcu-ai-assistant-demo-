# import json
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import os
# import re

# DATA_PATH = "../data/parsed"
# FAISS_PATH = "./data/faiss/local_multi.faiss"
# META_PATH = "./data/faiss/local_multi_meta.json"

# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# def clean_chunk(text: str) -> str:
#     text = text.replace('\r', '').strip()
#     # 🔹 Крок 1: об’єднання всіх рядків таблиць між [TABLE] ... (до пустого рядка)
#     lines = text.split('\n')
#     merged = []
#     buffer = []
#     inside_table = False

#     for line in lines:
#         stripped = line.strip()

#         if stripped.startswith('[TABLE]'):
#             # Початок таблиці
#             inside_table = True
#             buffer = [stripped]
#             continue

#         if inside_table:
#             # Кінець таблиці — якщо натрапили на порожній рядок або новий [SOURCE]
#             if stripped == "" or stripped.startswith("[SOURCE]"):
#                 inside_table = False
#                 merged.append(' '.join(buffer))
#                 if stripped:  # не губимо [SOURCE]
#                     merged.append(stripped)
#             else:
#                 # Додаємо все в один рядок таблиці
#                 buffer.append(stripped)
#         else:
#             merged.append(stripped)

#     # якщо таблиця закінчилась текстом — додаємо залишок
#     if buffer:
#         merged.append(' '.join(buffer))

#     text = '\n'.join(merged)

#     # 🔹 Крок 2: базове очищення
#     text = re.sub(r'\s{2,}', ' ', text)          # подвійні пробіли
#     text = re.sub(r'\n{3,}', '\n\n', text)       # зайві нові рядки
#     text = text.replace('│', '|').replace('‖', '|')  # дивні символи таблиць

#     return text
# def collect_chunks():
#     all_chunks = []
#     for file in os.listdir(DATA_PATH):
#         if not file.endswith(".json"):
#             continue

#         path = os.path.join(DATA_PATH, file)
#         with open(path, "r", encoding="utf-8") as f:
#             try:
#                 docs = json.load(f)
#             except json.JSONDecodeError as e:
#                 print(f"[WARN] ⚠️ JSON decode error in {file}: {e}")
#                 continue

#         # 🔍 Вирівнюємо структуру файлів
#         if isinstance(docs, str):
#             docs = [{"text": docs}]
#         elif isinstance(docs, dict):
#             docs = [docs]
#         elif isinstance(docs, list):
#             if all(isinstance(x, str) for x in docs):
#                 docs = [{"text": x} for x in docs]
#             elif not all(isinstance(x, dict) for x in docs):
#                 print(f"[WARN] Unexpected format in {file}, normalizing...")
#                 docs = [{"text": str(x)} for x in docs]

#         for d in docs:
#             text = d.get("text", "")
#             if not text or len(text.strip()) < 10:
#                 continue
#             chunk = {
#                 "source": file.replace(".json", ""),
#                 "text": clean_chunk(text)
#             }
#             all_chunks.append(chunk)

#     print(f"[BUILD] Loaded {len(all_chunks)} text chunks.")
#     return all_chunks

# if __name__ == "__main__":
#     print("[BUILD] Collecting chunks...")
#     chunks = collect_chunks()
#     print(f"[BUILD] Loaded {len(chunks)} chunks.")

#     print("[BUILD] Encoding embeddings...")
#     texts = [c["text"] for c in chunks]
#     emb = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

#     print("[BUILD] Creating FAISS index...")
#     index = faiss.IndexFlatIP(emb.shape[1])
#     index.add(np.array(emb, dtype="float32"))

#     os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
#     faiss.write_index(index, FAISS_PATH)
#     json.dump(chunks, open(META_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

#     print(f"[DONE] Indexed {len(chunks)} chunks into {FAISS_PATH}")
import os
import json
import numpy as np
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pathlib import Path
# # Шляхи
# DATA_PATH = "../data/parsed"
# FAISS_PATH = "../data/faiss/local_multi.faiss"
# META_PATH = "../data/faiss/local_multi_meta.json"

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATA_PATH = str(Path(DATA_DIR) / "parsed")

FAISS_DIR = str(Path(DATA_DIR) / "faiss")
FAISS_PATH = str(Path(FAISS_DIR) / "local_multi.faiss")
META_PATH = str(Path(FAISS_DIR) / "local_multi_meta.json")
# Модель для векторизації
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Максимальна довжина текстового чанку (символи)
MAX_CHARS = 1000


def clean_chunk(text: str) -> str:
    """Нормалізує текст перед індексацією"""
    text = text.replace("\u00A0", " ")  # non-breaking spaces
    text = text.replace("\n\n", "\n")
    text = text.strip()
    return text


def collect_chunks():
    """Збирає таблиці та текстові блоки із data/parsed"""
    all_chunks = []

    for file in os.listdir(DATA_PATH):
        if not file.endswith(".json"):
            continue

        path = os.path.join(DATA_PATH, file)
        with open(path, "r", encoding="utf-8") as f:
            try:
                docs = json.load(f)
            except Exception as e:
                print(f"⚠️ Помилка при читанні {file}: {e}")
                continue

        for d in docs:
            # Іноді в JSON трапляється рядок, а не словник
            if isinstance(d, str):
                continue

            text = d.get("text", "")
            if len(text.strip()) < 10:
                continue

            cleaned = clean_chunk(text)

            # 🧩 Якщо це таблиця — зберігаємо її як один блок (не ріжемо!)
            if "[TABLE]" in cleaned or "|" in cleaned:
                all_chunks.append({
                    "source": file.replace(".json", ""),
                    "type": "table",
                    "text": cleaned
                })
                continue

            # 🧩 Якщо це звичайний текст — ділимо на чанки
            for i in range(0, len(cleaned), MAX_CHARS):
                part = cleaned[i:i + MAX_CHARS].strip()
                if len(part) > 10:
                    all_chunks.append({
                        "source": file.replace(".json", ""),
                        "type": "text",
                        "text": part
                    })

    print(f"[BUILD] Loaded {len(all_chunks)} chunks.")
    return all_chunks


def build_index():
    print("[BUILD] Collecting chunks...")
    chunks = collect_chunks()

    print(f"[BUILD] Encoding {len(chunks)} embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    print("[BUILD] Creating FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
    faiss.write_index(index, FAISS_PATH)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Indexed {len(chunks)} chunks → {FAISS_PATH}")


if __name__ == "__main__":
    build_index()
