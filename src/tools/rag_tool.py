from langchain.tools import tool
from src.database.vector_store import get_retriever
from langchain_google_genai import ChatGoogleGenerativeAI


@tool
def product_catalog_rag(query: str) -> str:
    """
    Useful for answering questions about products in the internal catalog.
    Use this to find product details, stock levels, prices, and descriptions.
    Input should be a specific question about products.
    """
    retriever = get_retriever()
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)

    # We can use a simple RetrievalQA chain or just retrieve and format.
    # For simplicity and effectiveness, let's retrieve and let the agent handle the final answer,
    # but the tool itself should return a helpful string.

    docs = retriever.invoke(query)

    if not docs:
        return "No relevant products found in the catalog."

    # Format the retrieved documents
    result = "Found the following relevant products:\n\n"
    for i, doc in enumerate(docs, 1):
        result += f"{i}. {doc.page_content}\n\n"

    return result
