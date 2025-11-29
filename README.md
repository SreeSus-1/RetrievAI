RetrievAI — A Role-Aware, Knowledge-Augmented Conversational Agent

RetrievAI is a dual-RBAC (Role-Based Access Control), retrieval-augmented AI chatbot designed for secure enterprise environments. It combines dense semantic retrieval, grounded generation, and fine-grained permission filtering to deliver accurate, cited, and policy-compliant responses for users across three access levels:

🔵 Public Users – read-only, high-level summaries

🟡 Internal Users – detailed operational content

🔴 Private/Admin Users – full access, including document updates + flagging

RetrievAI demonstrates how real organizations can integrate RAG (Retrieval-Augmented Generation) with security, freshness, and auditability—features missing in most traditional chatbots.

🚀 Key Features
✅ Dual-RBAC Enforcement

RetrievAI enforces permissions at two levels:

Folder-Level RBAC — Public, Internal, Private directories

In-Document RBAC — CATEGORY: PUBLIC / INTERNAL / PRIVATE sections inside mixed documents

This ensures zero leakage and fine-grained control.

🔍 Dense Semantic Retrieval

Uses OpenAI embeddings (text-embedding-3-large)

Vector similarity search powered by NumPy

Chunk metadata includes file name + role for traceability

🧩 Custom Chunker

Each document is segmented into ~1–2k character chunks with:

FILE:<filename> CATEGORY:<role>


This enables exact rehydration and precise citation.

⚡ Hot-Reload Indexing

Private/Admin users can:

Flag documents

Upload updated files

Trigger automatic re-indexing

Retriever reloads instantly—no server restart needed

🧠 Grounded Generation

LLM outputs only from retrieved evidence:

No hallucinations

If insufficient evidence → returns
“Insufficient authorized information.”

📊 Three-Level Access Demo

Your demo includes examples for:

Public user responses

Internal user cascade

Private (Admin) detailed responses

Flagging → re-indexing → updated retrieval

🏗️ System Architecture
User → Login (Role) → RBAC Filter → Retriever → LLM Generator → RBAC Filter → Response

Components:

main.py – FastAPI router + endpoints

auth.py – Minimal token-based login

retriever.py – Dense embedding index, chunk filtering

indexer.py – Chunking + embedding building

chat.py – RAG generation + refusal logic

Data/raw/ – public, internal, private folders

📁 Folder Structure
RetrievAI/
│── backend/
│   ├── main.py
│   ├── auth.py
│   ├── retriever.py
│   ├── indexer.py
│   ├── chat.py
│   ├── utils.py
│── Data/
│   └── raw/
│       ├── Public/
│       ├── Internal/
│       ├── Private/
│── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│── README.md
│── requirements.txt

🛠️ Tech Stack
Layer	Tools
Backend	FastAPI, Uvicorn
Retrieval	NumPy, OpenAI embeddings
Document handling	pypdf, regex
Security	Dual RBAC, token authentication
Frontend	HTML/CSS/JS
Storage	Local file system (Public/Internal/Private)
⚙️ Installation & Setup
1. Clone repository
git clone https://github.com/yourusername/RetrievAI.git
cd RetrievAI

2. Install dependencies
pip install -r requirements.txt

3. Add .env file
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini

4. Run backend
uvicorn backend.main:app --reload

5. Open frontend

Open in browser:

frontend/index.html

🧪 Experiments & Results
✔ Public vs Internal vs Private Behavior

Public users receive brief, high-level summaries

Internal users receive operational details

Private users receive full content + contact + procedural data

✔ Flagging + Re-Indexing

Updated documents immediately affect retrieval (Figure shown in paper).

✔ Quantitative Evaluation
Metric	Result
Groundedness	92%
Citation correctness	95%
RBAC Violations	0%
Refusal Rate	17% (correct behavior)
Latency (local)	P50: 180 ms, P95: 430 ms
📸 Screenshots (Add Your Images Here)
System Architecture

Login UI

Example: Public Access

Example: Internal Access

Example: Private Access

🔒 Security Model

RetrievAI guarantees:

No unauthorized content retrieval

Document-level + section-level permission filtering

Redaction and refusal when evidence is missing

Traceable citations for every answer

📘 Use Cases

Enterprise helpdesk

University internal knowledge portals

HR policy assistants

Document-sensitive organizations

Any environment needing safe LLM answers

🎯 Future Work

Add neural re-ranker for improved retrieval

Deploy on cloud with persistent storage

Multi-agent support (verification + reranking agent)

User studies for usability + trust metrics

Vector database integration (FAISS, Qdrant, Pinecone)

👩‍💻 Authors

Ramya Sree Kanijam
Alam K Sathya Chowdary LNU
Lakshmi Sahithi Likhya Paruchuri
Texas A&M University – Corpus Christi

⭐ If you like this project, please star the repository!
