

# # backend/finetune.py  (optional utility; NOT used by RAG)
# from __future__ import annotations
# import json
# from pathlib import Path
# from .utils import DATA_DIR, INDEX_DIR
# from .chunker import chunk_text  # use your real chunker

# def build_train_jsonl(out_path: Path | None = None, max_examples: int | None = None) -> Path:
#     """
#     Build a synthetic chat dataset for optional fine-tuning.
#     This does NOT affect RAG; it’s only for model style tuning later.
#     """
#     if out_path is None:
#         out_path = INDEX_DIR / "train.jsonl"
#     out_path.parent.mkdir(parents=True, exist_ok=True)

#     roles = ["public", "internal", "private"]
#     records = []

#     for role in roles:
#         d = (DATA_DIR / role)
#         if not d.exists():
#             continue
#         for p in d.rglob("*.txt"):
#             text = p.read_text(encoding="utf-8", errors="ignore").strip()
#             if not text:
#                 continue
#             for ch in chunk_text(text, max_chars=1800, min_chars=600, overlap_sents=1):
#                 prompt = (
#                     "You are an assistant. Answer using this passage only.\n"
#                     f"PASSAGE:\n{ch}\n\n"
#                     "QUESTION: Summarize key points for a colleague."
#                 )
#                 completion = "• Point 1\n• Point 2\n• Point 3"
#                 records.append({
#                     "messages": [
#                         {"role": "system", "content": "Follow instructions and be concise. Use 3 bullet points."},
#                         {"role": "user", "content": prompt},
#                         {"role": "assistant", "content": completion},
#                     ]
#                 })
#                 if max_examples and len(records) >= max_examples:
#                     break
#             if max_examples and len(records) >= max_examples:
#                 break

#     with out_path.open("w", encoding="utf-8") as f:
#         for r in records:
#             f.write(json.dumps(r, ensure_ascii=False) + "\n")

#     print(f"[finetune] wrote {len(records)} examples -> {out_path}")
#     return out_path

# if __name__ == "__main__":
#     build_train_jsonl()
