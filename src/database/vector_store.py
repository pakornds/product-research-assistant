import os
import time  # Added for rate limiting
import pandas as pd
import shutil
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Define paths
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "products_catalog.csv",
)
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma_db"
)


def get_embeddings():
    # Updated to the standard embedding model.
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", task_type="retrieval_document"
    )


def ingest_data():
    """Ingests data from CSV to ChromaDB using batching to avoid Rate Limits."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    documents = []
    for _, row in df.iterrows():
        # Create a rich text representation for embedding
        page_content = (
            f"Product: {row['product_name']}\n"
            f"Category: {row['category']}\n"
            f"Brand: {row['brand']}\n"
            f"Description: {row['description']}\n"
            f"Price: ${row['current_price']}\n"
            f"Stock: {row['stock_quantity']}\n"
            f"Rating: {row['average_rating']}"
        )

        # Store all fields as metadata for filtering/retrieval
        metadata = row.to_dict()
        documents.append(Document(page_content=page_content, metadata=metadata))

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    print(f"Total documents to ingest: {len(splits)}")

    # Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    # --- BATCHING IMPLEMENTATION START ---

    # 1. Initialize empty ChromaDB
    # Note: 'embedding_function' is the new argument name (vs 'embedding') in recent Chroma versions
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=get_embeddings())

    # 2. Define Batch Parameters
    # Batch size 10-20 is usually safe for the free tier
    BATCH_SIZE = 15
    SLEEP_TIME = 2  # Seconds to wait between batches

    print("Starting batched ingestion...")

    for i in range(0, len(splits), BATCH_SIZE):
        batch = splits[i : i + BATCH_SIZE]

        print(
            f"Processing batch {i // BATCH_SIZE + 1} (Documents {i} to {i + len(batch)})..."
        )

        # Add batch to vector store
        vectorstore.add_documents(documents=batch)

        # Sleep to respect rate limits (Requests Per Minute)
        time.sleep(SLEEP_TIME)

    # --- BATCHING IMPLEMENTATION END ---

    print("Vector store created successfully.")
    return vectorstore


def get_vector_store():
    """Returns the existing vector store."""
    if not os.path.exists(DB_PATH):
        print("Vector store not found. Ingesting data...")
        return ingest_data()

    try:
        return Chroma(persist_directory=DB_PATH, embedding_function=get_embeddings())
    except Exception as e:
        msg = str(e)
        # Auto-rebuild if embedding dimension mismatch (e.g., old DB built with a different model)
        if "dimension" in msg.lower():
            print("Embedding dimension mismatch detected; rebuilding Chroma DB...")
            shutil.rmtree(DB_PATH, ignore_errors=True)
            return ingest_data()
        raise


def get_retriever():
    """Returns a retriever for the vector store."""
    vectorstore = get_vector_store()
    return vectorstore.as_retriever(search_kwargs={"k": 5})


if __name__ == "__main__":
    load_dotenv()
    try:
        ingest_data()
    except Exception as e:
        print(f"Error ingesting data: {e}")
