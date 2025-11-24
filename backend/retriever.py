from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict
import numpy as np

from .utils import INDEX_DIR
from .embedder import embed_texts


class Retriever:
    """
    Loads embeddings + metadata from the index,
    embeds queries, applies RBAC based on CATEGORY role,
    and returns top-k chunks with their metadata.
    """

    def __init__(self):
        self.X: np.ndarray = np.zeros((0, 0), dtype="float32")
        self.X_norm: np.ndarray = np.zeros((0, 0), dtype="float32")
        self.meta: List[Dict] = []
        self.load()

    def load(self) -> None:
        """
        Load the current index and metadata from disk.
        Called at startup and again after /documents/flag → build_index().
        """
        idx_path = INDEX_DIR / "index.npz"
        meta_path = INDEX_DIR / "meta.json"

        if not idx_path.exists() or not meta_path.exists():
            if self.X.size == 0:
                # First-time startup with no index at all
                raise RuntimeError("Missing index. Run: python -m backend.indexer")
            print("[retriever] WARNING: Index files not found during reload. Keeping old in-memory index.")
            return

        data = np.load(idx_path)
        X = data["X"].astype("float32")
        # Normalize rows for cosine similarity
        X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)

        self.X = X
        self.X_norm = X_norm
        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))

        print(f"[retriever] Reloaded index: {self.X.shape[0]} chunks.")

    # ---- embedding ----
    def _embed_query(self, q: str) -> np.ndarray:
        arr = np.array(embed_texts([q]), dtype="float32")
        v = arr[0]
        v /= (np.linalg.norm(v) + 1e-8)
        return v

    # ---- main retrieve ----
    def retrieve(self, query: str, allowed_roles: List[str], top_k: int = 8) -> List[Dict]:
        """
        Retrieve top_k chunks where category_role is in allowed_roles.
        We intentionally ignore folder_role for access, so
        PUBLIC sections inside Internal/Private folders are still visible
        to public users.
        """
        query = (query or "").strip()
        if not query or self.X_norm.size == 0:
            return []

        allowed = {r.lower() for r in allowed_roles}

        q = self._embed_query(query)
        sims = self.X_norm @ q
        order = np.argsort(-sims)

        results: List[Dict] = []

        for i in order:
            m = self.meta[i]
            category_role = m.get("category_role", "public").lower()

            # RBAC: category-level only
            if category_role not in allowed:
                continue

            text = (m.get("chunk_text") or "").strip()
            if not text:
                continue

            results.append(
                {
                    "text": text,
                    "meta": m,
                    "cos": float(sims[i]),
                }
            )

            if len(results) >= max(1, int(top_k)):
                break

        print(
            f"[retriever] Returned {len(results)} chunks for roles {sorted(allowed)}"
        )
        return results
