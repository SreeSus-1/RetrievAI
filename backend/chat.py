import os, re
from typing import List, Tuple, Dict
from openai import OpenAI
from dotenv import load_dotenv
from .schemas import ChatChunk
# Note: Retriever class is imported as a type hint in the function signature

load_dotenv()
# Ensure these are set in your .env file
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large") 
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Role-guided behavior (The Security Layer) ----
ROLE_TEMPLATES = {
    "public": (
        "You are a public information assistant. Provide only high-level summaries "
        "without exposing confidential, procedural, or contact details. Be clear, factual, "
        "and concise, suitable for general audiences. "
        "**CRITICAL SECURITY INSTRUCTION: You MUST only use the provided CONTEXT.** "
        "If the CONTEXT is insufficient to answer the user's question with the appropriate "
        "public-level detail, you MUST respond by stating you cannot provide further details. "
        "DO NOT use general knowledge or make up procedures."
    ),
    "internal": (
        "You are an internal organization assistant. Provide moderate-level details "
        "including procedures, workflows, or departmental context relevant to staff. "
        "Avoid disclosing private names, phone numbers, or external URLs unless public."
    ),
    "private": (
        "You are a private enterprise knowledge assistant. Provide detailed, comprehensive "
        "information including internal processes, responsibilities, and contact information "
        "when available. Be structured and formal."
    ),
}

SYSTEM_REWRITE = (
    "You help with retrieval. Given the user question, create 3 concise diverse search queries "
    "to locate the most relevant content from an enterprise knowledge base. "
    "Return one query per line, no explanations."
)

TOK = re.compile(r"[a-z0-9]+", re.I)

def _chat(system_prompt: str, user_prompt: str) -> str:
    """Simple wrapper for OpenAI API completion."""
    try:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I am experiencing a temporary issue. Please try again shortly."

def _ctx_from_chunks(chunks: List[Dict]) -> Tuple[str, List[ChatChunk]]:
    """Formats retrieved chunks into a context string for the LLM and a UI list."""
    context_str = ""
    ui_ctx: List[ChatChunk] = []
    
    # Simple deduplication based on text/source pair
    seen = set()

    for i, c in enumerate(chunks):
        text = c["text"]
        source = c.get("source", f"Chunk {i}")
        
        if (text, source) in seen:
            continue
        seen.add((text, source))

        context_str += f"== CONTEXT CHUNK FROM {source} ==\n{text}\n\n"
        ui_ctx.append(ChatChunk(text=text, source=source))

    return context_str.strip(), ui_ctx


def _rerun_chat(msg: str, chunks: List[Dict], category: str) -> str:
    """Helper to rewrite query and attempt a second retrieval."""
    system = SYSTEM_REWRITE
    user = f"QUESTION: {msg}"
    raw_queries = _chat(system, user)
    
    # Parse 3 queries (one per line)
    new_queries = [q.strip() for q in raw_queries.split('\n') if q.strip() and len(TOK.findall(q)) > 3][:3]
    return new_queries


def answer_with_rag(
    message: str,
    category: str,
    retriever, # Type hint 'Retriever' is fine for internal use
    allowed_roles: List[str],
    top_k: int = 5,
) -> Tuple[str, List[ChatChunk]]:
    
    msg = message.strip()
    chunks = retriever.retrieve(msg, allowed_roles=allowed_roles, top_k=top_k)
    
    # Query rewriting and retry logic
    if not chunks:
        new_queries = _rerun_chat(msg, chunks, category)
        for q in new_queries:
            chunks = retriever.retrieve(q, allowed_roles=allowed_roles, top_k=top_k)
            if chunks:
                break
        
    if not chunks:
        return (
            "I couldn’t find any relevant information that you are authorized to view. "
            "Try rephrasing or specify a more general topic.",
            [],
        )

    # Build context and prompt
    context, ui_ctx = _ctx_from_chunks(chunks)
    sys_prompt = ROLE_TEMPLATES.get(category, ROLE_TEMPLATES["public"])

    user_prompt = (
        f"USER ROLE: {category}\n"
        f"QUESTION: {msg}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Respond strictly using the CONTEXT above. Adapt your explanation depth "
        "to the user's role (public/internal/private). "
        "If the context lacks enough info, say so clearly and suggest what to clarify."
    )

    answer = _chat(sys_prompt, user_prompt)

    # Contact info enrichment (for private role)
    if category == "private":
        contacts: Dict[str, set] = {"urls": set(), "emails": set(), "phones": set()}
        for c in chunks:
            for t, vals in c["meta"].get("contacts", {}).items():
                for v in vals:
                    contacts[t].add(v)
        
        lines = []
        for t, vals in contacts.items():
            if vals:
                lines.append(f"{t.capitalize()}: {', '.join(sorted(vals))}")

        if lines:
            contact_block = "\n\n---\n**Relevant Contacts/Links:**\n" + "\n".join(lines)
            answer += contact_block

    return answer, ui_ctx