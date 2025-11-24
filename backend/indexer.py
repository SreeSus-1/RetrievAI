from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Dict
import numpy as np

from .utils import INDEX_DIR, DATA_DIR, ROLE_TO_DIRS
from .chunker import chunk_text
from .embedder import embed_texts

# --- Roles and regexes -------------------------------------------------------

ROLE_NAMES = {"public", "internal", "private"}

# Matches blocks like:
# ==============================
# CATEGORY: PUBLIC
# ==============================
CATEGORY_BLOCK_RE = re.compile(
    r"=+\s*\n\s*CATEGOR(?:Y|IES):\s*(PUBLIC|INTERNAL|PRIVATE)\s*\n=+\s*",
    re.I,
)

URL_RE = re.compile(r"url:\s*(https?://\S+)", re.I)
EMAIL_RE = re.compile(
    r"email:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
    re.I,
)
PHONE_RE = re.compile(
    r"(?:phn|phone):\s*([\+\d][\d\s\-().]{7,})",
    re.I,
)


def extract_contacts(text: str) -> Dict[str, list]:
    """Extract url:/email:/phone:/phn: contact info from text."""
    return {
        "urls": URL_RE.findall(text),
        "emails": EMAIL_RE.findall(text),
        "phones": PHONE_RE.findall(text),
    }


def _read_text(path: Path) -> str:
    """Safe file read."""
    try:
        if path.suffix.lower() == ".pdf":
            # Optional PDF support
            try:
                from pypdf import PdfReader
            except ImportError:
                return ""
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def parse_sections(text: str, fallback_role: str) -> List[Dict[str, str]]:
    """
    Parse CATEGORY blocks of the form:

    ==============================
    CATEGORY: PUBLIC
    ==============================

    The text between blocks is assigned to that role.
    If no blocks are found, assign the whole doc to fallback_role.
    """
    out: List[Dict[str, str]] = []

    matches = list(CATEGORY_BLOCK_RE.finditer(text))
    if matches:
        for i, m in enumerate(matches):
            role = m.group(1).strip().lower()
            if role not in ROLE_NAMES:
                continue

            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if body:
                out.append({"role": role, "text": body})

    if not out and text.strip():
        # no CATEGORY blocks → treat whole doc as one section with folder role
        out = [{"role": fallback_role, "text": text.strip()}]

    return out


def find_files() -> List[Dict]:
    """
    Find all files under Data/raw for each logical role,
    based on ROLE_TO_DIRS in utils.py.
    Returns list of dicts: {"path": Path, "folder_role": "public"/"internal"/"private"}
    """
    files: List[Dict] = []

    for folder_role, dir_names in ROLE_TO_DIRS.items():
        for dirname in dir_names:
            root = DATA_DIR / dirname
            if not root.exists():
                print(f"[index] WARNING: Directory not found: {root}")
                continue

            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                if p.suffix.lower() not in {".txt", ".md", ".pdf"}:
                    continue
                files.append({"path": p, "folder_role": folder_role})

    return files


def build_index() -> None:
    print("\n[index] Rebuilding index...\n")

    file_entries = find_files()
    if not file_entries:
        print("[index] No documents found.")
        return

    all_texts: List[str] = []
    all_meta: List[Dict] = []

    for entry in file_entries:
        path: Path = entry["path"]
        folder_role: str = entry["folder_role"]

        # Skip helper meta files if any
        if path.name.endswith("_meta.txt"):
            continue

        raw = _read_text(path)
        if not raw.strip():
            continue

        sections = parse_sections(raw, fallback_role=folder_role)

        print(f"[index] File: {path.name}")
        print(f"        Folder role: {folder_role}")
        print(f"        Section roles: {[s['role'] for s in sections]}")

        for sec in sections:
            category_role = sec["role"]    # public/internal/private from CATEGORY tag
            body = sec["text"]
            contacts = extract_contacts(body)

            # Small header helps LLM see where this came from
            header = (
                f"FILE: {path.name}  "
                f"FOLDER: {folder_role}  "
                f"CATEGORY: {category_role}\n"
            )

            chunks = chunk_text(header + body)
            for idx, ch in enumerate(chunks):
                all_texts.append(ch)
                all_meta.append(
                    {
                        "path": str(path.resolve()),
                        "folder_role": folder_role,      # physical folder
                        "category_role": category_role,  # sensitivity tag
                        "chunk_id": idx,
                        "chunk_text": ch,
                        "contacts": contacts,
                    }
                )

    if not all_texts:
        print("[index] Nothing to embed.")
        return

    print(f"[index] Embedding {len(all_texts)} chunks…")

    # Batch embedding (simple version; could batch in chunks if huge)
    X = np.array(embed_texts(all_texts), dtype="float32")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(INDEX_DIR / "index.npz", X=X)
    (INDEX_DIR / "meta.json").write_text(
        json.dumps(all_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[index] ✅ Index built successfully with {len(all_texts)} chunks.\n")


if __name__ == "__main__":
    build_index()
