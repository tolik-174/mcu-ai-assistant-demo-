# ##true code backend/app.py
# from fastapi import FastAPI
# from pydantic import BaseModel
# import faiss
# import json
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import requests
# import os
# import re
# import asyncio
# import requests
# from code_search import router as code_router
# from code_search import auto_rebuild_on_start
# from code_search import search_files_by_name, open_file_by_path
# from code_search import local_search_files, local_open_file


# app = FastAPI()
# app.include_router(code_router)
# auto_rebuild_on_start()

# FAISS_PATH = "../data/faiss/local_multi.faiss"
# META_PATH = "../data/faiss/local_multi_meta.json"
# REGISTER_DIR = "../data/parsed"
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "mistral"

# print("[INIT] Loading embedding model...")
# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# print("[READY] Embedding model loaded successfully.")

# print("[INIT] Loading FAISS index and metadata...")
# index = faiss.read_index(FAISS_PATH)
# meta = json.load(open(META_PATH, "r", encoding="utf-8"))
# print(f"[READY] Loaded {len(meta)} chunks into memory.")


# class QueryRequest(BaseModel):
#     query: str
#     lang: str = "en"


# @app.post("/search")
# async def search(req: QueryRequest):
#     query = req.query.strip()
#     query_lower = query.lower()

#     # -----------------------------
#     # КЛЮЧОВІ СЛОВА
#     # -----------------------------
#     table_keywords = ["table", "characteristics", "consumption", "tim", "timer", "adc", "usart", "i2c", "spi", "gpio"]
#     register_keywords = ["register", "cr", "sr", "ccmr", "ccer", "psc", "arr", "ccr", "bit", "mask", "offset"]
#     stk_keywords = ["stk", "nucleo", "board", "pin", "header", "connector", "jumper", "cn", "hardware"]

#     # -----------------------------
#     # FILE SEARCH тригер
#     # -----------------------------
#     #file_extensions = [".c", ".h", ".cpp", ".hpp", ".s", ".asm", ".py", ".xml", ".json", ".txt"]
#  # === FILE SEARCH DETECT ===
#     file_exts = [".c", ".h", ".cpp", ".hpp", ".s", ".py", ".xml", ".txt", ".asm"]

#     is_file_query = (
#         query_lower.startswith("search file") or
#         query_lower.startswith("open ") or
#         any(query_lower.endswith(ext) for ext in file_exts)
#     )

#     if is_file_query:
#         # ------------------------------
#         # ВИТЯГУЄМО ІМ'Я ФАЙЛУ
#         m = re.findall(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", query_lower)
#         filename = m[0] if m else query_lower.replace("search file", "").replace("open", "").strip()

#         # ------------------------------
      
#         results = local_search_files(filename)

#         if not results:
#             return {
#                 "status": "not_found",
#                 "type": "file",
#                 "answer": f"File '{filename}' not found."
#             }

#         exact = [r for r in results if r["file"].lower() == filename.lower()]
#         same_base = [r for r in results if r["file"].split(".")[0].lower() == filename.split(".")[0].lower()]

#         # exact match → open file immediately
#         if len(exact) == 1:
#             file = exact[0]
#             data = local_open_file(file["path"])

#             return {
#                 "status": "ok",
#                 "type": "file",
#                 "opened": file["path"],
#                 "project": file["project"],
#                 "content": data.get("content", ""),
#                 "info": data
#             }

#         # more than one exact match (rare)
#         if len(exact) > 1:
#             rows = "\n".join(
#                 f"| `{r['file']}` | `{r['path']}` |"
#                 for r in exact
#             )
#             return {
#                 "status": "multiple_exact",
#                 "answer": (
#                     f"⚠️ Multiple exact matches for **`{filename}`**:\n\n"
#                     f"| File | Path |\n|------|-------|\n{rows}\n\n"
#                     "Specify exact path: `open <filename>`"
#                 ),
#                 "choices": exact
#             }

#         # fallback: same basename (c + cpp)
#         if same_base:
#             rows = "\n".join(
#                 f"| `{r['file']}` | `{r['path']}` |"
#                 for r in same_base
#             )
#             return {
#                 "status": "multiple_related",
#                 "answer": (
#                     f"🔎 Found related files for **`{filename}`**:\n\n"
#                     f"| File | Path |\n|------|-------|\n{rows}\n\n"
#                     "Specify which one to open: `open adc_ep.c`"
#                 ),
#                 "choices": same_base
#             }

#         # any match → ask user
#         rows = "\n".join(
#             f"| `{r['file']}` | `{r['path']}` |"
#             for r in results
#         )
#         return {
#             "status": "multiple",
#             "answer": (
#                 f"🔎 Multiple matching files:\n\n"
#                 f"| File | Path |\n|------|-------|\n{rows}\n\n"
#                 "Specify exact file name."
#             ),
#             "choices": results
#         }

#     #############################################

#     # -----------------------------
#     # Генеруємо embedding для FAISS
#     # -----------------------------
#     query_emb = await asyncio.to_thread(model.encode, [query], convert_to_numpy=True, normalize_embeddings=True)
#     D, I = index.search(query_emb.astype("float32"), 8)
#     chunks = [meta[i] for i in I[0] if i < len(meta)]

#     is_table_query = any(k in query_lower for k in table_keywords)
#     is_register_query = any(k in query_lower for k in register_keywords)
#     is_stk_query = any(k in query_lower for k in stk_keywords)

#     # -----------------------------
#     # 1️⃣ STK / Nucleo
#     # -----------------------------
#     if is_stk_query:
#         stk_chunks = [c for c in chunks if any(k in c["text"].lower() for k in stk_keywords)]
#         context = "\n\n".join([c["text"] for c in stk_chunks]) or "\n\n".join(c["text"] for c in chunks)

#         prompt = (
#             "You are a hardware assistant. Show the STM32 STK/Nucleo pinout or connector table. "
#             "Return exact Markdown tables from documentation.\n\n"
#             f"{context}\n\nQuestion: {query}"
#         )

#     # -----------------------------
#     # 2️⃣ Таблиці
#     # -----------------------------
#     elif is_table_query:
#         table_chunks = [c for c in chunks if "|" in c["text"] or "---" in c["text"]]

#         if table_chunks:
#             output = []
#             for c in table_chunks:
#                 for line in c["text"].split("\n"):
#                     line = line.strip()
#                     if "|" in line:
#                         cols = [p.strip() or "—" for p in line.split("|")]
#                         output.append("| " + " | ".join(cols) + " |")
#                     elif re.match(r"table\s*\d+", line, re.I):
#                         output.append(f"**{line}**")
#             return {
#                 "status": "ok",
#                 "type": "table",
#                 "answer": "\n".join(output),
#                 "chunks_used": len(table_chunks)
#             }

#         context = "\n\n".join(c["text"] for c in chunks)
#         prompt = (
#             "Show the STM32 documentation table exactly as it appears. Markdown format only.\n\n"
#             f"{context}\n\nQuestion: {query}"
#         )

#     # -----------------------------
#     # 3️⃣ Реєстри (локальна обробка)
#     # -----------------------------
#     elif is_register_query:

#         reg_match = None
#         for token in query.split():
#             if "_" in token and token.isupper():
#                 reg_match = token
#                 break

#         if reg_match:
#             reg_name = reg_match.upper()
#             found = []

#             for file in os.listdir(REGISTER_DIR):
#                 if file.endswith("_registers.json"):
#                     try:
#                         data = json.load(open(os.path.join(REGISTER_DIR, file), encoding="utf-8"))
#                         for reg in data:
#                             if reg_name in reg.get("name", "").upper():
#                                 reg["source"] = file
#                                 found.append(reg)
#                     except:
#                         continue

#             if found:
#                 bits_clean = {}
#                 for r in found:
#                     for b in r.get("bits", []):
#                         m = re.match(r"Bit\s+([\d:]+)\s+([A-Z0-9_]+)\s*:?\s*(.*)", b, re.I)
#                         if m:
#                             num, name, desc = m.groups()
#                             bits_clean[name] = {"bit": num, "desc": desc}

#                 md = f"## {reg_name}\n"
#                 md += "**Register description**\n\n"
#                 md += "### Bits\n| Bit | Name | Description |\n|-----|------|-------------|\n"
#                 for name, info in bits_clean.items():
#                     md += f"| {info['bit']} | {name} | {info['desc']} |\n"

#                 return {"status": "ok", "answer": md}

#         context = "\n".join(c["text"] for c in chunks)
#         prompt = (
#             "Explain this STM32 register including all bits.\n\n"
#             f"{context}\n\nQuestion: {query}"
#         )

#     # -----------------------------
#     # 4️⃣ FAISS fallback (AI генерує текст)
#     # -----------------------------
#     else:
#         context = "\n\n".join([c["text"] for c in chunks])
#         prompt = (
#             f"Answer in {req.lang} based on STM32 documentation.\n\n"
#             f"{context}\n\nQuestion: {query}"
#         )

#     # -----------------------------
#     # SEND TO OLLAMA
#     # -----------------------------
#     resp = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": prompt}, stream=False)
#     answer = ""
#     for line in resp.text.split("\n"):
#         try:
#             js = json.loads(line)
#             answer += js.get("response", "")
#         except:
#             continue

#     return {
#         "status": "ok",
#         "answer": answer.strip(),
#         "chunks_used": len(chunks)
#     }


# from fastapi import FastAPI
# from pydantic import BaseModel
# import faiss
# import json
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import requests
# import os
# import re
# import asyncio
# from pathlib import Path

# from code_search import router as code_router
# from code_search import auto_rebuild_on_start
# from code_search import local_search_files, local_open_file

# app = FastAPI()
# app.include_router(code_router)
# auto_rebuild_on_start()

# FAISS_PATH = "../data/faiss/local_multi.faiss"
# META_PATH = "../data/faiss/local_multi_meta.json"
# REGISTER_DIR = "../data/parsed"
# PROJECTS_ROOT = Path("../data/projects/zips").resolve()

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "mistral"

# print("[INIT] Loading embedding model...")
# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# print("[READY] Embedding model loaded successfully.")

# print("[INIT] Loading FAISS index and metadata...")
# index = faiss.read_index(FAISS_PATH)
# meta = json.load(open(META_PATH, "r", encoding="utf-8"))
# print(f"[READY] Loaded {len(meta)} chunks into memory.")


# class QueryRequest(BaseModel):
#     query: str
#     lang: str = "en"


# @app.post("/search")
# async def search(req: QueryRequest):
#     query = req.query.strip()
#     query_lower = query.lower()

#     # =============================
#     # FILE SEARCH DETECT
#     # =============================
#     file_exts = [".c", ".h", ".cpp", ".hpp", ".s", ".asm", ".py", ".xml", ".txt"]

#     is_file_query = (
#         query_lower.startswith("open ") or
#         query_lower.startswith("search file") or
#         any(query_lower.endswith(ext) for ext in file_exts)
#     )

#     if is_file_query:
#         # ---- extract filename
#         m = re.findall(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", query_lower)
#         filename = m[0] if m else query_lower.replace("open", "").replace("search file", "").strip()

#         results = local_search_files(filename)

#         if not results:
#             return {
#                 "status": "not_found",
#                 "answer": f"File '{filename}' not found."
#             }

#         # ---- build choices WITH id + absolute_path
#         choices = []
#         for i, r in enumerate(results):
#             abs_path = str((PROJECTS_ROOT / r["path"]).resolve())
#             choices.append({
#                 "id": i,
#                 "project": r["project"],
#                 "file": r["file"],
#                 "relative_path": r["relative_path"],
#                 "absolute_path": abs_path
#             })

#         # ---- single match → open immediately
#         if len(choices) == 1:
#             file = choices[0]
#             data = local_open_file(f"{file['project']}/{file['relative_path']}")

#             return {
#                 "status": "ok",
#                 "opened": file["absolute_path"],
#                 "file": file["file"],
#                 "content": data.get("content", "")
#             }

#         # ---- multiple matches
#         msg = "Multiple files found:\n\n"
#         for c in choices:
#             msg += f"[{c['id']}] {c['project']}/{c['relative_path']}\n"
#         msg += "\nUse: open <id>"

#         return {
#             "status": "multiple",
#             "answer": msg,
#             "choices": choices
#         }

#     # =============================
#     # FAISS SEARCH (без змін)
#     # =============================
#     query_emb = await asyncio.to_thread(
#         model.encode,
#         [query],
#         convert_to_numpy=True,
#         normalize_embeddings=True
#     )
#     D, I = index.search(query_emb.astype("float32"), 8)
#     chunks = [meta[i] for i in I[0] if i < len(meta)]

#     context = "\n\n".join(c["text"] for c in chunks)
#     prompt = (
#         f"Answer in {req.lang} based on STM32 documentation.\n\n"
#         f"{context}\n\nQuestion: {query}"
#     )

#     resp = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": prompt}, stream=False)
#     answer = ""
#     for line in resp.text.split("\n"):
#         try:
#             js = json.loads(line)
#             answer += js.get("response", "")
#         except:
#             continue

#     return {
#         "status": "ok",
#         "answer": answer.strip()
#     }

from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from sentence_transformers import SentenceTransformer
from svd_api import router as svd_router
from pydantic import BaseModel
from pathlib import Path
from code_search import router as code_router
from code_search import auto_rebuild_on_start
from code_search import local_search_files
from datetime import datetime
from code_search import unzip_projects, build_global_index

import faiss
import json
import requests
import os
import re
import asyncio
import shutil


app = FastAPI()
app.include_router(code_router)
app.include_router(svd_router)
auto_rebuild_on_start()

# FAISS_PATH = "../data/faiss/local_multi.faiss"
# META_PATH = "../data/faiss/local_multi_meta.json"
# REGISTER_DIR = "../data/parsed"
#  OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"
INDEXING_STATUS = {
    "running": False,
    "message": "Idle",
    "last_error": None
}
# PDF_DIR = "../data/pdf"
# ZIP_DIR = "../data/projects/zips"
# PARSED_DIR = "../data/parsed"
# FAISS_DIR = "../data/faiss"
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

FAISS_PATH = os.path.join(DATA_DIR, "faiss", "local_multi.faiss")
META_PATH = os.path.join(DATA_DIR, "faiss", "local_multi_meta.json")
REGISTER_DIR = os.path.join(DATA_DIR, "parsed")
PDF_DIR = os.path.join(DATA_DIR, "pdf")
ZIP_DIR = os.path.join(DATA_DIR, "projects", "zips")
PARSED_DIR = os.path.join(DATA_DIR, "parsed")
FAISS_DIR = os.path.join(DATA_DIR, "faiss")

#  абсолютна база (щоб absolute_path був правильний)
BASE_DIR = Path(__file__).resolve().parent.parent  # .../0001
# PROJECTS_DIR = (BASE_DIR / "data" / "projects" / "zips").resolve()
PROJECTS_DIR = (Path(DATA_DIR) / "projects" / "zips").resolve()
print("[INIT] Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("[READY] Embedding model loaded successfully.")

# print("[INIT] Loading FAISS index and metadata...")
# index = faiss.read_index(FAISS_PATH)
# meta = json.load(open(META_PATH, "r", encoding="utf-8"))
# print(f"[READY] Loaded {len(meta)} chunks into memory.")

print("[INIT] Loading FAISS index and metadata...")
index = None
meta = []
if os.path.exists(FAISS_PATH) and os.path.exists(META_PATH):
    index = faiss.read_index(FAISS_PATH)
    meta = json.load(open(META_PATH, "r", encoding="utf-8"))
    print(f"[READY] Loaded {len(meta)} chunks into memory.")
else:
    print("[WARN] FAISS index or metadata not found.")
    print("[WARN] Documentation search will be unavailable until indexes are built.")


class QueryRequest(BaseModel):
    query: str
    lang: str = "en"
    target: str | None = None  # stm32 / ra2l1 / mspm0 / etc.
    mode: str = "docs"
    sources: list[str] | None = None  # "docs" (default) - all documentation

def _mk_choices(results: list[dict]) -> list[dict]:
    """Додаємо id + absolute_path, і нормалізуємо поля."""
    choices = []
    for i, r in enumerate(results):
        rel = r.get("path") or r.get("relative_path") or ""
        abs_path = (PROJECTS_DIR / rel).resolve()
        choices.append({
            "id": i,
            "project": r.get("project", ""),
            "file": r.get("file", os.path.basename(rel)),
            "relative_path": r.get("relative_path", rel),
            "path": rel,  # залишаємо для сумісності
            "absolute_path": str(abs_path),
        })
    return choices


def _mk_md_table(choices: list[dict]) -> str:
    rows = "\n".join([f"| `{c['id']}` | `{c['project']}` | `{c['relative_path']}` |" for c in choices])
    return (
        "| ID | Project | Path |\n"
        "|----|---------|------|\n"
        f"{rows}\n\n"
        "Use: `open <id>`"
    )

def _make_sources(chunks: list[dict], limit: int = 5) -> list[dict]:
    sources = []
    seen = set()

    for c in chunks:
        pdf = c.get("source") or c.get("pdf") or "unknown"
        page = c.get("page")  # може бути None
        typ = c.get("type") or c.get("kind") or "text"

        key = (pdf, page, typ)
        if key in seen:
            continue
        seen.add(key)

        text = (c.get("text") or "").strip().replace("\n", " ")
        preview = text[:180] + ("…" if len(text) > 180 else "")

        sources.append({
            "pdf": pdf,
            "page": page,
            "type": typ,
            "preview": preview
        })

        if len(sources) >= limit:
            break

    return sources


def make_timestamped_name(filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace(" ", "_")
    return f"{timestamp}_{safe_name}"

def save_uploaded_file(upload: UploadFile, target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)

    filename = make_timestamped_name(upload.filename or "uploaded_file")
    out_path = os.path.join(target_dir, filename)

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return out_path


def rebuild_pdf_indexes():
    from parser.pdf_parser import parse_pdf
    from parser.table_parser import extract_tables
    from parser.register_parser import parse_registers
    from embeddings.build_index import build_index
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(PARSED_DIR, exist_ok=True)
    os.makedirs(FAISS_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    for file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, file)
        base = os.path.splitext(file)[0]

        text_out = os.path.join(PARSED_DIR, f"{base}.json")
        table_out = os.path.join(PARSED_DIR, f"{base}_tables.json")
        reg_out = os.path.join(PARSED_DIR, f"{base}_registers.json")

        try:
            parse_pdf(pdf_path, text_out)
        except Exception as e:
            print(f"[WARN] parse_pdf failed for {file}: {e}")

        try:
            extract_tables(pdf_path, table_out)
        except Exception as e:
            print(f"[WARN] extract_tables failed for {file}: {e}")

        try:
            parse_registers(pdf_path, reg_out)
        except Exception as e:
            print(f"[WARN] parse_registers failed for {file}: {e}")

    build_index()

    global index, meta
    index = faiss.read_index(FAISS_PATH)
    meta = json.load(open(META_PATH, "r", encoding="utf-8"))

def rebuild_single_pdf(pdf_path: str):
    from parser.pdf_parser import parse_pdf
    from parser.table_parser import extract_tables
    from parser.register_parser import parse_registers
    from embeddings.build_index import build_index

    os.makedirs(PARSED_DIR, exist_ok=True)
    os.makedirs(FAISS_DIR, exist_ok=True)

    file = os.path.basename(pdf_path)
    base = os.path.splitext(file)[0]

    text_out = os.path.join(PARSED_DIR, f"{base}.json")
    table_out = os.path.join(PARSED_DIR, f"{base}_tables.json")
    reg_out = os.path.join(PARSED_DIR, f"{base}_registers.json")

    try:
        parse_pdf(pdf_path, text_out)
    except Exception as e:
        print(f"[WARN] parse_pdf failed for {file}: {e}")

    try:
        extract_tables(pdf_path, table_out)
    except Exception as e:
        print(f"[WARN] extract_tables failed for {file}: {e}")

    try:
        parse_registers(pdf_path, reg_out)
    except Exception as e:
        print(f"[WARN] parse_registers failed for {file}: {e}")

    build_index()

    global index, meta
    index = faiss.read_index(FAISS_PATH)
    meta = json.load(open(META_PATH, "r", encoding="utf-8"))

def rebuild_single_pdf_task(pdf_path: str):
    INDEXING_STATUS["running"] = True
    INDEXING_STATUS["message"] = f"Indexing {os.path.basename(pdf_path)}"
    INDEXING_STATUS["last_error"] = None

    try:
        rebuild_single_pdf(pdf_path)
        INDEXING_STATUS["message"] = "Indexing completed"
    except Exception as e:
        INDEXING_STATUS["last_error"] = str(e)
        INDEXING_STATUS["message"] = "Indexing failed"
        print(f"[ERROR] PDF indexing failed: {e}")
    finally:
        INDEXING_STATUS["running"] = False

@app.post("/upload/pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        saved_path = save_uploaded_file(file, PDF_DIR)

        background_tasks.add_task(rebuild_single_pdf_task, saved_path)

        return {
            "status": "ok",
            "type": "pdf",
            "filename": os.path.basename(saved_path),
            "message": "PDF uploaded successfully. Indexing started in background."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {e}")


@app.post("/upload/zip")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    try:
        saved_path = save_uploaded_file(file, ZIP_DIR)

        unzip_projects()
        build_global_index()

        return {
            "status": "ok",
            "type": "zip",
            "filename": os.path.basename(saved_path),
            "message": "ZIP uploaded and indexed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZIP upload failed: {e}")

TARGET_ALIASES = {
    "stm32f103": ["stm32f103", "stm32f103c4", "stm32f103c8", "stm32f103rc", "stm32f103rg"],
    "ra2l1": ["ra2l1", "ek_ra2l1", "r20an0598"],
    "mspm0": ["mspm0", "mspm0_sdk", "mspm0g", "mspm0l"],
}
def matches_target(value: str, target: str | None) -> bool:
    if not target:
        return True

    aliases = TARGET_ALIASES.get(target.lower(), [target.lower()])
    value_low = value.lower()

    return any(a in value_low for a in aliases)


def score_table_chunk(c: dict) -> int:
    text = c.get("text", "")
    low = text.lower()

    score = 0
    score += text.count("|") * 2

    useful_words = [
        "symbol", "parameter", "test conditions",
        "typ", "min", "max", "unit",
        "adc", "characteristics"
    ]

    for w in useful_words:
        if w in low:
            score += 20

    # штраф за майже порожні таблиці
    if text.count("---") > text.count("symbol") + 3:
        score -= 30

    return score



def normalize_register_name(name: str) -> str:
    name = name.upper().strip()
    name = name.replace("->", "_")
    name = name.replace(".", "_")
    name = name.replace(" ", "_")
    while "__" in name:
        name = name.replace("__", "_")
    return name


def extract_register_candidates(query: str) -> list[str]:
    q = query.upper()
    q = q.replace("->", "_")
    q = q.replace(".", "_")
    q = re.sub(r"[^A-Z0-9_]+", " ", q)

    stop_words = {
        "EXPLAIN", "SHOW", "ALL", "BITS", "BIT", "REGISTER",
        "REGISTERS", "LIST", "AND", "WHAT", "DOES", "OF", "THE"
    }

    tokens = [t for t in q.split() if t not in stop_words]

    candidates = []

    # 1) RCC APB1RSTR -> RCC_APB1RSTR
    for i in range(len(tokens) - 1):
        if tokens[i] in {"RCC", "ADC", "TIM", "TIM1", "TIM2", "TIM3", "GPIO", "USART", "SPI", "I2C", "DMA"}:
            candidates.append(tokens[i] + "_" + tokens[i + 1])

    # 2) ADC_CR, TIM2_SR, RCC_APB1RSTR
    for t in tokens:
        if "_" in t and len(t) >= 5:
            candidates.append(t)

    # 3) APB1RSTR, CR2, SR, CR
    for t in tokens:
        if re.search(r"(RSTR|ENR|CR|CR1|CR2|SR|DR|ODR|IDR|BRR|BSRR|CCR|ARR|PSC)$", t):
            candidates.append(t)

    return list(dict.fromkeys(candidates))


@app.get("/documents") # return list of loaded documents with chunk counts
def list_documents():
    docs = {}

    for c in meta:
        source = c.get("source") or c.get("pdf")
        if not source:
            continue

        source = str(source)

        if source not in docs:
            docs[source] = {
                "id": source,
                "name": source,
                "type": c.get("type") or c.get("kind") or "text",
                "chunks": 0
            }

        docs[source]["chunks"] += 1

    return {
        "status": "ok",
        "documents": sorted(docs.values(), key=lambda x: x["name"])
    }


@app.post("/search")
async def search(req: QueryRequest):
    query = req.query.strip()
    query_lower = query.lower()

    table_keywords = [
        "table",
        "characteristics",
        "comparison",
        "compare",
        "features",
        "parameters",
        "electrical",
        "consumption"
    ]

    register_keywords = [
        "register",
        "bit",
        "bits",
        "mask",
        "offset",
        "cr",
        "sr",
        "ccmr",
        "ccer",
        "psc",
        "arr",
        "ccr"
    ]

    stk_keywords = [
        "stk",
        "nucleo",
        "board",
        "pinout",
        "pin",
        "header",
        "connector",
        "jumper",
        "cn",
        "hardware"
    ]

    #file_exts = [".c", ".h", ".cpp", ".hpp", ".s", ".py", ".xml", ".txt", ".asm"]
    is_file_query = (
        req.mode == "sdk" or
        query_lower.startswith(("search", "serch", "search file", "open ")) or
        bool(re.search(r"[A-Za-z0-9_\-]+\.(c|h|cpp|hpp|s|py|xml|txt|asm)", query_lower))
    )

    # =========================
    # FILE SEARCH
    # =========================
    if is_file_query:
        m = re.findall(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", query)
        filename = m[0] if m else re.sub(r"^(search file|search|serch|open)\s+", "", query_lower).strip()

        results = local_search_files(filename)
        if req.target:
            results = [
                r for r in results
                if matches_target(
                    str(r.get("project", "")) + " " +
                    str(r.get("path", "")) + " " +
                    str(r.get("relative_path", "")),
                    req.target
                )
            ]
        if not results:
            return {
                "status": "not_found",
                "type": "file",
                "answer": f"File `{filename}` not found for target `{req.target or 'all'}`."
            }

        exact = [r for r in results if r["file"].lower() == filename.lower()]

        # рівно 1 — повертаємо absolute_path
        if len(exact) == 1:
            r = exact[0]
            rel = r.get("path") or r.get("relative_path") or ""
            abs_path = (PROJECTS_DIR / rel).resolve()
            return {
                "status": "ok",
                "type": "file",
                "absolute_path": str(abs_path),
                "answer": f"Opened: `{r.get('project','')}/{r.get('relative_path', rel)}`"
            }

        #  кілька повертаємо markdown таблицю + choices з id/absolute_path
        choices = _mk_choices(exact if len(exact) > 1 else results)
        return {
            "status": "multiple",
            "type": "file",
            "answer": " Multiple files found:\n\n" + _mk_md_table(choices),
            "choices": choices
        }

    # =========================
    # FAISS SEARCH
    # =========================


    if index is None or not meta:
        return {
            "status": "not_found",
            "answer": "Documentation index is not available. Please upload PDFs or rebuild indexes first.",
            "sources": []
        }
    query_emb = await asyncio.to_thread(model.encode, [query], convert_to_numpy=True, normalize_embeddings=True)


    D, I = index.search(query_emb.astype("float32"), 5)
    best_score = float(D[0][0]) if len(D[0]) > 0 else 0.0
    if best_score < 0.25:
        return {
            "status": "not_found",
            "answer": "I don't have reliable information in the loaded documentation.",
            "sources": []
        }
    

    chunks = [meta[i] for i in I[0] if i < len(meta)]

    if req.sources:
        selected_sources = set(req.sources)

        filtered_by_sources = [
            c for c in chunks
            if str(c.get("source") or c.get("pdf") or "") in selected_sources
        ]

        if filtered_by_sources:
            chunks = filtered_by_sources
        else:
            return {
                "status": "not_found",
                "answer": "No reliable information found in the selected documentation.",
                "sources": []
            }
    filtered = []

    # target filter ONLY for docs/table/stk, NOT registers
    if req.target and req.mode in ["docs"]:
        target = req.target.lower()

        filtered = [
            c for c in chunks
            if target in str(c.get("source", "")).lower()
            or target in str(c.get("text", "")).lower()
    ]
    if filtered:
        chunks = filtered
    # else:
    #     return {
    #         "status": "not_found",
    #         "answer": f"No reliable documentation found for target `{req.target}`.",
    #         "sources": []
    #     }

    
    is_register_query = (
        req.mode == "registers"
        or "register" in query_lower
        or "bits" in query_lower
        or "bit" in query_lower
        or bool(re.search(r"\b[A-Z]{2,8}_[A-Z0-9_]{2,30}\b", query))
    )
    is_table_query = (
        any(k in query_lower for k in table_keywords)
        or query_lower.startswith("show table")
    )
    is_stk_query = any(k in query_lower for k in stk_keywords)

    SAFETY_RULES = (
        "Answer ONLY using the provided documentation context.\n"
        "Do not guess. Do not mix MCU families.\n"
        "If the answer is not present in the context, say: "
        "'I don't have reliable information in the loaded documentation.'\n\n"
    )
    
    # 1) REGISTERS
    if is_register_query:
        reg_match = None
        candidates = extract_register_candidates(query)

        if candidates:
            reg_match = candidates[0]

        if reg_match:
            reg_name = reg_match.upper()
            found = []

            for file in os.listdir(REGISTER_DIR):
                if file.endswith("_registers.json"):
                    try:
                        data = json.load(open(os.path.join(REGISTER_DIR, file), encoding="utf-8"))
                        for reg in data:
                            
                            db_name = normalize_register_name(reg.get("name", ""))
                            if (
                                reg_name == db_name
                                or reg_name in db_name
                                or db_name in reg_name
                            ):
                                reg["source"] = file
                                found.append(reg)
                    except:
                        continue

            if found:
                bits_clean = {}
                for r in found:
                    for b in r.get("bits", []):
                        m = re.match(r"Bit\s+([\d:]+)\s+([A-Z0-9_]+)\s*:?\s*(.*)", b, re.I)
                        if m:
                            num, name, desc = m.groups()
                            bits_clean[name] = {"bit": num, "desc": desc}

                md = f"## {reg_name}\n"
                md += "**Register description**\n\n"
                md += "### Bits\n| Bit | Name | Description |\n|-----|------|-------------|\n"
                for name, info in bits_clean.items():
                    md += f"| {info['bit']} | {name} | {info['desc']} |\n"
                # return {"status": "ok", "answer": md}
                return {
                    "status": "ok",
                    "answer": md,
                    "sources": [{"pdf": r.get("source", "registers.json"), "page": None, "type": "register", "preview": reg_name}]
                }

        # context = "\n".join(c["text"] for c in chunks)
        # prompt = (
        #     SAFETY_RULES +
        #     "Explain this STM32 register including all bits.\n\n"
        #     f"{context}\n\nQuestion: {query}"
        # )
        return {
            "status": "not_found",
            "answer": (
                f"Exact register definition for `{reg_match or query}` "
                "was not found in the loaded register database."
            ),
            "sources": []
        }


    # 2) TABLES (як у тебе було)
    elif is_table_query:
        table_chunks = [c for c in chunks if "|" in c["text"] or "---" in c["text"]]

        if table_chunks:
            output = []
            best_table = max(table_chunks, key=score_table_chunk)

            for line in best_table["text"].split("\n"):
                line = line.strip()

                if not line or "|" not in line:
                    continue

                cols = [p.strip() for p in line.split("|") if p.strip()]

                if all(c in ["---", "—"] for c in cols):
                    continue
                useful_cols = [c for c in cols if c not in ["—", "---"]]
                if len(useful_cols) < 2:
                    continue

                output.append("| " + " | ".join(cols) + " |")

            return {
                "status": "ok",
                "type": "table",
                "answer": "\n".join(output),
                "chunks_used": 1,
                "sources": _make_sources([best_table], limit=1)
            }

        context = "\n\n".join(c["text"] for c in chunks)
        prompt = (
            SAFETY_RULES +
            f"Show the documentation table exactly as it appears. Markdown format only.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}"
        )


    # 3) STK
    elif is_stk_query:
        stk_chunks = [c for c in chunks if any(k in c["text"].lower() for k in stk_keywords)]
        context = "\n\n".join([c["text"] for c in stk_chunks]) or "\n\n".join(c["text"] for c in chunks)
        prompt = (
            SAFETY_RULES +
            "You are a hardware assistant. Show the STM32 STK/Nucleo pinout or connector table. "
            "Return exact Markdown tables from documentation.\n\n"
            f"{context}\n\nQuestion: {query}"
        )

    

    # 4) FALLBACK
    else:
        context = "\n\n".join([c["text"] for c in chunks])
        prompt = (
            SAFETY_RULES +
            f"Answer in {req.lang} based on STM32 documentation.\n\n"
            f"{context}\n\nQuestion: {query}"
        )

    # SEND TO OLLAMA (як у тебе)
    resp = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "prompt": prompt}, stream=False)
    answer = ""
    for line in resp.text.split("\n"):
        try:
            js = json.loads(line)
            answer += js.get("response", "")
        except:
            continue

    # return {"status": "ok", "answer": answer.strip(), "chunks_used": len(chunks)}
    return {
        "status": "ok",
        "answer": answer.strip(),
        "chunks_used": len(chunks),
        "sources": _make_sources(chunks, limit=5)
    }
@app.get("/index/status")
def index_status():
    return INDEXING_STATUS


@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_loaded": index is not None,
        "chunks": len(meta)
    }
