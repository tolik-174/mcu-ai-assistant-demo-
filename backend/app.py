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
from pydantic import BaseModel
from pathlib import Path
import faiss
import json
from sentence_transformers import SentenceTransformer
import requests
import os
import re
import asyncio

from code_search import router as code_router
from code_search import auto_rebuild_on_start
from code_search import local_search_files

app = FastAPI()
app.include_router(code_router)
auto_rebuild_on_start()

FAISS_PATH = "../data/faiss/local_multi.faiss"
META_PATH = "../data/faiss/local_multi_meta.json"
REGISTER_DIR = "../data/parsed"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

# ✅ абсолютна база (щоб absolute_path був правильний)
BASE_DIR = Path(__file__).resolve().parent.parent  # .../0001
PROJECTS_DIR = (BASE_DIR / "data" / "projects" / "zips").resolve()

print("[INIT] Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("[READY] Embedding model loaded successfully.")

print("[INIT] Loading FAISS index and metadata...")
index = faiss.read_index(FAISS_PATH)
meta = json.load(open(META_PATH, "r", encoding="utf-8"))
print(f"[READY] Loaded {len(meta)} chunks into memory.")


class QueryRequest(BaseModel):
    query: str
    lang: str = "en"


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

@app.post("/search")
async def search(req: QueryRequest):
    query = req.query.strip()
    query_lower = query.lower()

    table_keywords = ["table", "characteristics", "consumption", "tim", "timer", "adc", "usart", "i2c", "spi", "gpio"]
    register_keywords = ["register", "cr", "sr", "ccmr", "ccer", "psc", "arr", "ccr", "bit", "mask", "offset"]
    stk_keywords = ["stk", "nucleo", "board", "pin", "header", "connector", "jumper", "cn", "hardware"]

    file_exts = [".c", ".h", ".cpp", ".hpp", ".s", ".py", ".xml", ".txt", ".asm"]
    is_file_query = (
        query_lower.startswith("search file") or
        query_lower.startswith("open ") or
        any(query_lower.endswith(ext) for ext in file_exts)
    )

    # =========================
    # FILE SEARCH
    # =========================
    if is_file_query:
        m = re.findall(r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+", query)
        filename = m[0] if m else query_lower.replace("search file", "").replace("open", "").strip()

        results = local_search_files(filename)

        if not results:
            return {"status": "not_found", "type": "file", "answer": f"File `{filename}` not found."}

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
    query_emb = await asyncio.to_thread(model.encode, [query], convert_to_numpy=True, normalize_embeddings=True)
    D, I = index.search(query_emb.astype("float32"), 8)
    chunks = [meta[i] for i in I[0] if i < len(meta)]

    is_table_query = any(k in query_lower for k in table_keywords)
    is_register_query = any(k in query_lower for k in register_keywords)
    is_stk_query = any(k in query_lower for k in stk_keywords)

    # 1) STK
    if is_stk_query:
        stk_chunks = [c for c in chunks if any(k in c["text"].lower() for k in stk_keywords)]
        context = "\n\n".join([c["text"] for c in stk_chunks]) or "\n\n".join(c["text"] for c in chunks)
        prompt = (
            "You are a hardware assistant. Show the STM32 STK/Nucleo pinout or connector table. "
            "Return exact Markdown tables from documentation.\n\n"
            f"{context}\n\nQuestion: {query}"
        )

    # 2) TABLES (як у тебе було)
    elif is_table_query:
        table_chunks = [c for c in chunks if "|" in c["text"] or "---" in c["text"]]
        if table_chunks:
            output = []
            for c in table_chunks:
                for line in c["text"].split("\n"):
                    line = line.strip()
                    if "|" in line:
                        cols = [p.strip() or "—" for p in line.split("|")]
                        output.append("| " + " | ".join(cols) + " |")
                    elif re.match(r"table\s*\d+", line, re.I):
                        output.append(f"**{line}**")
            # return {"status": "ok", "type": "table", "answer": "\n".join(output), "chunks_used": len(table_chunks)}
            return {
                "status": "ok",
                "type": "table",
                "answer": "\n".join(output),
                "chunks_used": len(table_chunks),
                "sources": _make_sources(table_chunks, limit=5)
            }

        context = "\n\n".join(c["text"] for c in chunks)
        prompt = (
            "Show the STM32 documentation table exactly as it appears. Markdown format only.\n\n"
            f"{context}\n\nQuestion: {query}"
        )

    # 3) REGISTERS
    elif is_register_query:
        reg_match = None
        for token in query.split():
            if "_" in token and token.isupper():
                reg_match = token
                break

        if reg_match:
            reg_name = reg_match.upper()
            found = []

            for file in os.listdir(REGISTER_DIR):
                if file.endswith("_registers.json"):
                    try:
                        data = json.load(open(os.path.join(REGISTER_DIR, file), encoding="utf-8"))
                        for reg in data:
                            if reg_name in reg.get("name", "").upper():
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

        context = "\n".join(c["text"] for c in chunks)
        prompt = (
            "Explain this STM32 register including all bits.\n\n"
            f"{context}\n\nQuestion: {query}"
        )

    # 4) FALLBACK
    else:
        context = "\n\n".join([c["text"] for c in chunks])
        prompt = (
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
