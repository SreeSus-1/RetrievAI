import json
import numpy as np
from pathlib import Path
from typing import Tuple, List

class VectorDB:
    def __init__(self, index_path: Path, meta_path: Path):
        self.index_path = index_path
        self.meta_path = meta_path
        self._X = None
        self._meta = None

    def load(self):
        self._X = np.load(self.index_path)["X"]
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self._meta = json.load(f)

    def save(self, X: np.ndarray, meta: List[dict]):
        np.savez_compressed(self.index_path, X=X)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def search(self, q: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        X = self._X
        qn = q / (np.linalg.norm(q) + 1e-9)
        Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
        sims = Xn @ qn
        idx = np.argsort(-sims)[:top_k]
        return [(int(i), float(sims[i])) for i in idx]

    @property
    def meta(self):
        return self._meta
