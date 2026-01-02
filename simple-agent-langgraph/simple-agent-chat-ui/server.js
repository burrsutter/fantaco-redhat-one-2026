const express = require('express');
const axios = require('axios');
require('dotenv').config({ path: '../.env' });

const app = express();
const CHAT_UI_PORT = process.env.CHAT_UI_PORT || 3001;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

// Middleware
app.use(express.json());
app.use(express.static('public'));

// API endpoint to proxy requests to FastAPI
app.get('/api/question', async (req, res) => {
    const { q } = req.query;

    if (!q) {
        return res.status(400).json({ error: 'Question parameter "q" is required' });
    }

    try {
        console.log(`Forwarding question to FastAPI: ${q}`);
        const response = await axios.get(`${FASTAPI_URL}/question`, {
            params: { q },
            timeout: 120000 // 120 second timeout for LLM + MCP tool calls
        });

        console.log('Received response from FastAPI');
        res.json(response.data);
    } catch (error) {
        console.error('Error calling FastAPI:', error.message);

        if (error.response) {
            res.status(error.response.status).json({
                error: error.response.data.detail || 'Error from FastAPI backend'
            });
        } else if (error.code === 'ECONNREFUSED') {
            res.status(503).json({
                error: 'Cannot connect to FastAPI backend. Is it running?'
            });
        } else {
            res.status(500).json({
                error: 'Internal server error'
            });
        }
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', fastapi_url: FASTAPI_URL });
});

app.listen(CHAT_UI_PORT, () => {
    console.log(`Chat UI server running on http://localhost:${CHAT_UI_PORT}`);
    console.log(`FastAPI backend: ${FASTAPI_URL}`);
});
