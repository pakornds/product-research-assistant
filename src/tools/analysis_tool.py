from langchain.tools import tool
from src.database.vector_store import get_vector_store
import json


def calculate_margin(price: float, cost: float) -> float:
    """Calculate profit margin percentage"""
    if price == 0:
        return 0.0
    return ((price - cost) / price) * 100


@tool
def price_analysis(query: str) -> str:
    """
    Useful for analyzing pricing and profit margins of internal products.
    Use this to find low margin products, average margins, or pricing recommendations.
    """
    # 1. Retrieve relevant products (or all if needed, but let's stick to retrieval for scalability)
    # For "lowest profit margins", we might ideally want to query a SQL DB, but we have a vector store.
    # We'll fetch a larger batch of relevant items or just items matching the query context.

    vectorstore = get_vector_store()
    # Fetching more docs to do a better analysis
    docs = vectorstore.similarity_search(query, k=10)

    if not docs:
        return "No products found to analyze."

    products_data = []
    for doc in docs:
        meta = doc.metadata
        price = float(meta.get("current_price", 0))
        cost = float(meta.get("cost", 0))
        margin = calculate_margin(price, cost)

        products_data.append(
            {
                "name": meta.get("product_name"),
                "price": price,
                "cost": cost,
                "margin": round(margin, 2),
            }
        )

    # 2. Deterministic Analysis (e.g., sort by margin)
    # If the query asks for "lowest", we sort.
    if "lowest" in query.lower():
        products_data.sort(key=lambda x: x["margin"])
    elif "highest" in query.lower():
        products_data.sort(key=lambda x: x["margin"], reverse=True)

    # 3. Use LLM to generate insights
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)

    prompt = f"""
    Analyze the following product pricing data based on the user's query: "{query}"
    
    Data:
    {json.dumps(products_data, indent=2)}
    
    Provide a summary of the margins and any specific recommendations.
    Do not make up numbers, use the provided data.
    """

    response = llm.invoke(prompt)
    return response.content
