from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.agent.graph import run_agent
from src.api.db import init_db, log_query, get_queries, add_feedback
from src.database.models import QueryRequest, QueryResponse
from src.database.vector_store import get_vector_store
import os

app = FastAPI(title="Product Research Assistant API")


# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()

    # Skip heavy vector init when running tests
    if os.getenv("SKIP_VECTOR_INIT") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return

    # Ensure vector store is ready
    if not os.path.exists(os.path.join("data", "chroma_db")):
        try:
            print("Initializing vector store...")
            get_vector_store()
        except Exception as e:
            # During tests we don't want to fail startup if vector init is optional
            print(f"Vector store init skipped due to error: {e}")


class FeedbackRequest(BaseModel):
    query_id: int
    rating: int
    comment: Optional[str] = None


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
def query_agent(request: QueryRequest):
    try:
        result = run_agent(request.query)

        # Log to DB
        query_id = log_query(request.query, result["answer"], result["tools_used"])

        return QueryResponse(
            answer=result["answer"],
            tools_used=result["tools_used"],
            reasoning=result["reasoning"],
            query_id=query_id,
        )
    except Exception as e:
        # Surface error detail for debugging; FastAPI will still return 500.
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queries")
def get_history():
    return get_queries()


@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    add_feedback(feedback.query_id, feedback.rating, feedback.comment)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
