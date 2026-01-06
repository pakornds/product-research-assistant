# Product Research Assistant

An AI-powered agent for e-commerce product research, pricing analysis, and market trend discovery.

### Quick Architecture Overview

- **Brain**: Google Gemini 3 Flash (via LangGraph for cyclic reasoning).
- **Memory**: ChromaDB (Vector Store) for product data + SQLite for interaction history.
- **Tools**:
  - `product_catalog_rag`: Semantic search over internal CSV data.
  - `web_search`: Real-time market data via Tavily API.
  - `price_analysis`: Deterministic Python math for margin calculations.

## Setup Instructions

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google API Key (Gemini)
- Tavily API Key

### 1. Installation

Clone the repository and navigate to the project folder:

```bash
git clone https://github.com/pakornds/quanxai-assignment.git
cd quanxai-assignment
```

Create a virtual environment and install dependencies using `uv`:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Or using standard `pip`:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys.

### 3. Data Ingestion

Initialize the vector database with the product catalog:

```bash
python src/database/vector_store.py
```

## Run the Application

### Local Run

Start the FastAPI server:

```bash
uvicorn src.api.app:app --reload
```

The API will be available at `http://localhost:8000`.

### Docker Run

Build and run with Docker Compose:

```bash
docker-compose up --build
```

## Test the API

You can test the API using `curl` or the Swagger UI at `http://localhost:8000/docs`.

### Example Queries

**1. Product Catalog RAG**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What wireless headphones do we have in stock?"}'
```

**2. Web Search**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Current market price for noise-cancelling headphones?"}'
```

**3. Price Analysis**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Which products have lowest profit margins?"}'
```

**4. Multi-Tool Complex Query**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Should we adjust AudioMax headphones pricing vs competitors?"}'
```

## Load Testing

To run the load tests using Locust:

1. Ensure the API is running (`uvicorn src.api.app:app`).
2. Run Locust:
   ```bash
   locust -f load_tests/locustfile.py
   ```
3. Open `http://localhost:8089` in your browser.
4. Set the number of users (e.g., 10), spawn rate (e.g., 1), and host (http://localhost:8000), then click "Start".

**Latest run (Locust, host=http://localhost:8000):**

- **Requests:** /query 19 (18 failed), /health 9 (0 failed); total 28 requests
- **Latency:** /query median ≈ 35s, p95 ≈ 78s, p99 ≈ 78s; /health median ≈ 3ms
- **Throughput:** ~0.5 RPS aggregate during the run
- **Status:** /query saw 95% failures due to upstream rate limits; /health succeeded
- **Bottleneck:** Gemini rate limits on concurrent calls (LLM/tool dependency)
- **Next steps:** add request queueing/backoff for LLM calls, reduce concurrency in load, add caching for hot queries, and consider mock mode under load tests.

## Testing Status

- Automated tests are not implemented/run for this submission; please ignore test gaps.

## Architecture

See [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) for detailed system design and diagrams.

## Limitations & Future Improvements

### What's Not Implemented / Limitations

- **Authentication**: The API currently has no authentication mechanism.
- **Search Fallback**: If the Tavily API key is missing or the quota is exceeded, the system falls back to a mock search implementation which returns static data.
- **Local Vector Store**: ChromaDB is running locally. In a production environment, a persistent server-based vector database would be preferred.
- **Session History**: The agent is stateless per request; no thread/conversation continuity yet.
- **Automated Tests**: Integration/end-to-end tests are not implemented/run; test coverage is effectively absent for this submission.
- **Feedback Flow**: Feedback endpoint is stubbed; only DB scripts exist—no end-to-end feedback handling or surfacing.

### What I Would Improve

- **Caching**: Implement Redis caching for frequent queries to reduce latency and LLM costs.
- **Frontend**: Build a simple React or Streamlit UI for better user interaction.
- **CI/CD**: Set up GitHub Actions for automated testing and deployment.
- **Error Handling**: Add more granular error handling and retry logic for external API calls.

### What I Learned

- **Tooling & LangGraph**: Designing cyclic agent flows and tool-routing with LangGraph.
- **Vector Store (ChromaDB)**: Building and querying a product RAG pipeline with metadata filters.
- **Databases**: Using SQLite for history/feedback persistence alongside Chroma for retrieval.
- **Testing**: Writing pytest-style unit tests for deterministic functions and API routes.
- **Load Testing**: Using Locust to probe p50/p95/p99 latency and surface bottlenecks.

### Challenges I Faced

- **Tool Orchestration**: Reliable tool-calling required clear docstrings and schema alignment.
- **LLM/Embedding Limits**: Managed rate limits with batched ingestion for Gemini embeddings.
- **Data Consistency**: Keeping SQLite history/feedback and vector data in sync across runs.
- **Test Isolation**: Mocked external APIs (Tavily/Gemini) to keep tests fast and deterministic.
- **Performance Under Load**: LLM latency dominated p95/p99; caching is the next mitigation step.

## What I Tried (Worked / Not Worked)

- **Worked: Embedding pipeline** — Rebuilt Chroma with `models/gemini-embedding-001` and auto-recovery for dimension mismatches.
- **Worked: Batched ingestion** — Batching (15 docs, 2s sleep) stabilized embedding rate limits during ingest.
- **Worked: Reasoning-first agent** — System prompt enforces reasoning before tool calls; parsing extracts reasoning separately.
- **Worked: Test isolation** — Added lazy model init and `.env` loading; tests run without real LLM calls when mocked.
- **Not Worked: High-concurrency load** — Gemini rate limits cause 95% failures at ~0.5 RPS during Locust; needs backoff/queueing or mock mode.
- **Not Worked: Session continuity** — Threaded/session memory not implemented; agent remains stateless per request.
- **Partially Worked: Docker/run** — Local runs are fine; load tests under Docker not validated due to LLM rate limits.
