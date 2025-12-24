import os
import requests
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Suppress httpx and llama_stack_client INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("llama_stack_client").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DIMENSION = os.getenv("EMBEDDING_DIMENSION")

logger.info(f"LLAMA_STACK_BASE_URL: {LLAMA_STACK_BASE_URL}")
logger.info(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
logger.info(f"EMBEDDING_DIMENSION: {EMBEDDING_DIMENSION}")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Create vector store with embedding model configuration and hybrid search
vs = client.vector_stores.create(
    name="hr-benefits-hybrid",
    extra_body={
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "search_mode": "hybrid",  # Enable hybrid search (keyword + semantic)
        "bm25_weight": 0.5,  # Weight for keyword search (BM25)
        "semantic_weight": 0.5,  # Weight for semantic search
    }
)
logger.info(f"Vector store created: {vs.id}")

# Download clean text file
url = "https://raw.githubusercontent.com/burrsutter/fantaco-redhat-one-2026/refs/heads/main/basic-rag-llama-stack/source_docs/FantaCoFabulousHRBenefits_clean.txt"
logger.info(f"Downloading text file from {url}...")
response = requests.get(url)
text_content = response.text

logger.info(f"Downloaded {len(text_content)} characters of text")

# Save the text to source_docs folder for inspection
source_docs_path = os.path.join(os.path.dirname(__file__), "source_docs", "FantaCoFabulousHRBenefits_clean.txt")
os.makedirs(os.path.dirname(source_docs_path), exist_ok=True)
with open(source_docs_path, 'w', encoding='utf-8') as f:
    f.write(text_content)
logger.info(f"Saved text to: {source_docs_path}")

# Upload as text file
text_buffer = BytesIO(text_content.encode('utf-8'))
text_buffer.name = "hr-benefits-clean.txt"

uploaded_file = client.files.create(
    file=text_buffer,
    purpose="assistants"
)

# Attach file to vector store with custom chunking strategy
client.vector_stores.files.create(
    vector_store_id=vs.id,
    file_id=uploaded_file.id,
    chunking_strategy={
        "type": "static",
        "static": {
            "max_chunk_size_tokens": 100,
            "chunk_overlap_tokens": 10
        }
    }
)

logger.info(f"File {uploaded_file.id} added to vector store")

