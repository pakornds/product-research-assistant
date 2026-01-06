# System Architecture

## Overview

The Product Research Assistant is a modular AI system designed to help product managers make data-driven decisions. It combines **Retrieval-Augmented Generation (RAG)** for internal data, **Web Search** for external market data, and **Deterministic Analysis** for pricing calculations.

The core of the system is an **Agent** built with **LangGraph**, which autonomously routes queries to the appropriate tools.

## Components

### 1. Data Pipeline

- **Source:** `products_catalog.csv`
- **Ingestion:** Python script (`src/database/vector_store.py`) reads the CSV.
- **Processing:**
  - Text fields (Name, Description, Category) are combined into a rich text representation.
  - Text is chunked using `RecursiveCharacterTextSplitter`.
  - Embeddings are generated using `GoogleGenerativeAIEmbeddings`.
- **Storage:** `ChromaDB` (Local Vector Store) stores the embeddings and metadata.
- **Updates (current):** Full rebuild. Re-run `python src/database/vector_store.py` monthly to re-embed the CSV and recreate Chroma.
- **Updates (future):** Delta ingest as outlined below (add/update/delete without full re-index).

### 2. Monthly Update Strategy (Incremental Design)

While the current implementation performs a full rebuild for simplicity, a production-grade incremental update strategy would work as follows to avoid full re-indexing:

1.  **Change Detection**:

    - Load the new `products_catalog.csv` and the existing vector store.
    - Compare the new dataset against the stored data using `product_id` as the primary key.

2.  **Operations**:

    - **New Products**: Generate embeddings and `add` to ChromaDB.
    - **Updated Products**:
      - _Metadata only (Price, Stock)_: Use ChromaDB's `update` method to modify metadata without re-embedding (fast/cheap).
      - _Content (Description)_: Re-generate embeddings and `update` the vector (slower/costly).
    - **Deleted Products**: Identify IDs missing from the new CSV and `delete` them from ChromaDB.

3.  **Benefits**:
    - Reduces embedding costs (only pay for new/changed descriptions).
    - Minimizes downtime (updates can happen in the background).

### 3. AI Agent (The Brain)

- **Framework:** `LangGraph`
- **Model:** `ChatGoogleGenerativeAI` (Gemini 3 Flash)
- **Logic:**
  - The agent receives a user message.
  - It evaluates if it needs to call a tool (`product_catalog_rag`, `web_search`, `price_analysis`).
  - It executes the tool and receives the output.
  - It may call multiple tools in a loop (e.g., Get Internal Price -> Get External Price -> Compare).
  - Finally, it generates a natural language response.

### 3. Tools (The Skills)

- **Product RAG:** Queries ChromaDB to find relevant products.
- **Web Search:** Uses `TavilySearchResults` (or a mock) to find real-time market data.
- **Price Analysis:** A deterministic Python function calculates margins `((Price - Cost) / Price) * 100`. The LLM then summarizes these calculated metrics.

### 4. API Layer

- **Framework:** `FastAPI`
- **Endpoints:**
  - `POST /query`: Main interface for the agent.
  - `GET /queries`: Retrieves chat history from SQLite.
  - `POST /feedback`: Stores user feedback.

### 5. Deployment

- **Containerization:** Docker encapsulates the application and dependencies.
- **Orchestration:** Docker Compose manages the API service and volume mapping for data persistence.

## Production Considerations

### Scalability

- **Vector DB:** Migrate from local ChromaDB to a managed service like Pinecone or Weaviate for millions of records.
- **API:** Run multiple workers with Gunicorn/Uvicorn behind a load balancer (Nginx).
- **Async:** The current implementation is synchronous for simplicity. Converting to `async def` and using async DB drivers would improve throughput.

### Privacy & Security

- **Current:** Uses OpenAI API.
- **Enterprise:** Switch to Azure OpenAI for data privacy guarantees (no training on data).
- **Strict:** Self-host an open-source model (Llama 3) using vLLM within a private VPC.

### Latency

- **Caching:** Implement Redis caching for frequent queries (e.g., "What are our bestsellers?").
- **Embeddings:** Cache embeddings for the product catalog to avoid re-computing unchanged products.

## Load Testing Strategy

We use **Locust** for load testing. The test simulates concurrent users sending queries to the `/query` endpoint.

**Key Metrics to Monitor:**

1.  **RPS (Requests Per Second):** Throughput capacity.
2.  **Latency (p95):** 95th percentile response time (target < 2s for simple queries, < 5s for complex agent loops).
3.  **Error Rate:** Should be < 1%.

**Bottlenecks:**

- **LLM Latency:** The primary bottleneck is the external API call to Gemini.
- **Vector Search:** Local ChromaDB is fast for small datasets but may slow down under high concurrency without a dedicated server.
