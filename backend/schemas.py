from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    categories: List[str]  # lowercased categories from token

class ChatRequest(BaseModel):
    category: str  # "public" | "internal" | "private"
    message: str
    history: Optional[List[dict]] = None
    top_k: int = 5

class ChatChunk(BaseModel):
    text: str
    source: str

class ChatResponse(BaseModel):
    answer: str
    context: List[ChatChunk]

# These are for the /documents/flag endpoint, derived from your file
class DocumentCreateRequest(BaseModel):
    title: str
    description: str
    accessible_to: List[str]
    folder: str

class DocumentCreateResponse(BaseModel):
    ok: bool
    path: str