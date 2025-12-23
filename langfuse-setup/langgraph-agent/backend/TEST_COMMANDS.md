# FastAPI Test Commands

This document contains test commands for the LangGraph + Langfuse FastAPI server (`6-langgraph-langfuse-fastapi.py`).

## Prerequisites

1. **Start the MCP Servers** (Customer & Finance)
2. **Set up environment variables** in `.env` file
3. **Start Langfuse** (if running locally at http://localhost:3000)

## Start the FastAPI Server

```bash
cd backend
python 6-langgraph-langfuse-fastapi.py
```

The server will start on `http://localhost:8002` (or the port specified in your `.env` file).

---

## API Endpoints

### 1. Health Check

Check if the server is running and MCP clients are connected:

```bash
curl -s http://localhost:8002/health | python -m json.tool
```

**Expected Response:**
```json
{
    "status": "healthy",
    "mcp_clients": ["customer", "finance"],
    "tools_count": 4
}
```

---

### 2. Root Endpoint (API Info)

Get information about the API and available tools:

```bash
curl -s http://localhost:8002/ | python -m json.tool
```

**Expected Response:**
```json
{
    "message": "LangGraph MCP Customer Service API",
    "version": "1.0.0",
    "status": "running",
    "available_tools": [
        "search_customers",
        "get_customer",
        "fetch_order_history",
        "fetch_invoice_history"
    ]
}
```

---

### 3. Chat Endpoint - Simple Customer Query

Ask about a specific customer:

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who is Thomas Hardy?",
    "session_id": "test-session-123",
    "user_id": "test-user"
  }'
```

**Pretty Print Response:**
```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who is Thomas Hardy?",
    "session_id": "test-session-123",
    "user_id": "test-user"
  }' | python -m json.tool
```

---

### 4. Chat Endpoint - Customer with Orders

Get customer information and their orders:

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What are the orders for Thomas Hardy?\", \"session_id\": \"session-456\", \"user_id\": \"admin\"}"
```

**Alternative with single quotes (easier):**
```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the orders for Thomas Hardy?", "session_id": "session-456"}' \
  | python -m json.tool
```

---

### 5. Chat Endpoint - Search by Company Name

Find orders for a specific company:

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find orders for Lonesome Pine Restaurant", "session_id": "demo-session"}' \
  | python -m json.tool
```

---

### 6. Chat Endpoint - Complex Query

Ask about multiple aspects (customer details + order history):

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Thomas Hardy and his complete order history", "session_id": "complex-query-1", "user_id": "analyst"}' \
  | python -m json.tool
```

---

### 7. Chat Endpoint - Search by Email

Search for a customer by email address:

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find the customer with email thomashardy@example.com", "session_id": "email-search"}' \
  | python -m json.tool
```

---

### 8. Chat Endpoint - Without Optional Fields

Test with only the required `message` field:

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is Thomas Hardy?"}' \
  | python -m json.tool
```

---

## Response Format

All successful chat responses follow this format:

```json
{
  "reply": "The AI-generated response text...",
  "tool_result": null,
  "trace_id": "019b4ccc-fa59-7fa2-a56e-854d0fafbfda"
}
```

**Fields:**
- `reply` (string): The AI assistant's response
- `tool_result` (any): Reserved for future use (currently null)
- `trace_id` (string): Langfuse trace ID for observability

---

## View Traces in Langfuse

After making a request, you can view the full trace in Langfuse using the `trace_id` from the response:

```
http://localhost:3000/trace/{trace_id}
```

For example:
```
http://localhost:3000/trace/019b4ccc-fa59-7fa2-a56e-854d0fafbfda
```

---

## Testing with Different Sessions

To test session tracking in Langfuse, use different `session_id` values:

**Session 1:**
```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is Thomas Hardy?", "session_id": "morning-session"}' \
  | python -m json.tool
```

**Session 2:**
```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find Lonesome Pine orders", "session_id": "afternoon-session"}' \
  | python -m json.tool
```

You'll see these as separate sessions in the Langfuse dashboard.

---

## Testing with Different Users

Test user tracking by providing different `user_id` values:

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What orders does AROUT have?", "user_id": "sales-manager", "session_id": "sales-1"}' \
  | python -m json.tool
```

---

## Error Handling Test

Test the API with an invalid request:

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"invalid": "field"}' \
  | python -m json.tool
```

**Expected Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required",
      "input": {"invalid": "field"}
    }
  ]
}
```

---

## Batch Testing Script

Create a simple bash script to test multiple scenarios:

```bash
#!/bin/bash

echo "=== Health Check ==="
curl -s http://localhost:8002/health | python -m json.tool

echo -e "\n=== Test 1: Thomas Hardy ==="
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is Thomas Hardy?", "session_id": "batch-1"}' \
  | python -m json.tool | grep -A1 "reply"

echo -e "\n=== Test 2: Orders ==="
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What orders does Thomas Hardy have?", "session_id": "batch-2"}' \
  | python -m json.tool | grep -A1 "reply"

echo -e "\n=== Test 3: Company Search ==="
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find Lonesome Pine Restaurant", "session_id": "batch-3"}' \
  | python -m json.tool | grep -A1 "reply"

echo -e "\nDone!"
```

Save as `test_api.sh`, make executable with `chmod +x test_api.sh`, and run with `./test_api.sh`.

---

## Notes

1. **Port**: Default port is 8002. Change via `PORT` environment variable.
2. **MCP Servers**: Must be running before starting FastAPI server.
3. **Langfuse**: Traces are sent to the URL specified in `LANGFUSE_BASE_URL`.
4. **Session Tracking**: Use consistent `session_id` for conversation continuity in Langfuse.
5. **User Tracking**: The `user_id` field helps track usage per user in Langfuse analytics.
