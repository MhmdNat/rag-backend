# RAG — Retrieval-Augmented Generation Toolkit

Professional, production-minded README for running, developing, and deploying this RAG project.

## Project overview
- Purpose: run a lightweight Retrieval-Augmented Generation (RAG) stack that ingests PDFs, stores embeddings in a vector store (Weaviate), and answers queries using a local LLM (Ollama) with human feedback captured in LangSmith.
- Structure: ingestion, embedding model, vectorstore helpers, query pipeline, a small CLI (`main.py`) and a FastAPI-based web API (`src/api/feedback_api.py`).

## Requirements
- Python 3.12+
- Docker & Docker Compose (for Weaviate)
- Ollama (local LLM runtime) or an alternative endpoint
- Environment variables (see `.env.example` below)

Dependencies are declared in `pyproject.toml`. To install into a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Installing with `pip install -e .` uses the `pyproject.toml` dependencies.

## Quick start

1) Start Weaviate locally (Docker Compose):

```bash
docker-compose up -d weaviate
# View logs:
docker-compose logs -f weaviate
# Stop:
docker-compose down
```

This repository contains `docker-compose.yml` preconfigured to run Weaviate on `http://localhost:8080` and gRPC on `50051`. Data persistency is mounted to `./weaviate_data`.

2) Start Ollama (local LLM):

- Install/run Ollama according to your OS and make sure the Ollama daemon is listening (default `http://127.0.0.1:11434`). The project sends generation requests to `http://127.0.0.1:11434/api/generate` with a configured `model` (see `src/query/apiCommunication/sendToOllama.py`).

3) Set environment variables (create `.env`):

```
LANGCHAIN_API_KEY=your_langchain_or_langsmith_key
# Optional overrides (add if needed):
# WEAVIATE_URL=http://localhost:8080
```

4) Ingest a PDF (CLI):

```bash
# Example: ingest a local PDF into Weaviate class/index `RAGDocs`
python main.py ingest --source data/pdfs/your.pdf --index RAGDocs --batch-size 500
```

5) Query (CLI):

```bash
python main.py query --query "What is control 1?" --index RAGDocs --top-k 5
```

6) Run the web API (FastAPI):

```bash
# Development server
uvicorn "src.api.feedback_api:app" --host 0.0.0.0 --port 8000 --reload

# The API will warm shared models on startup and requires LANGCHAIN_API_KEY in the environment.
```

## CLI 

The CLI entrypoint is `main.py` (Click-based).
- `ingest` — ingest PDF or local file to vectorstore
  - `--source, -s` Path or URL to ingest (required)
  - `--batch-size, -b` Batch size for vector storage (default 500)
  - `--index, -i` Weaviate index/class (default `RAGDocs`)
  - `--force, -f` Force re-ingestion (ignore cache)

- `query` — run a local RAG pipeline from the terminal
  - `--query, -q` Text to query (required)
  - `--index, -i` Weaviate index/class (default `RAGDocs`)
  - `--top-k, -k` Number of top passages to retrieve/rerank (default 5)

Examples:

```bash
python main.py ingest -s data/pdfs/cis_controls.pdf -i RAGDocs
python main.py query -q "What is control 6?" -k 5
```

## Web API 

Start the app with `uvicorn "src.api.feedback_api:app" --reload`.

Endpoints:
- `GET /api/health` — returns `{ "status": "ok" }`.

- `POST /api/query` — run RAG pipeline and capture LangSmith trace.
  - Request model: `src/api/dto/Query.py` -> fields: `query` (str), `top_k` (int), `index` (str)
  - Response model: `src/api/dto/Query.py` -> `run_id`, `query`, `rewritten_query`, `answer`
  - Example curl:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is CIS control 1?","top_k":5,"index":"RAGDocs"}'
```

- `POST /api/feedback` — submit human feedback to LangSmith for a given run.
  - Request model: `src/api/dto/Feedback.py` -> `run_id` (str), `score` (0 or 1), `comment` (optional)
  - Response: confirmation with `feedback_id` and message.
  - Example curl:

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"run_id":"<run-id>","score":1,"comment":"Helpful answer"}'
```

Notes:
- The API uses `LANGCHAIN_API_KEY` from the environment at startup. The FastAPI `lifespan` warms models on first run so the first request is fast.
- LangSmith tracing is used to capture `run_id` for feedback linking.

## How the pipeline works
- Query rewrite: `src/query/rewrite_query.py` to normalize/clarify the user prompt.
- Retrieval: `src/query/retriever.py` fetches top candidates from Weaviate.
- Reranking: `src/query/reranker.py` extracts and reranks the most relevant passages.
- Prompting: `src/query/apiCommunication/sendToOllama.py` builds a strict prompt and POSTs to the local Ollama HTTP API (`127.0.0.1:11434`).
- Feedback: `src/api/feedback_api.py` sends human feedback scores/comments to LangSmith.

## Weaviate (Docker)

This project ships a `docker-compose.yml` with a `weaviate` service. Key points:
- Ports: `8080` (HTTP), `50051` (gRPC)
- Data path: `./weaviate_data` is mounted into the container for persistence.
- Important environment variables (in the compose file):
  - `QUERY_DEFAULTS_LIMIT` — default query limit
  - `AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED` — allow anonymous access
  - `PERSISTENCE_DATA_PATH` — container data path
  - `DEFAULT_VECTORIZER_MODULE` — set to `none` (vectorization handled externally)

Commands:

```bash
# Start in background
docker-compose up -d weaviate

# Follow logs
docker-compose logs -f weaviate

# Remove and clear volume data (careful)
docker-compose down -v
```
