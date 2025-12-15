#!/bin/bash

# Get detailed information about the builtin::rag tools
echo "=== RAG Tools Overview ==="
echo ""

# List all RAG tools (there are multiple tools in the builtin::rag toolgroup)
curl -sS -H "Content-Type: application/json" \
  "http://localhost:8321/v1/tool-runtime/list-tools" | jq '.data[] | select(.toolgroup_id == "builtin::rag")'

echo ""
echo "=== Knowledge Search Tool (detailed) ==="
echo ""

# Get details for knowledge_search tool
curl -sS -H "Content-Type: application/json" \
  "http://localhost:8321/v1/tool-runtime/list-tools" | \
  jq '.data[] | select(.toolgroup_id == "builtin::rag" and .name == "knowledge_search")'

echo ""
echo "=== Insert Into Memory Tool (detailed) ==="
echo ""

# Get details for insert_into_memory tool
curl -sS -H "Content-Type: application/json" \
  "http://localhost:8321/v1/tool-runtime/list-tools" | \
  jq '.data[] | select(.toolgroup_id == "builtin::rag" and .name == "insert_into_memory")'

echo ""
echo "=== Summary ==="
echo ""
echo "The builtin::rag toolgroup contains 2 tools:"
echo "1. knowledge_search - Search for information in a database"
echo "   - Required parameter: query (string)"
echo ""
echo "2. insert_into_memory - Insert documents into memory"
echo "   - No input schema defined (null)"
