from __future__ import annotations
import re
from typing import List

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_PARA_SPLIT = re.compile(r"\n\s*\n+")

def _normalize(s: str) -> str:
    """Normalizes whitespace and preserves paragraph breaks."""
    s = s.replace("\r", "")
    parts = _PARA_SPLIT.split(s.strip())
    parts = [" ".join(p.split()) for p in parts]
    return "\n\n".join(parts)

def _sentences(text: str) -> List[str]:
    """Splits text into sentences, respecting paragraph boundaries."""
    sents: List[str] = []
    for para in _PARA_SPLIT.split(text):
        para = para.strip()
        if not para:
            continue
        for s in _SENT_SPLIT.split(para):
            s = s.strip()
            if s:
                sents.append(s)
    return sents

def chunk_text(
    text: str,
    max_chars: int = 1800,   
    min_chars: int = 600,    
    overlap_sents: int = 1,  
) -> List[str]:
    """Splits raw text into overlapping chunks based on sentences."""
    sents = _sentences(text)
    chunks: List[str] = []
    curr: List[str] = []
    curr_len = 0

    def flush():
        if curr:
            chunks.append(" ".join(curr))
            curr.clear()
            nonlocal curr_len
            curr_len = 0

    for i, s in enumerate(sents):
        s_len = len(s) + 1 
        if curr_len + s_len <= max_chars or not curr:
            curr.append(s)
            curr_len += s_len
        else:
            flush()
            # overlap: carry last N sentences into the next chunk
            if overlap_sents > 0 and chunks and i > 0:
                # Find the index of the sentence N steps back
                carry_start = max(0, i - overlap_sents)
                carry = sents[carry_start:i]
                if carry:
                    curr.extend(carry)
                    curr_len = sum(len(x) + 1 for x in curr)
            
            curr.append(s)
            curr_len += s_len

    flush()

    # merge tiny last chunk
    if len(chunks) >= 2 and len(chunks[-1]) < min_chars:
        chunks[-2] = (chunks[-2] + " " + chunks[-1]).strip()
        chunks.pop()

    return [c for c in (x.strip() for x in chunks) if c]