"""
Vector Store for RAG
Loads documents from knowledge base and creates searchable vector store
"""
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
from .logger import get_logger

load_dotenv()

logger = get_logger("vector_store")

# Paths
ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "data" / "knowledge_base"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

def build_vector_store():
    """Load documents, split into chunks, and create vector store."""

    logger.info("Building vector store...")

    # 1. Load documents
    logger.info(f"Loading documents from {KB_DIR}...")
    loader = DirectoryLoader(
        str(KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader
    )
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} documents")

    # 2. Split into chunks
    logger.info("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")

    # 3. Create vector store
    logger.info("Generating embeddings and storing in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_STORE_DIR)
    )
    logger.info(f"Vector store created at {VECTOR_STORE_DIR}")

    return vector_store

def load_vector_store():
    """Load existing vector store."""

    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            f"Vector store not found at {VECTOR_STORE_DIR}. "
            "Run build_vector_store() first."
        )

    return Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=embeddings
    )

def search_vector_store(query: str, top_k: int = 3):
    """Search vector store for relevant documents."""

    vector_store = load_vector_store()
    results = vector_store.similarity_search_with_score(query, k=top_k)

    return results
