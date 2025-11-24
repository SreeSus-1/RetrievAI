from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import os
import re

from .schemas import (
    LoginRequest,
    LoginResponse,
    ChatRequest,
    ChatResponse,
)
from .auth import login as do_login, decode_token
from .retriever import Retriever
from .chat import answer_with_rag
from .utils import DATA_DIR, ROOT
from .indexer import build_index

app = FastAPI(title="RBAC RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# SINGLETON RETRIEVER
# --------------------------------------------------------------------

_GLOBAL_RETRIEVER: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Provide the single shared Retriever instance."""
    global _GLOBAL_RETRIEVER
    if _GLOBAL_RETRIEVER is None:
        print("[main] Initializing Retriever singleton…")
        _GLOBAL_RETRIEVER = Retriever()
    return _GLOBAL_RETRIEVER


# --------------------------------------------------------------------
# AUTH + RBAC
# --------------------------------------------------------------------

def require_auth(authorization: str = Header("")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def cascade(role: str) -> List[str]:
    """
    Role cascade:
      public  -> ['public']
      internal -> ['public', 'internal']
      private -> ['public', 'internal', 'private']
    """
    role = (role or "").lower()
    return {
        "public": ["public"],
        "internal": ["public", "internal"],
        "private": ["public", "internal", "private"],
    }.get(role, ["public"])


# --------------------------------------------------------------------
# ENDPOINTS
# --------------------------------------------------------------------

@app.post("/auth/login", response_model=LoginResponse)
def route_login(req: LoginRequest):
    out = do_login(req.username, req.password)
    if not out:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return out


@app.post("/chat", response_model=ChatResponse)
async def route_chat(
    req: ChatRequest,
    user=Depends(require_auth),
    retriever_service: Retriever = Depends(get_retriever),
):
    requested = (req.category or "").strip().lower()
    user_roles = [c.lower() for c in user.get("categories", [])]

    if requested not in user_roles:
        raise HTTPException(
            status_code=403,
            detail=f"User not authorized for {requested}",
        )

    # Cascade role → allowed sensitivity levels
    cascaded = cascade(requested)
    # (Optional intersect with user_roles – safe but not strictly needed)
    allowed_roles = [r for r in cascaded if r in {"public", "internal", "private"}]

    answer, ctx = answer_with_rag(
        message=req.message,
        category=requested,
        retriever=retriever_service,
        allowed_roles=allowed_roles,
        top_k=req.top_k,
    )

    return {"answer": answer, "context": ctx}


@app.post("/documents/flag")
async def documents_flag(
    title: str = Form(...),
    description: str = Form(""),  # currently unused but kept
    folder: str = Form(...),      # "public" | "internal" | "private"
    file: UploadFile = File(...),
    user=Depends(require_auth),
    retriever_service: Retriever = Depends(get_retriever),
):
    """
    Upload / replace a document in the chosen folder.
    - Only private users can flag.
    - Deletes any old files with the same slug prefix.
    - Saves new file.
    - Rebuilds index and reloads retriever in memory.
    """
    user_roles = {c.lower() for c in user.get("categories", [])}
    if "private" not in user_roles:
        raise HTTPException(
            status_code=403,
            detail="Only private users can flag documents",
        )

    folder = (folder or "").strip().lower()
    FOLDER_MAP = {"public": "Public", "internal": "Internal", "private": "Private"}
    if folder not in FOLDER_MAP:
        raise HTTPException(status_code=400, detail="Invalid folder")

    target_dir = DATA_DIR / FOLDER_MAP[folder]
    target_dir.mkdir(parents=True, exist_ok=True)

    # Slug by title
    base_slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-") or "doc"

    # Delete older versions
    deleted_count = 0
    for old in target_dir.glob(f"{base_slug}_*.*"):
        try:
            old.unlink()
            deleted_count += 1
            print(f"[flag] Deleted old file: {old.name}")
        except Exception as e:
            print(f"[flag] Failed to delete {old}: {e}")

    # Save new file
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ext = os.path.splitext(file.filename)[1].lower() or ".txt"
    fpath = target_dir / f"{base_slug}_{ts}{ext}"
    fpath.write_bytes(await file.read())
    print(f"[flag] Saved new file: {fpath}")

    # Rebuild index
    print("[flag] Rebuilding index after flag…")
    build_index()

    # Reload retriever in memory
    print("[flag] Reloading retriever in memory…")
    retriever_service.load()

    return {
        "ok": True,
        "path": str(fpath.relative_to(ROOT)),
        "deleted_files": deleted_count,
    }


@app.get("/health")
def route_health():
    return {"status": "ok", "message": "RBAC RAG chatbot API running"}


# --------------------------------------------------------------------
# FRONTEND STATIC
# --------------------------------------------------------------------

FRONTEND_DIST_PATH = Path(__file__).resolve().parents[1] / "frontend"
if FRONTEND_DIST_PATH.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST_PATH), html=True), name="static")
