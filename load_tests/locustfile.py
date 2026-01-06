from locust import HttpUser, task, between
import random


class ProductResearchUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def rag_query(self):
        """Simulate a common RAG query (lighter load)."""
        self.client.post(
            "/query", json={"query": "What wireless headphones do we have in stock?"}
        )

    @task(1)
    def complex_query(self):
        """Simulate a complex multi-tool query (heavier load)."""
        self.client.post(
            "/query",
            json={
                "query": "Should we adjust AudioMax headphones pricing vs competitors?"
            },
        )

    @task(2)
    def price_analysis(self):
        """Simulate a price analysis query."""
        self.client.post(
            "/query", json={"query": "Which products have lowest profit margins?"}
        )

    @task(1)
    def health_check(self):
        """Check health endpoint."""
        self.client.get("/health")
