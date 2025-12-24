import os
import requests
import logging
import sys
import time
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client import APIConnectionError, APIStatusError
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

# Validate required environment variables
if not EMBEDDING_MODEL:
    logger.error("EMBEDDING_MODEL not set in .env file")
    sys.exit(1)

if not EMBEDDING_DIMENSION:
    logger.error("EMBEDDING_DIMENSION not set in .env file")
    sys.exit(1)

try:
    EMBEDDING_DIMENSION = int(EMBEDDING_DIMENSION)
except ValueError:
    logger.error(f"EMBEDDING_DIMENSION must be a number, got: {EMBEDDING_DIMENSION}")
    sys.exit(1)

logger.info(f"LLAMA_STACK_BASE_URL: {LLAMA_STACK_BASE_URL}")
logger.info(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
logger.info(f"EMBEDDING_DIMENSION: {EMBEDDING_DIMENSION}")
logger.info("-" * 80)

# Initialize client
try:
    logger.info("Initializing Llama Stack client...")
    client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)
    logger.info("Client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize client: {e}")
    logger.error("Make sure Llama Stack server is running")
    sys.exit(1)

# Create vector store with embedding model configuration and hybrid search
try:
    logger.info("Creating vector store...")
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
    logger.info(f"✓ Vector store created: {vs.id}")
except APIConnectionError as e:
    logger.error(f"Cannot connect to Llama Stack server at {LLAMA_STACK_BASE_URL}")
    logger.error("Please ensure the server is running and accessible")
    sys.exit(1)
except APIStatusError as e:
    logger.error(f"API error creating vector store: {e.status_code} - {e.message}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error creating vector store: {e}")
    sys.exit(1)

# Download clean text file
url = "https://raw.githubusercontent.com/burrsutter/fantaco-redhat-one-2026/refs/heads/main/basic-rag-llama-stack/source_docs/FantaCoFabulousHRBenefits_clean.txt"
try:
    logger.info(f"Downloading document...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()  # Raise error for bad status codes
    text_content = response.text

    if not text_content or len(text_content) < 100:
        logger.error("Downloaded file appears to be empty or too small")
        sys.exit(1)

    logger.info(f"✓ Downloaded {len(text_content)} characters")
except requests.exceptions.Timeout:
    logger.error(f"Download timed out after 30 seconds")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    logger.error(f"Failed to connect to {url}")
    logger.error("Check your internet connection")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP error downloading file: {e.response.status_code}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error downloading file: {e}")
    sys.exit(1)

# Save the text to source_docs folder for inspection
try:
    source_docs_path = os.path.join(os.path.dirname(__file__), "source_docs", "FantaCoFabulousHRBenefits_clean.txt")
    os.makedirs(os.path.dirname(source_docs_path), exist_ok=True)
    with open(source_docs_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
    logger.info(f"✓ Saved to: {source_docs_path}")
except IOError as e:
    logger.error(f"Failed to save file: {e}")
    logger.warning("Continuing with upload (file not saved locally)")
except Exception as e:
    logger.error(f"Unexpected error saving file: {e}")
    logger.warning("Continuing with upload (file not saved locally)")

# Upload as text file
try:
    logger.info("Uploading document to Llama Stack...")
    text_buffer = BytesIO(text_content.encode('utf-8'))
    text_buffer.name = "hr-benefits-clean.txt"

    uploaded_file = client.files.create(
        file=text_buffer,
        purpose="assistants"
    )
    logger.info(f"✓ File uploaded: {uploaded_file.id}")
except APIConnectionError as e:
    logger.error("Lost connection to Llama Stack server during upload")
    sys.exit(1)
except APIStatusError as e:
    logger.error(f"API error uploading file: {e.status_code} - {e.message}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error uploading file: {e}")
    sys.exit(1)

# Attach file to vector store with custom chunking strategy
try:
    logger.info("Attaching file to vector store...")
    logger.info(f"  Chunking: 100 tokens per chunk, 10 token overlap")

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
    logger.info(f"✓ File attached to vector store")
except APIConnectionError as e:
    logger.error("Lost connection to Llama Stack server during file attachment")
    sys.exit(1)
except APIStatusError as e:
    logger.error(f"API error attaching file: {e.status_code} - {e.message}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error attaching file: {e}")
    sys.exit(1)

# Check file processing status
logger.info("-" * 80)
logger.info("Checking file processing status...")
logger.info("Waiting 10 seconds for processing to complete...")
time.sleep(10)

try:
    files = client.vector_stores.files.list(vector_store_id=vs.id)
    file_list = list(files)

    if not file_list:
        logger.warning("No files found in vector store")
        sys.exit(1)

    for f in file_list:
        logger.info(f"File ID: {f.id}")
        logger.info(f"Status: {f.status}")

        if f.status == "completed":
            logger.info("✓ File processing completed successfully!")
            logger.info("\nVector store is ready for querying")
            logger.info(f"Vector store ID: {vs.id}")
        elif f.status == "failed":
            logger.error("✗ File processing failed!")

            # Try to get detailed error information
            if hasattr(f, 'last_error') and f.last_error:
                logger.error(f"Error details: {f.last_error}")

            # Show full file object for debugging
            logger.error(f"\nFull file object: {f}")

            logger.error("\nTroubleshooting suggestions:")
            logger.error("1. Check that the embedding model is available on the server")
            logger.error("   Current model: " + EMBEDDING_MODEL)
            logger.error("2. Verify EMBEDDING_DIMENSION matches the model")
            logger.error(f"   Current dimension: {EMBEDDING_DIMENSION}")
            logger.error("3. Check server logs for detailed error messages")
            logger.error("4. Try a different embedding model in .env file")
            sys.exit(1)
        elif f.status == "in_progress":
            logger.warning("File is still processing. It may take a few more moments.")
            logger.info("Run 2_list_available_vector_stores.py later to check status")
        else:
            logger.warning(f"Unexpected file status: {f.status}")

except APIConnectionError as e:
    logger.error("Lost connection to Llama Stack server while checking status")
    logger.warning("File may still be processing - check later")
except Exception as e:
    logger.error(f"Error checking file status: {e}")
    logger.warning("File may still be processing - check manually")

logger.info("-" * 80)
