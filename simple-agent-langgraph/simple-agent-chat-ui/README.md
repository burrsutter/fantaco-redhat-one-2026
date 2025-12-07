# Simple Agent Chat UI

A modern chat interface for the LangGraph FastAPI backend that enables natural language conversations with an AI assistant that can access customer, order, and invoice data.

## Features

- Clean, modern chat interface
- Real-time messaging with typing indicators
- Connects to LangGraph FastAPI backend
- Handles customer queries, orders, and invoices
- Error handling and user feedback

## Prerequisites

- Node.js (v14 or higher)
- FastAPI backend running (from `9_langgraph_fastapi.py`)

## Installation

1. Navigate to the project directory:
```bash
cd simple-agent-chat-ui
```

2. Install dependencies:
```bash
npm install
```

## Configuration

The app uses environment variables for configuration:

- `CHAT_UI_PORT` - Port for the chat UI server (default: 3000)
- `FASTAPI_URL` - URL of the FastAPI backend (default: http://localhost:8000)

You can set these in a `.env` file or export them:

```bash
export CHAT_UI_PORT=3000
export FASTAPI_URL=http://localhost:8000
```

## Running the Application

1. Start the FastAPI backend first:
```bash
cd ..
python 9_langgraph_fastapi.py
```

2. In a new terminal, start the chat UI:
```bash
cd simple-agent-chat-ui
npm start
```

For development with auto-reload:
```bash
npm run dev
```

3. Open your browser to:
```
http://localhost:3000
```

## Screenshot

![LangGraph Chat Assistant](chat-ui-1.png)

## Usage

Simply type questions in the chat interface:

- "Find all orders for thomashardy@example.com"
- "What invoices does customer ABC123 have?"
- "Show me customer information for maria@company.com"
- "What is the status of order 12345?"

The AI assistant will process your questions and return relevant information from the connected MCP servers.

## Project Structure

```
simple-agent-chat-ui/
├── package.json          # Dependencies and scripts
├── server.js             # Express server
├── public/
│   ├── index.html        # Main HTML page
│   ├── styles.css        # Styling
│   └── app.js           # Client-side JavaScript
└── README.md            # This file
```

## API Endpoints

### GET /api/question
Proxies questions to the FastAPI backend.

**Query Parameters:**
- `q` - The question to ask

**Example:**
```bash
curl "http://localhost:3000/api/question?q=what%20is%20the%20weather"
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "fastapi_url": "http://localhost:8000"
}
```

## Troubleshooting

### "Cannot connect to FastAPI backend"
- Ensure the FastAPI server is running on port 8000 (or configured port)
- Check that `FASTAPI_URL` is set correctly

### Port already in use
- Change the port: `CHAT_UI_PORT=3001 npm start`

### No response from chatbot
- Check FastAPI server logs for errors
- Verify MCP servers are running and accessible
- Check browser console for errors
