import os
import requests
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from io import BytesIO

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# Create vector store with embedding model configuration and hybrid search
vs = client.vector_stores.create(
    name="hr-benefits-hybrid",
    extra_body={
        "embedding_model": "sentence-transformers/nomic-ai/nomic-embed-text-v1.5",
        "embedding_dimension": 768,
        "search_mode": "hybrid",  # Enable hybrid search (keyword + semantic)
        "bm25_weight": 0.5,  # Weight for keyword search (BM25)
        "semantic_weight": 0.5,  # Weight for semantic search
    }
)
print(f"Vector store created: {vs.id}")

# Download clean text file
url = "https://raw.githubusercontent.com/burrsutter/fantaco-redhat-one-2026/refs/heads/main/basic-rag-llama-stack/source_docs/FantaCoFabulousHRBenefits_clean.txt"
print(f"Downloading text file from {url}...")
response = requests.get(url)
text_content = response.text

print(f"Downloaded {len(text_content)} characters of text")

# Save the text to source_docs folder for inspection
source_docs_path = os.path.join(os.path.dirname(__file__), "source_docs", "FantaCoFabulousHRBenefits_clean.txt")
os.makedirs(os.path.dirname(source_docs_path), exist_ok=True)
with open(source_docs_path, 'w', encoding='utf-8') as f:
    f.write(text_content)
print(f"Saved text to: {source_docs_path}")

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

print(f"File {uploaded_file.id} added to vector store")

# Check file status
import time
time.sleep(2)
files = client.vector_stores.files.list(vector_store_id=vs.id)
for f in files:
    print(f"File status: {f.status}")
