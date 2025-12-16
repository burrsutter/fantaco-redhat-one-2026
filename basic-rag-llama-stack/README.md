# Llama Stack RAG (Retrieval-Augmented Generation)

This project demonstrates how to use the built-in RAG capabilities of Llama Stack to create a question-answering system over custom documents.

## How RAG Works in Llama Stack

Llama Stack provides native RAG support through its **Agent API** with the `file_search` tool:

1. **Vector Store Creation**: Documents are uploaded and chunked into smaller pieces
2. **Embedding Generation**: Each chunk is converted to a vector embedding using an embedding model
3. **Vector Search**: When a query is made, it's embedded and compared against stored chunks using:
   - **Semantic search**: Vector similarity (cosine/dot product)
   - **Keyword search**: BM25 algorithm
   - **Hybrid search**: Combination of both (configurable weights)
4. **Retrieval**: Top matching chunks are retrieved based on relevance scores
5. **Generation**: The LLM uses retrieved context to generate answers, citing sources

### Architecture

```
User Query → Embedding → Vector Search → Top K Chunks → LLM + Context → Answer
                              ↓
                        Vector Store
                     (Embeddings + Metadata)
```

## Prerequisites

- Llama Stack server running (default: `http://localhost:8321`)
- Python 3.12+ with required packages:
  ```bash
  pip install llama-stack-client python-dotenv requests
  ```

## Environment Variables

Set these before running scripts:

```bash
export LLAMA_STACK_BASE_URL=http://localhost:8321
export INFERENCE_MODEL=ollama/qwen3:14b-q8_0
export VECTOR_STORE_ID=vs_your-vector-store-id  # Optional, for specific scripts
```

## Scripts Overview

### 1. Vector Store Management

#### `1_create_vector_store.py`
Creates a vector store with hybrid search capabilities.

**What it does:**
- Downloads HTML document from remote URL
- Strips HTML/CSS tags, preserves text structure
- Creates vector store with hybrid search (BM25 + semantic)
- Uploads and chunks document (100 tokens per chunk, 10 token overlap)
- Saves clean text to `source_docs/` for inspection

**Usage:**
```bash
python 1_create_vector_store.py
```

**Output:**
- Vector store ID
- File processing status
- Clean text saved to `source_docs/FantaCoFabulousHRBenefits_clean.txt`

---

#### `2_list_available_vector_stores.py`
Lists all vector stores with their files.

**Usage:**
```bash
python 2_list_available_vector_stores.py
```

**Output:**
```
Available Vector Stores:
--------------------------------------------------------------------------------
ID: vs_5082c71d-f1a2-421d-a453-392afab67462
Name: hr-benefits-hybrid
Created: 1765837795
Files: 1
```

---

#### `2_list_available_vector_stores.sh`
Shell script alternative using curl and jq.

**Usage:**
```bash
./2_list_available_vector_stores.sh
```

**Output:**
```
hr-benefits-hybrid vs_5082c71d-f1a2-421d-a453-392afab67462
```

---

#### `7_delete_vector_store.py`
Interactive script to safely delete vector stores.

**Features:**
- Lists all vector stores
- Multiple deletion options:
  1. Delete all
  2. Delete by name pattern
  3. Delete specific store by number
  4. Cancel
- Requires confirmation before deletion

**Usage:**
```bash
python 7_delete_vector_store.py
```

---

### 2. RAG Query Scripts

#### `3_test_rag_hr_benefits.py`
Main RAG test script - asks about retirement benefits.

**Query:** "What do I receive when I retire?"

**Usage:**
```bash
export LLAMA_STACK_BASE_URL=http://localhost:8321
export INFERENCE_MODEL=ollama/qwen3:14b-q8_0
python 3_test_rag_hr_benefits.py
```

**Features:**
- Uses Llama Stack Agent API
- Automatically finds latest `hr-benefits-hybrid` vector store
- Streams response with full verbose output (thinking, tool calls, answer)

---

#### `5_test_gold_watch.py`
Tests retrieval with specific query about gold watch retirement benefit.

**Query:** "When do I get my gold watch?"

**Usage:**
```bash
python 5_test_gold_watch.py
```

---

#### `6_test_unique_terms.py`
Tests retrieval quality with multiple unique terms from the document.

**Queries:**
- "Tell me about the chocolate statue and personal bard"
- "What do I get instead of a gold watch when I retire"
- "Tell me about the 401k and astrological alignment"

**Usage:**
```bash
python 6_test_unique_terms.py
```

**Purpose:** Validates that vector search finds the correct detailed section, not just brief mentions.

---

### 3. Debug and Testing

#### `4_debug_vector_search.py`
Debug tool to inspect raw vector search results.

**What it does:**
- Tests direct vector store search API (not through Agent)
- Shows top-K chunks for various queries
- Displays relevance scores and content snippets
- Validates retrieval quality

**Usage:**
```bash
python 4_debug_vector_search.py
```

**Output:**
```
Query: 'gold watch retirement'
--------------------------------------------------------------------------------
Found 6 results

  Result 1:
    Score: 0.002515042051429417
    Content: ...instead of a gold watch, you receive a life-sized statue...
```

---

## Common Workflows

### Complete Setup and Test

```bash
# 1. Set environment variables
export LLAMA_STACK_BASE_URL=http://localhost:8321
export INFERENCE_MODEL=ollama/qwen3:14b-q8_0

# 2. Create vector store with documents
python 1_create_vector_store.py

# 3. List vector stores (copy the ID)
python 2_list_available_vector_stores.py

# 4. Test RAG queries
python 3_test_rag_hr_benefits.py

# 5. Debug if results aren't good
python 4_debug_vector_search.py
```

### Clean Up Old Vector Stores

```bash
python 7_delete_vector_store.py
# Choose option 2: Delete by name pattern
# Enter: "hr-benefits"
# Confirm: yes
```

## Configuration Details

### Vector Store Settings

From `1_create_vector_store.py`:

```python
# Hybrid search configuration
extra_body={
    "embedding_model": "sentence-transformers/nomic-ai/nomic-embed-text-v1.5",
    "embedding_dimension": 768,
    "search_mode": "hybrid",  # Keyword + semantic
    "bm25_weight": 0.5,       # Weight for keyword search
    "semantic_weight": 0.5,   # Weight for semantic search
}

# Chunking strategy
chunking_strategy={
    "type": "static",
    "static": {
        "max_chunk_size_tokens": 100,
        "chunk_overlap_tokens": 10
    }
}
```

### Agent Configuration

```python
agent = Agent(
    client,
    model=INFERENCE_MODEL,
    instructions="Answer questions based on the provided documents.",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store_id]
    }],
)
```

## Document Processing

The HTML text extraction process:

1. **Download**: Fetches HTML from remote URL
2. **Parse**: Uses `HTMLParser` to extract text
3. **Clean**:
   - Skips `<style>` and `<script>` tags
   - Adds newlines after block elements (`<p>`, `<div>`, `<h1>`, etc.)
   - Cleans whitespace while preserving words
4. **Save**: Stores clean text to `source_docs/` for inspection
5. **Upload**: Sends to Llama Stack for chunking and embedding

## Troubleshooting

### No results from RAG queries

1. Check vector store exists:
   ```bash
   python 2_list_available_vector_stores.py
   ```

2. Verify file processing completed:
   - Look for `File status: completed` in creation output

3. Debug retrieval:
   ```bash
   python 4_debug_vector_search.py
   ```
   - Check if relevant chunks are being retrieved
   - Examine relevance scores

### Connection errors

Ensure Llama Stack server is running:
```bash
curl http://localhost:8321/v1/models
```

### Poor retrieval quality

- Adjust chunk size (currently 100 tokens)
- Tune hybrid search weights (bm25_weight vs semantic_weight)
- Try different queries with more specific keywords
- Check `source_docs/FantaCoFabulousHRBenefits_clean.txt` to verify text extraction

## Source Documents

Clean extracted documents are saved in:
```
source_docs/
└── FantaCoFabulousHRBenefits_clean.txt
```

You can inspect this file to verify proper text extraction and understand what content the RAG system has access to.

## Advanced: LangGraph Integration

`7_langgraph_rag_client.py` demonstrates integrating Llama Stack RAG with LangGraph for building agentic workflows. See that file for details.

## References

- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
- [Llama Stack Client Python SDK](https://github.com/meta-llama/llama-stack-client-python)
- Original source: `https://raw.githubusercontent.com/burrsutter/fantaco-redhat-one-2026/main/naive-rag-llama-stack/source_docs/FantaCoFabulousHRBenefits.html`
