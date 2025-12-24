import os
import logging
import sys
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client import APIConnectionError

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

logger.info("=" * 80)
logger.info("Available Models on Llama Stack Server")
logger.info("=" * 80)
logger.info(f"Server: {LLAMA_STACK_BASE_URL}")
logger.info("-" * 80)

# Initialize client
try:
    client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)
except Exception as e:
    logger.error(f"Failed to initialize client: {e}")
    sys.exit(1)

# List all models
try:
    logger.info("\nFetching available models...")
    models = client.models.list()

    model_list = list(models)

    if not model_list:
        logger.warning("No models found on the server")
        logger.info("\nYou need to register models using client.models.register()")
        sys.exit(0)

    logger.info(f"\nFound {len(model_list)} model(s):\n")

    embedding_models = []
    llm_models = []
    other_models = []

    for model in model_list:
        model_type = getattr(model, 'model_type', 'unknown')

        if model_type == 'embedding':
            embedding_models.append(model)
        elif model_type in ['llm', 'text']:
            llm_models.append(model)
        else:
            other_models.append(model)

    # Display Embedding Models
    if embedding_models:
        logger.info("🔹 EMBEDDING MODELS:")
        logger.info("-" * 80)
        for model in embedding_models:
            logger.info(f"  ID: {model.identifier}")
            if hasattr(model, 'provider_id'):
                logger.info(f"  Provider: {model.provider_id}")
            if hasattr(model, 'provider_resource_id'):
                logger.info(f"  Resource ID: {model.provider_resource_id}")
            if hasattr(model, 'metadata'):
                logger.info(f"  Metadata: {model.metadata}")
            logger.info("")

    # Display LLM Models
    if llm_models:
        logger.info("🔹 LLM MODELS:")
        logger.info("-" * 80)
        for model in llm_models:
            logger.info(f"  ID: {model.identifier}")
            if hasattr(model, 'provider_id'):
                logger.info(f"  Provider: {model.provider_id}")
            if hasattr(model, 'provider_resource_id'):
                logger.info(f"  Resource ID: {model.provider_resource_id}")
            logger.info("")

    # Display Other Models
    if other_models:
        logger.info("🔹 OTHER MODELS:")
        logger.info("-" * 80)
        for model in other_models:
            logger.info(f"  ID: {model.identifier}")
            logger.info(f"  Type: {model.model_type}")
            if hasattr(model, 'provider_id'):
                logger.info(f"  Provider: {model.provider_id}")
            logger.info("")

    logger.info("=" * 80)

    # Recommendations
    if not embedding_models:
        logger.warning("\n⚠ No embedding models found!")
        logger.info("You need an embedding model for vector stores.")
        logger.info("Run: python 0_register_embedding_model.py")

except APIConnectionError as e:
    logger.error(f"Cannot connect to server at {LLAMA_STACK_BASE_URL}")
    logger.error("Make sure the server is running")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error listing models: {e}")
    sys.exit(1)
