import os
import numpy as np
from openai import OpenAI
from typing import List

# This client is used by indexer.py and retriever.py
from dotenv import load_dotenv
load_dotenv() 

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embeds a list of texts using the configured OpenAI model."""
    texts = [t.replace("\n", " ") for t in texts]
    out = []
    # Batching loop for safety/efficiency
    for t in texts:
        r = _client.embeddings.create(model=EMBED_MODEL, input=t)
        out.append(r.data[0].embedding)
    return np.array(out, dtype="float32")