# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from pathlib import Path
# import json
# import re
# import zipfile
# import os
# from typing import Optional, List
# from datetime import datetime

# router = APIRouter(prefix="/code", tags=["code"])

# # Головна папка з проектами
# PROJECTS_ROOT = Path("../data/projects/zips").resolve()
# # Глобальний індекс
# GLOBAL_INDEX_PATH = PROJECTS_ROOT / "global_index.json"

# # Розширення кодових файлів
# CODE_EXT = {".c", ".h", ".cpp", ".hpp", ".s", ".asm", ".txt", ".md", ".ld", ".yaml", ".yml", ".xml", ".json", ".py", ".js", ".ts"}


# class SearchResponse(BaseModel):
#     status: str
#     query: str
#     results: Optional[List[dict]] = None
#     message: Optional[str] = None
#     projects_searched: Optional[List[str]] = None


# class ProjectMetadata(BaseModel):
#     name: str
#     source_zip: str
#     extracted_at: str
#     total_files: int
#     code_files: int
#     size_mb: float
#     description: Optional[str] = None


# def create_project_metadata(project_name: str, zip_path: Path, extract_dir: Path) -> dict:
#     """
#     Створює метадані для проекту
#     """
#     total_files = sum(1 for _ in extract_dir.rglob("*") if _.is_file())
#     code_files = sum(1 for _ in extract_dir.rglob("*") if _.is_file() and _.suffix.lower() in CODE_EXT)
    
#     # Розмір папки
#     size_bytes = sum(f.stat().st_size for f in extract_dir.rglob("*") if f.is_file())
#     size_mb = round(size_bytes / (1024 * 1024), 2)
    
#     metadata = {
#         "name": project_name,
#         "source_zip": zip_path.name,
#         "extracted_at": datetime.now().isoformat(),
#         "total_files": total_files,
#         "code_files": code_files,
#         "size_mb": size_mb,
#         "description": f"Low-level development examples from {project_name}"
#     }
    
#     return metadata


# def save_project_metadata(extract_dir: Path, metadata: dict):
#     """
#     Зберігає метадані проекту
#     """
#     metadata_path = extract_dir / "metadata.json"
#     metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
#     print(f"[METADATA] Saved metadata for {metadata['name']}")


# def build_project_index(extract_dir: Path, project_name: str) -> List[dict]:
#     """
#     Будує індекс для конкретного проекту
#     """
#     print(f"[INDEX] Building index for {project_name}...")
#     files_data: List[dict] = []
    
#     for path in extract_dir.rglob("*"):
#         # Пропускаємо метадані та індекси
#         if path.name in ["metadata.json", "index.json"]:
#             continue
            
#         if path.is_file() and path.suffix.lower() in CODE_EXT:
#             try:
#                 rel_path = path.relative_to(extract_dir).as_posix()
#                 files_data.append({
#                     "project": project_name,
#                     "path": rel_path,
#                     "name": path.name,
#                     "size": path.stat().st_size,
#                     "extension": path.suffix.lower(),
#                     "full_path": str(path.relative_to(PROJECTS_ROOT).as_posix())
#                 })
#             except Exception as e:
#                 print(f"[WARN] Cannot index {path}: {e}")
#                 continue
    
#     # Зберігаємо індекс проекту
#     index_path = extract_dir / "index.json"
#     index_path.write_text(json.dumps(files_data, indent=2), encoding="utf-8")
#     print(f"[SUCCESS] Indexed {len(files_data)} files for {project_name}")
    
#     return files_data


# def build_global_index() -> dict:
#     """
#     Будує глобальний індекс всіх проектів
#     """
#     print("[GLOBAL INDEX] Building global index...")
#     global_data = {
#         "generated_at": datetime.now().isoformat(),
#         "projects": [],
#         "total_projects": 0,
#         "total_files": 0
#     }
    
#     if not PROJECTS_ROOT.exists():
#         return global_data
    
#     for item in PROJECTS_ROOT.iterdir():
#         if item.is_dir() and not item.name.startswith('.'):
#             metadata_path = item / "metadata.json"
#             index_path = item / "index.json"
            
#             if metadata_path.exists() and index_path.exists():
#                 try:
#                     metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    
#                     global_data["projects"].append({
#                         "name": metadata["name"],
#                         "path": item.name,
#                         "code_files": metadata["code_files"],
#                         "size_mb": metadata["size_mb"],
#                         "description": metadata.get("description", ""),
#                         "extracted_at": metadata["extracted_at"]
#                     })
#                     global_data["total_files"] += metadata["code_files"]
#                 except Exception as e:
#                     print(f"[WARN] Cannot read metadata for {item.name}: {e}")
    
#     global_data["total_projects"] = len(global_data["projects"])
    
#     # Зберігаємо глобальний індекс
#     GLOBAL_INDEX_PATH.write_text(json.dumps(global_data, indent=2), encoding="utf-8")
#     print(f"[SUCCESS] Global index: {global_data['total_projects']} projects, {global_data['total_files']} files")
    
#     return global_data


# def unzip_projects():
#     """
#     Розпаковує всі ZIP файли у відповідні папки
#     """
#     if not PROJECTS_ROOT.exists():
#         try:
#             PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
#             print(f"[INFO] Created directory: {PROJECTS_ROOT}")
#         except Exception as e:
#             print(f"[ERROR] Cannot create {PROJECTS_ROOT}: {e}")
#             return
    
#     if not os.access(PROJECTS_ROOT, os.W_OK):
#         print(f"[ERROR] No write permission for {PROJECTS_ROOT}")
#         return
    
#     zip_files = list(PROJECTS_ROOT.glob("*.zip"))
#     if not zip_files:
#         print(f"[INFO] No ZIP files found in {PROJECTS_ROOT}")
#         return
    
#     print(f"[INFO] Found {len(zip_files)} ZIP file(s)")
    
#     for zip_path in zip_files:
#         project_name = zip_path.stem
#         extract_dir = PROJECTS_ROOT / project_name
        
#         if extract_dir.exists():
#             print(f"[SKIP] {project_name} already extracted")
#             continue
        
#         try:
#             if not zipfile.is_zipfile(zip_path):
#                 print(f"[ERROR] {zip_path.name} is not a valid ZIP file")
#                 continue
            
#             with zipfile.ZipFile(zip_path, 'r') as z:
#                 bad_file = z.testzip()
#                 if bad_file:
#                     print(f"[ERROR] Corrupted file in {zip_path.name}: {bad_file}")
#                     continue
                
#                 file_list = z.namelist()
#                 print(f"[INFO] Extracting {zip_path.name} ({len(file_list)} files)...")
                
#                 # Розпаковуємо
#                 z.extractall(extract_dir)
#                 print(f"[SUCCESS] Extracted {zip_path.name} -> {project_name}/")
                
#                 # Створюємо метадані
#                 metadata = create_project_metadata(project_name, zip_path, extract_dir)
#                 save_project_metadata(extract_dir, metadata)
                
#                 # Будуємо індекс для проекту
#                 build_project_index(extract_dir, project_name)
                
#         except zipfile.BadZipFile:
#             print(f"[ERROR] {zip_path.name} is corrupted")
#         except PermissionError:
#             print(f"[ERROR] No permission to extract {zip_path.name}")
#         except Exception as e:
#             print(f"[ERROR] Cannot unzip {zip_path.name}: {type(e).__name__} - {e}")


# def load_global_index() -> dict:
#     """
#     Завантажує глобальний індекс
#     """
#     if not GLOBAL_INDEX_PATH.exists():
#         return build_global_index()
    
#     try:
#         return json.loads(GLOBAL_INDEX_PATH.read_text(encoding="utf-8"))
#     except Exception as e:
#         print(f"[ERROR] Cannot load global index: {e}")
#         return build_global_index()


# def load_project_index(project_name: str) -> List[dict]:
#     """
#     Завантажує індекс конкретного проекту
#     """
#     project_dir = PROJECTS_ROOT / project_name
#     index_path = project_dir / "index.json"
    
#     if not index_path.exists():
#         return []
    
#     try:
#         return json.loads(index_path.read_text(encoding="utf-8"))
#     except Exception as e:
#         print(f"[ERROR] Cannot load index for {project_name}: {e}")
#         return []


# @router.post("/rebuild")
# def rebuild_all_indexes():
#     """
#     Повна перебудова всіх індексів
#     """
#     unzip_projects()
    
#     # Перебудовуємо індекси всіх проектів
#     for item in PROJECTS_ROOT.iterdir():
#         if item.is_dir() and not item.name.startswith('.'):
#             build_project_index(item, item.name)
    
#     # Будуємо глобальний індекс
#     global_data = build_global_index()
    
#     return {
#         "status": "ok",
#         "projects_indexed": global_data["total_projects"],
#         "total_files": global_data["total_files"],
#         "root": str(PROJECTS_ROOT)
#     }


# @router.post("/rebuild_project/{project_name}")
# def rebuild_project_index(project_name: str):
#     """
#     Перебудова індексу конкретного проекту
#     """
#     project_dir = PROJECTS_ROOT / project_name
    
#     if not project_dir.exists():
#         raise HTTPException(status_code=404, detail=f"Project {project_name} not found")
    
#     files = build_project_index(project_dir, project_name)
#     build_global_index()
    
#     return {
#         "status": "ok",
#         "project": project_name,
#         "files_indexed": len(files)
#     }


# @router.get("/projects")
# def list_projects():
#     """
#     Список всіх проектів з метаданими
#     """
#     global_index = load_global_index()
    
#     return {
#         "status": "ok",
#         "projects": global_index.get("projects", []),
#         "total_projects": global_index.get("total_projects", 0),
#         "total_files": global_index.get("total_files", 0)
#     }


# @router.get("/project/{project_name}")
# def get_project_info(project_name: str):
#     """
#     Детальна інформація про конкретний проект
#     """
#     project_dir = PROJECTS_ROOT / project_name
#     metadata_path = project_dir / "metadata.json"
    
#     if not metadata_path.exists():
#         raise HTTPException(status_code=404, detail=f"Project {project_name} not found")
    
#     try:
#         metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
#         index = load_project_index(project_name)
        
#         # Статистика по розширеннях
#         extensions = {}
#         for file in index:
#             ext = file.get("extension", "unknown")
#             extensions[ext] = extensions.get(ext, 0) + 1
        
#         return {
#             "status": "ok",
#             "metadata": metadata,
#             "files_count": len(index),
#             "extensions": extensions
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Cannot read project info: {e}")


# @router.get("/search_code", response_model=SearchResponse)
# def search_code(
#     query: str,
#     project: Optional[str] = None,
#     case_sensitive: bool = False,
#     max_results: int = 30
# ):
#     """
#     Пошук по коду в одному або всіх проектах
#     """
#     query = query.strip()
#     if not query:
#         raise HTTPException(status_code=400, detail="query is empty")
    
#     # Визначаємо в яких проектах шукати
#     if project:
#         projects_to_search = [project]
#     else:
#         global_index = load_global_index()
#         projects_to_search = [p["name"] for p in global_index.get("projects", [])]
    
#     if not projects_to_search:
#         return SearchResponse(
#             status="error",
#             query=query,
#             message="No projects found. Try /code/rebuild"
#         )
    
#     results = []
#     pattern = re.compile(re.escape(query), re.IGNORECASE if not case_sensitive else 0)
    
#     for proj_name in projects_to_search:
#         index = load_project_index(proj_name)
        
#         for file_info in index:
#             file_path = PROJECTS_ROOT / proj_name / file_info["path"]
            
#             if not file_path.exists():
#                 continue
            
#             try:
#                 text = file_path.read_text(encoding="utf-8", errors="ignore")
#             except Exception:
#                 continue
            
#             matches = list(pattern.finditer(text))
            
#             if matches:
#                 match = matches[0]
#                 idx = match.start()
                
#                 start = max(0, idx - 120)
#                 end = min(len(text), idx + 120)
#                 snippet = text[start:end].replace("\n", " ").strip()
                
#                 if start > 0:
#                     snippet = "..." + snippet
#                 if end < len(text):
#                     snippet = snippet + "..."
                
#                 results.append({
#                     "project": proj_name,
#                     "file": file_info["name"],
#                     "path": file_info["full_path"],
#                     "relative_path": file_info["path"],
#                     "snippet": snippet,
#                     "matches_count": len(matches),
#                     "line_number": text[:idx].count('\n') + 1,
#                     "extension": file_info.get("extension", "")
#                 })
            
#             if len(results) >= max_results:
#                 break
        
#         if len(results) >= max_results:
#             break
    
#     if not results:
#         return SearchResponse(
#             status="not_found",
#             query=query,
#             message=f"No matches for '{query}'",
#             projects_searched=projects_to_search
#         )
    
#     return SearchResponse(
#         status="ok",
#         query=query,
#         results=results,
#         message=f"Found {len(results)} matches",
#         projects_searched=projects_to_search
#     )


# @router.get("/search_by_filename")
# def search_by_filename(
#     filename: str,
#     project: Optional[str] = None
# ):
#     """
#     Пошук файлів за назвою
#     """
#     filename = filename.strip().lower()
#     if not filename:
#         raise HTTPException(status_code=400, detail="filename is empty")
    
#     if project:
#         projects_to_search = [project]
#     else:
#         global_index = load_global_index()
#         projects_to_search = [p["name"] for p in global_index.get("projects", [])]
    
#     results = []
    
#     for proj_name in projects_to_search:
#         index = load_project_index(proj_name)
        
#         for file_info in index:
#             if filename in file_info["name"].lower():
#                 results.append({
#                     "project": proj_name,
#                     "file": file_info["name"],
#                     "path": file_info["full_path"],
#                     "relative_path": file_info["path"],
#                     "extension": file_info.get("extension", "")
#                 })
    
#     return {
#         "status": "ok" if results else "not_found",
#         "query": filename,
#         "results": results,
#         "count": len(results),
#         "projects_searched": projects_to_search
#     }


# @router.get("/get_file")
# def get_file(path: str):
#     """
#     Отримати вміст файлу (path відносно PROJECTS_ROOT)
#     """
#     safe_path = Path(path)
#     full_path = (PROJECTS_ROOT / safe_path).resolve()
    
#     try:
#         full_path.relative_to(PROJECTS_ROOT)
#     except ValueError:
#         raise HTTPException(status_code=400, detail="invalid path - outside projects root")
    
#     if not full_path.exists():
#         raise HTTPException(status_code=404, detail="file not found")
    
#     if not full_path.is_file():
#         raise HTTPException(status_code=400, detail="path is not a file")
    
#     try:
#         content = full_path.read_text(encoding="utf-8", errors="ignore")
        
#         # Визначаємо проект
#         try:
#             rel_path = full_path.relative_to(PROJECTS_ROOT)
#             project_name = rel_path.parts[0] if rel_path.parts else "unknown"
#         except:
#             project_name = "unknown"
        
#         return {
#             "status": "ok",
#             "project": project_name,
#             "path": path,
#             "filename": full_path.name,
#             "size": full_path.stat().st_size,
#             "lines": content.count('\n') + 1,
#             "extension": full_path.suffix.lower(),
#             "content": content
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Cannot read file: {e}")


# @router.get("/zip_status")
# def zip_status():
#     """
#     Статус ZIP файлів та розпакованих проектів
#     """
#     zips = []
    
#     if not PROJECTS_ROOT.exists():
#         return {
#             "status": "error",
#             "message": f"Projects root does not exist: {PROJECTS_ROOT}"
#         }
    
#     for zip_path in PROJECTS_ROOT.glob("*.zip"):
#         project_name = zip_path.stem
#         extract_dir = PROJECTS_ROOT / project_name
        
#         zip_info = {
#             "name": zip_path.name,
#             "project_name": project_name,
#             "size_mb": round(zip_path.stat().st_size / (1024*1024), 2),
#             "extracted": extract_dir.exists(),
#             "has_index": (extract_dir / "index.json").exists() if extract_dir.exists() else False,
#             "has_metadata": (extract_dir / "metadata.json").exists() if extract_dir.exists() else False,
#             "is_valid": zipfile.is_zipfile(zip_path)
#         }
        
#         zips.append(zip_info)
    
#     global_index = load_global_index()
    
#     return {
#         "status": "ok",
#         "projects_root": str(PROJECTS_ROOT),
#         "zip_files": zips,
#         "total_projects": global_index.get("total_projects", 0),
#         "total_files": global_index.get("total_files", 0)
#     }


# @router.get("/debug")
# def debug_info():
#     """
#     Детальна діагностична інформація
#     """
#     info = {
#         "projects_root": str(PROJECTS_ROOT),
#         "exists": PROJECTS_ROOT.exists(),
#         "writable": os.access(PROJECTS_ROOT, os.W_OK) if PROJECTS_ROOT.exists() else False,
#         "global_index_exists": GLOBAL_INDEX_PATH.exists(),
#         "projects": []
#     }
    
#     if PROJECTS_ROOT.exists():
#         for item in PROJECTS_ROOT.iterdir():
#             if item.is_dir() and not item.name.startswith('.'):
#                 proj_info = {
#                     "name": item.name,
#                     "has_metadata": (item / "metadata.json").exists(),
#                     "has_index": (item / "index.json").exists(),
#                     "files_count": sum(1 for _ in item.rglob("*") if _.is_file())
#                 }
#                 info["projects"].append(proj_info)
    
#     return info
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import re
import zipfile
import os
from typing import Optional, List
from datetime import datetime
from collections import defaultdict  # NEW


def auto_rebuild_on_start():
    print("[AUTO] Checking ZIP files on startup...")
    unzip_projects()
    build_global_index()
    print("[AUTO] ZIP scan completed.")


router = APIRouter(prefix="/code", tags=["code"])

# Головна папка з проектами
PROJECTS_ROOT = Path("../data/projects/zips").resolve()
# Глобальний індекс
GLOBAL_INDEX_PATH = PROJECTS_ROOT / "global_index.json"

# Розширення кодових файлів
CODE_EXT = {
    ".c", ".h", ".cpp", ".hpp", ".s", ".asm",
    ".txt", ".md", ".ld", ".yaml", ".yml",
    ".xml", ".json", ".py", ".js", ".ts"
}

# NEW: regex для витягування токенів (імена функцій, змінних, макросів і т.п.)
TOKEN_REGEX = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


class SearchResponse(BaseModel):
    status: str
    query: str
    results: Optional[List[dict]] = None
    message: Optional[str] = None
    projects_searched: Optional[List[str]] = None


class ProjectMetadata(BaseModel):
    name: str
    source_zip: str
    extracted_at: str
    total_files: int
    code_files: int
    size_mb: float
    description: Optional[str] = None


def create_project_metadata(project_name: str, zip_path: Path, extract_dir: Path) -> dict:
    """
    Створює метадані для проекту
    """
    total_files = sum(1 for _ in extract_dir.rglob("*") if _.is_file())
    code_files = sum(1 for _ in extract_dir.rglob("*") if _.is_file() and _.suffix.lower() in CODE_EXT)

    # Розмір папки
    size_bytes = sum(f.stat().st_size for f in extract_dir.rglob("*") if f.is_file())
    size_mb = round(size_bytes / (1024 * 1024), 2)

    metadata = {
        "name": project_name,
        "source_zip": zip_path.name,
        "extracted_at": datetime.now().isoformat(),
        "total_files": total_files,
        "code_files": code_files,
        "size_mb": size_mb,
        "description": f"Low-level development examples from {project_name}"
    }

    return metadata


def save_project_metadata(extract_dir: Path, metadata: dict):
    """
    Зберігає метадані проекту
    """
    metadata_path = extract_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[METADATA] Saved metadata for {metadata['name']}")


def build_project_index(extract_dir: Path, project_name: str) -> List[dict]:
    """
    Будує індекс для конкретного проекту (список файлів)
    """
    print(f"[INDEX] Building index for {project_name}...")
    files_data: List[dict] = []

    for path in extract_dir.rglob("*"):
        # Пропускаємо метадані та індекси
        if path.name in ["metadata.json", "index.json", "content_index.json"]:
            continue

        if path.is_file() and path.suffix.lower() in CODE_EXT:
            try:
                rel_path = path.relative_to(extract_dir).as_posix()
                files_data.append({
                    "project": project_name,
                    "path": rel_path,
                    "name": path.name,
                    "size": path.stat().st_size,
                    "extension": path.suffix.lower(),
                    "full_path": str(path.relative_to(PROJECTS_ROOT).as_posix())
                })
            except Exception as e:
                print(f"[WARN] Cannot index {path}: {e}")
                continue

    # Зберігаємо індекс проекту
    index_path = extract_dir / "index.json"
    index_path.write_text(json.dumps(files_data, indent=2), encoding="utf-8")
    print(f"[SUCCESS] Indexed {len(files_data)} files for {project_name}")

    return files_data


# NEW: інвертований індекс контенту: слово -> список файлів
def build_content_index(extract_dir: Path, project_name: str) -> dict:
    """
    Створює інвертований індекс контенту:
    token (слово/ідентифікатор) -> список файлів (відносні шляхи в проекті)
    """
    print(f"[CONTENT INDEX] Building content index for {project_name}...")

    content_index = defaultdict(set)

    for path in extract_dir.rglob("*"):
        # Пропускаємо службові файли
        if path.name in ["metadata.json", "index.json", "content_index.json"]:
            continue

        if not (path.is_file() and path.suffix.lower() in CODE_EXT):
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARN] Cannot read {path} for content index: {e}")
            continue

        tokens = TOKEN_REGEX.findall(text)
        if not tokens:
            continue

        tokens = [t.lower() for t in tokens]
        rel_path = path.relative_to(extract_dir).as_posix()

        # Кладемо у індекс унікальні токени для цього файлу
        for token in set(tokens):
            content_index[token].add(rel_path)

    # Перетворюємо set -> list для збереження в JSON
    clean_index = {k: sorted(list(v)) for k, v in content_index.items()}

    index_path = extract_dir / "content_index.json"
    index_path.write_text(json.dumps(clean_index, indent=2), encoding="utf-8")
    print(f"[SUCCESS] Content index saved: {index_path}, tokens: {len(clean_index)}")

    return clean_index


def build_global_index() -> dict:
    """
    Будує глобальний індекс всіх проектів
    """
    print("[GLOBAL INDEX] Building global index...")
    global_data = {
        "generated_at": datetime.now().isoformat(),
        "projects": [],
        "total_projects": 0,
        "total_files": 0
    }

    if not PROJECTS_ROOT.exists():
        return global_data

    for item in PROJECTS_ROOT.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            metadata_path = item / "metadata.json"
            index_path = item / "index.json"

            if metadata_path.exists() and index_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

                    global_data["projects"].append({
                        "name": metadata["name"],
                        "path": item.name,
                        "code_files": metadata["code_files"],
                        "size_mb": metadata["size_mb"],
                        "description": metadata.get("description", ""),
                        "extracted_at": metadata["extracted_at"]
                    })
                    global_data["total_files"] += metadata["code_files"]
                except Exception as e:
                    print(f"[WARN] Cannot read metadata for {item.name}: {e}")

    global_data["total_projects"] = len(global_data["projects"])

    # Зберігаємо глобальний індекс
    GLOBAL_INDEX_PATH.write_text(json.dumps(global_data, indent=2), encoding="utf-8")
    print(f"[SUCCESS] Global index: {global_data['total_projects']} projects, {global_data['total_files']} files")

    return global_data


def unzip_projects():
    """
    Розпаковує всі ZIP файли у відповідні папки + будує індекси
    """
    if not PROJECTS_ROOT.exists():
        try:
            PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
            print(f"[INFO] Created directory: {PROJECTS_ROOT}")
        except Exception as e:
            print(f"[ERROR] Cannot create {PROJECTS_ROOT}: {e}")
            return

    if not os.access(PROJECTS_ROOT, os.W_OK):
        print(f"[ERROR] No write permission for {PROJECTS_ROOT}")
        return

    zip_files = list(PROJECTS_ROOT.glob("*.zip"))
    if not zip_files:
        print(f"[INFO] No ZIP files found in {PROJECTS_ROOT}")
        return

    print(f"[INFO] Found {len(zip_files)} ZIP file(s)")

    for zip_path in zip_files:
        project_name = zip_path.stem
        extract_dir = PROJECTS_ROOT / project_name

        if extract_dir.exists():
            print(f"[SKIP] {project_name} already extracted")
            continue

        try:
            if not zipfile.is_zipfile(zip_path):
                print(f"[ERROR] {zip_path.name} is not a valid ZIP file")
                continue

            with zipfile.ZipFile(zip_path, 'r') as z:
                bad_file = z.testzip()
                if bad_file:
                    print(f"[ERROR] Corrupted file in {zip_path.name}: {bad_file}")
                    continue

                file_list = z.namelist()
                print(f"[INFO] Extracting {zip_path.name} ({len(file_list)} files)...")

                # Розпаковуємо
                z.extractall(extract_dir)
                print(f"[SUCCESS] Extracted {zip_path.name} -> {project_name}/")

                # Створюємо метадані
                metadata = create_project_metadata(project_name, zip_path, extract_dir)
                save_project_metadata(extract_dir, metadata)

                # Будуємо індекс для проекту (файли)
                build_project_index(extract_dir, project_name)

                # NEW: Будуємо інвертований індекс контенту
                build_content_index(extract_dir, project_name)

        except zipfile.BadZipFile:
            print(f"[ERROR] {zip_path.name} is corrupted")
        except PermissionError:
            print(f"[ERROR] No permission to extract {zip_path.name}")
        except Exception as e:
            print(f"[ERROR] Cannot unzip {zip_path.name}: {type(e).__name__} - {e}")


def load_global_index() -> dict:
    """
    Завантажує глобальний індекс
    """
    if not GLOBAL_INDEX_PATH.exists():
        return build_global_index()

    try:
        return json.loads(GLOBAL_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Cannot load global index: {e}")
        return build_global_index()


def load_project_index(project_name: str) -> List[dict]:
    """
    Завантажує індекс конкретного проекту (список файлів)
    """
    project_dir = PROJECTS_ROOT / project_name
    index_path = project_dir / "index.json"

    if not index_path.exists():
        return []

    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Cannot load index for {project_name}: {e}")
        return []


def load_content_index(project_name: str) -> dict:
    """
    Завантажує інвертований індекс контенту для проекту
    """
    project_dir = PROJECTS_ROOT / project_name
    index_path = project_dir / "content_index.json"

    if not index_path.exists():
        return {}

    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Cannot load content index for {project_name}: {e}")
        return {}


@router.post("/rebuild")
def rebuild_all_indexes():
    """
    Повна перебудова всіх індексів:
    - розпаковка (якщо потрібно)
    - індекси файлів
    - індекси контенту
    - глобальний індекс
    """
    unzip_projects()

    # Перебудовуємо індекси всіх проектів
    if PROJECTS_ROOT.exists():
        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                files = build_project_index(item, item.name)
                build_content_index(item, item.name)
                print(f"[REBUILD] {item.name}: {len(files)} files")

    # Будуємо глобальний індекс
    global_data = build_global_index()

    return {
        "status": "ok",
        "projects_indexed": global_data["total_projects"],
        "total_files": global_data["total_files"],
        "root": str(PROJECTS_ROOT)
    }


@router.post("/rebuild_project/{project_name}")
def rebuild_project_index(project_name: str):
    """
    Перебудова індексу конкретного проекту:
    - індекс файлів
    - індекс контенту
    - оновлення глобального індексу
    """
    project_dir = PROJECTS_ROOT / project_name

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_name} not found")

    files = build_project_index(project_dir, project_name)
    build_content_index(project_dir, project_name)
    build_global_index()

    return {
        "status": "ok",
        "project": project_name,
        "files_indexed": len(files)
    }


@router.get("/projects")
def list_projects():
    """
    Список всіх проектів з метаданими
    """
    global_index = load_global_index()

    return {
        "status": "ok",
        "projects": global_index.get("projects", []),
        "total_projects": global_index.get("total_projects", 0),
        "total_files": global_index.get("total_files", 0)
    }


@router.get("/project/{project_name}")
def get_project_info(project_name: str):
    """
    Детальна інформація про конкретний проект
    """
    project_dir = PROJECTS_ROOT / project_name
    metadata_path = project_dir / "metadata.json"

    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_name} not found")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        index = load_project_index(project_name)

        # Статистика по розширеннях
        extensions = {}
        for file in index:
            ext = file.get("extension", "unknown")
            extensions[ext] = extensions.get(ext, 0) + 1

        return {
            "status": "ok",
            "metadata": metadata,
            "files_count": len(index),
            "extensions": extensions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read project info: {e}")


@router.get("/search_code", response_model=SearchResponse)
def search_code(
    query: str,
    project: Optional[str] = None,
    case_sensitive: bool = False,
    max_results: int = 30
):
    """
    Пошук по коду в одному або всіх проектах (повний контентний пошук)
    """
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is empty")

    # Визначаємо в яких проектах шукати
    if project:
        projects_to_search = [project]
    else:
        global_index = load_global_index()
        projects_to_search = [p["name"] for p in global_index.get("projects", [])]

    if not projects_to_search:
        return SearchResponse(
            status="error",
            query=query,
            message="No projects found. Try /code/rebuild"
        )

    results = []
    pattern = re.compile(re.escape(query), re.IGNORECASE if not case_sensitive else 0)

    for proj_name in projects_to_search:
        index = load_project_index(proj_name)

        for file_info in index:
            file_path = PROJECTS_ROOT / proj_name / file_info["path"]

            if not file_path.exists():
                continue

            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            matches = list(pattern.finditer(text))

            if matches:
                match = matches[0]
                idx = match.start()

                start = max(0, idx - 120)
                end = min(len(text), idx + 120)
                snippet = text[start:end].replace("\n", " ").strip()

                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."

                results.append({
                    "project": proj_name,
                    "file": file_info["name"],
                    "path": file_info["full_path"],
                    "relative_path": file_info["path"],
                    "snippet": snippet,
                    "matches_count": len(matches),
                    "line_number": text[:idx].count('\n') + 1,
                    "extension": file_info.get("extension", "")
                })

            if len(results) >= max_results:
                break

        if len(results) >= max_results:
            break

    if not results:
        return SearchResponse(
            status="not_found",
            query=query,
            message=f"No matches for '{query}'",
            projects_searched=projects_to_search
        )

    return SearchResponse(
        status="ok",
        query=query,
        results=results,
        message=f"Found {len(results)} matches",
        projects_searched=projects_to_search
    )





# fuzzy search helpers тестовий варіант для хорошого пошуку по токенах
def levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)

    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i in range(1, len(a) + 1):
        curr[0] = i
        ca = a[i - 1]
        for j in range(1, len(b) + 1):
            cost = 0 if ca == b[j - 1] else 1
            curr[j] = min(
                curr[j - 1] + 1,   # insertion
                prev[j] + 1,       # deletion
                prev[j - 1] + cost # substitution
            )
        prev, curr = curr, prev

    return prev[-1]

def similarity(a: str, b: str) -> float:
    """Similarity 0–100."""
    dist = levenshtein_distance(a, b)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 100.0
    return 100.0 * (1.0 - dist / max_len)

def token_match_score(query: str, token: str) -> float:
    if len(token) < 5:
        return 0.0
    if token.replace("_", "").startswith(query[:3]):
        return 88.0

    if token[:1] != query[:1]:
        pass
    
    if abs(len(token) - len(query)) > max(3, len(query) // 2):
        return 0.0

    # BEST CASES
    if token == query:
        return 100.0

    if token.startswith(query):
        return 95.0

    if query in token:
        return 90.0

    # If none of above → fuzzy
    score = similarity(query, token)

    # VERY STRICT fuzzy cutoff
    if score < 75:
        return 0.0

    return score

###############################################

@router.get("/fast_search")
def fast_search(
    token: str,
    project: Optional[str] = None
):
    """
    Швидкий пошук по інвертованому індексу контенту.
    Шукає токен (ім'я функції, змінної, макроса і т.д.) по content_index.json
    """
    token = token.strip().lower()
    if not token:
        raise HTTPException(status_code=400, detail="token is empty")

    # Визначаємо проекти
    if project:
        projects_to_search = [project]
    else:
        global_index = load_global_index()
        projects_to_search = [p["name"] for p in global_index.get("projects", [])]

    results = []

    for proj_name in projects_to_search:
        content_index = load_content_index(proj_name)
        if not content_index:
            continue

        if token in content_index:
            for file_rel_path in content_index[token]:
                results.append({
                    "project": proj_name,
                    "file": os.path.basename(file_rel_path),
                    "path": f"{proj_name}/{file_rel_path}",
                    "relative_path": file_rel_path
                })

    return {
        "status": "ok" if results else "not_found",
        "query": token,
        "results": results,
        "count": len(results),
        "projects_searched": projects_to_search
    }

# Fuzzy search по токенах
@router.get("/fuzzy_search")
def fuzzy_search(
    query: str,
    project: Optional[str] = None,
    max_results: int = 6,
    max_files_per_token: int = 3
):
    query = query.strip().lower()
    if not query:
        raise HTTPException(status_code=400, detail="query is empty")

    # Які проєкти сканувати
    if project:
        projects = [project]
    else:
        global_index = load_global_index()
        projects = [p["name"] for p in global_index.get("projects", [])]

    results = []

    for proj in projects:
        content_index = load_content_index(proj)
        if not content_index:
            continue

        for token, files in content_index.items():

            score = token_match_score(query, token)
            if score == 0:
                continue

            # обмежуємо кількість файлів у відповіді
            limited_files = files[:max_files_per_token]

            results.append({
                "project": proj,
                "token": token,
                "score": round(score, 2),
                "files_total": len(files),
                "files": [
                    {
                        "file": os.path.basename(f),
                        "relative_path": f,
                        "path": f"{proj}/{f}"
                    }
                    for f in limited_files
                ]
            })

    # Сортування: кращі збіги → вгору
    results.sort(key=lambda x: (-x["score"], len(x["token"])))

    return {
        "status": "ok" if results else "not_found",
        "query": query,
        "results": results[:max_results],
        "count": len(results)
    }
##################################################




@router.get("/search_by_filename")
def search_by_filename(
    filename: str,
    project: Optional[str] = None
):
    """
    Пошук файлів за назвою
    """
    filename = filename.strip().lower()
    if not filename:
        raise HTTPException(status_code=400, detail="filename is empty")

    if project:
        projects_to_search = [project]
    else:
        global_index = load_global_index()
        projects_to_search = [p["name"] for p in global_index.get("projects", [])]

    results = []

    for proj_name in projects_to_search:
        index = load_project_index(proj_name)

        for file_info in index:
            if filename in file_info["name"].lower():
                results.append({
                    "project": proj_name,
                    "file": file_info["name"],
                    "path": file_info["full_path"],
                    "relative_path": file_info["path"],
                    "extension": file_info.get("extension", "")
                })

    return {
        "status": "ok" if results else "not_found",
        "query": filename,
        "results": results,
        "count": len(results),
        "projects_searched": projects_to_search
    }
#####################zmina###########################
def search_files_by_name(filename: str):
    """Пошук файлів за назвою у всіх проектах (всередині Python)."""
    filename = filename.lower()
    results = []

    global_index = load_global_index()
    projects = [p["name"] for p in global_index["projects"]]

    for proj_name in projects:
        index = load_project_index(proj_name)
        for f in index:
            if filename in f["name"].lower():
                results.append(f)

    return results


def open_file_by_path(path: str):
    """Повертає вміст файлу за шляхом."""
    safe_path = Path(path)
    full_path = PROJECTS_ROOT / safe_path

    if not full_path.exists():
        return {"error": "file not found"}

    return {
        "filename": full_path.name,
        "size": full_path.stat().st_size,
        "content": full_path.read_text(encoding="utf-8", errors="ignore")
    }
####################################################
@router.get("/get_file")
def get_file(path: str):
    """
    Отримати вміст файлу (path відносно PROJECTS_ROOT)
    """
    safe_path = Path(path)
    full_path = (PROJECTS_ROOT / safe_path).resolve()

    try:
        full_path.relative_to(PROJECTS_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid path - outside projects root")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="file not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="path is not a file")

    try:
        content = full_path.read_text(encoding="utf-8", errors="ignore")

        # Визначаємо проект
        try:
            rel_path = full_path.relative_to(PROJECTS_ROOT)
            project_name = rel_path.parts[0] if rel_path.parts else "unknown"
        except Exception:
            project_name = "unknown"

        return {
            "status": "ok",
            "project": project_name,
            "path": path,
            "filename": full_path.name,
            "size": full_path.stat().st_size,
            "lines": content.count('\n') + 1,
            "extension": full_path.suffix.lower(),
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read file: {e}")


@router.get("/zip_status")
def zip_status():
    """
    Статус ZIP файлів та розпакованих проектів
    """
    zips = []

    if not PROJECTS_ROOT.exists():
        return {
            "status": "error",
            "message": f"Projects root does not exist: {PROJECTS_ROOT}"
        }

    for zip_path in PROJECTS_ROOT.glob("*.zip"):
        project_name = zip_path.stem
        extract_dir = PROJECTS_ROOT / project_name

        zip_info = {
            "name": zip_path.name,
            "project_name": project_name,
            "size_mb": round(zip_path.stat().st_size / (1024*1024), 2),
            "extracted": extract_dir.exists(),
            "has_index": (extract_dir / "index.json").exists() if extract_dir.exists() else False,
            "has_metadata": (extract_dir / "metadata.json").exists() if extract_dir.exists() else False,
            "has_content_index": (extract_dir / "content_index.json").exists() if extract_dir.exists() else False,
            "is_valid": zipfile.is_zipfile(zip_path)
        }

        zips.append(zip_info)

    global_index = load_global_index()

    return {
        "status": "ok",
        "projects_root": str(PROJECTS_ROOT),
        "zip_files": zips,
        "total_projects": global_index.get("total_projects", 0),
        "total_files": global_index.get("total_files", 0)
    }


@router.get("/debug")
def debug_info():
    """
    Детальна діагностична інформація
    """
    info = {
        "projects_root": str(PROJECTS_ROOT),
        "exists": PROJECTS_ROOT.exists(),
        "writable": os.access(PROJECTS_ROOT, os.W_OK) if PROJECTS_ROOT.exists() else False,
        "global_index_exists": GLOBAL_INDEX_PATH.exists(),
        "projects": []
    }

    if PROJECTS_ROOT.exists():
        for item in PROJECTS_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                proj_info = {
                    "name": item.name,
                    "has_metadata": (item / "metadata.json").exists(),
                    "has_index": (item / "index.json").exists(),
                    "has_content_index": (item / "content_index.json").exists(),
                    "files_count": sum(1 for _ in item.rglob("*") if _.is_file())
                }
                info["projects"].append(proj_info)

    return info

###############for search testing####################
def local_search_files(filename: str):
    """Пошук файлів за назвою у локальних індексах."""
    filename = filename.lower()
    results = []

    global_index = load_global_index()
    projects = [p["name"] for p in global_index.get("projects", [])]

    for proj in projects:
        index = load_project_index(proj)
        for f in index:
            if filename in f["name"].lower():
                results.append({
                    "project": proj,
                    "file": f["name"],
                    "path": f["full_path"],
                    "relative_path": f["path"]
                })

    return results


def local_open_file(path: str):
    """Повертає вміст файлу за шляхом."""
    full = (PROJECTS_ROOT / path).resolve()

    try:
        full.relative_to(PROJECTS_ROOT)
    except:
        return {"error": "invalid path"}

    if not full.exists():
        return {"error": "not found"}

    return {
        "file": full.name,
        "path": path,
        "size": full.stat().st_size,
        "content": full.read_text(errors="ignore")
    }
####################################################


# curl -X POST http://localhost:8000/code/rebuild
# curl "http://localhost:8000/code/fast_search?token=adc_read_data"
# curl "http://localhost:8000/code/fuzzy_search?query=adcst"
# curl "http://localhost:8000/code/search_code?query=R_ADC_ScanStart"
# curl "http://localhost:8000/code/search_by_filename?filename=adc_ep.c"

