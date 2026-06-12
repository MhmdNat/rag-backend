# Astra Backend — RAG API for CIS Controls v8

FastAPI backend powering Astra: handles RAG queries (retrieve → rerank → generate),
streams responses via Server-Sent Events, and persists chats, messages, and feedback
to MySQL.

**Frontend repo:** [Astra Frontend](https://github.com/MhmdNat/rag-chat-ui)

---

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (dependency management)
- Docker (for MySQL and Weaviate)
- [Ollama](https://ollama.com) installed locally, with a model pulled (e.g. `ollama pull qwen2.5:7b`)
- (Optional) A LangSmith API key for tracing — get one at https://smith.langchain.com

---

## 1. Start the database and vector store

This project needs **MySQL** (chat/message/feedback storage) and **Weaviate** (vector store for retrieval).

Create a `docker-compose.yml` in the project root:

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: astra
      MYSQL_USER: astra_user
      MYSQL_PASSWORD: astra_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.27.0
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "none"
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  mysql_data:
  weaviate_data:
```

Then run:

```bash
docker compose up -d
```

---

## 2. Configure environment variables

Create a `.env` file in the project root:

```env
# MySQL
DB_USER=astra_user
DB_PASSWORD=astra_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=astra

# LangSmith (optional but required by current startup check)
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=astra

# Hugging Face (optional, speeds up model downloads)
HF_TOKEN=your_hf_token_here
```

---

## 3. Install dependencies

```bash
uv sync
```

> **GPU users:** if you want the embedding/reranker models to run on CUDA instead of CPU,
> confirm `uv run python -c "import torch; print(torch.cuda.is_available())"` prints `True`.
> If it prints `False`, see the troubleshooting note at the bottom of this README.

---

## 4. Ingest your documents into Weaviate

Run your ingestion script/notebook to embed and load the CIS Controls v8 document(s)
into the `RAGDocs` Weaviate collection before starting the API — the chatbot has nothing
to retrieve from until this step is done.

```bash
uv run python -m main.py ingest -s <data/data.pdf>
```


---

## 5. Start Ollama

Make sure Ollama is running and the model used in `src/query/apiCommunication/sendToOllama.py`
is pulled:

```bash
ollama pull qwen2.5:7b
ollama serve
```

---

## 6. Run the API server

```bash
uv run python -m uvicorn src.api.rag_api:app --reload
```

The API will be available at `http://localhost:8000`. Database tables are created
automatically on startup via `init_db()`.

Health check:

```bash
curl http://localhost:8000/api/health
```

---

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/query` | POST | Send a new message, returns SSE stream of tokens + metadata |
| `/api/regenerate` | POST | Regenerate a response, returns SSE stream |
| `/api/feedback` | POST | Submit thumbs up/down + optional reason |
| `/api/chats` | GET | List chats for a user |
| `/api/chats/{chat_id}/messages` | GET | Get messages (with version history) for a chat |
| `/api/chats/{chat_id}/user/{user_id}` | DELETE | Delete a chat |

---

## Troubleshooting

**Reranker/embeddings running on CPU and queries take ~30s:**
PyTorch may be resolving to the CPU wheel. Check:
```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```
If it shows `+cpu` and `False`, ensure `pyproject.toml` has:
```toml
[tool.uv]
torch-backend = "cu121"
```
and that `torch` is pinned to an exact version (e.g. `torch==2.5.1`) rather than `>=`.

**`PermissionError: [WinError 10013]` on Windows:**
Windows Firewall is blocking a socket used by uvicorn's reload process. Either run
without `--reload`, or remove the relevant outbound firewall rule for Python:
```powershell
netsh advfirewall firewall delete rule name="Python" dir=out
```
