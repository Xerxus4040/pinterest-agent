const express = require('express');
const app = express();

app.use(express.json());

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
// Gemini 3.5 Flash Endpoint
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent";

const USER_TENANTS = {};

// Root Path Domain Dashboard
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pinterest AI Agent - Gemini Tester</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; margin: 0; }
            .card { width: 100%; max-width: 500px; background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-top: 40px; }
            h2 { color: #38bdf8; margin-top: 0; font-size: 20px; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; background: #22c55e22; color: #4ade80; font-size: 11px; font-weight: bold; margin-bottom: 12px; }
            #chat-box { background: #0f172a; height: 220px; padding: 10px; border-radius: 8px; overflow-y: auto; margin-bottom: 12px; font-size: 13px; border: 1px solid #334155; }
            .msg { margin-bottom: 8px; line-height: 1.4; }
            .user { color: #38bdf8; font-weight: bold; }
            .ai { color: #f43f5e; font-weight: bold; }
            .input-group { display: flex; gap: 8px; }
            input { flex: 1; padding: 10px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px; outline: none; }
            button { background: #e60023; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: bold; }
            button:hover { background: #ad081b; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Pinterest AI Agent Hub 🚀</h2>
            <div class="badge">● Gemini 3.5 Flash Active</div>
            <div id="chat-box"><div class="msg"><span class="ai">Agent:</span> Send a query to test your Gemini API Key status directly!</div></div>
            <div class="input-group">
                <input type="text" id="userInput" placeholder="Test Gemini 3.5 Flash..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const chatBox = document.getElementById('chat-box');
                const msg = input.value.trim();
                if (!msg) return;

                chatBox.innerHTML += \`<div class="msg"><span class="user">You:</span> \${msg}</div>\`;
                input.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;
                chatBox.innerHTML += \`<div class="msg" id="loading"><span class="ai">Agent:</span> Thinking...</div>\`;

                try {
                    const res = await fetch('/api/test_chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: msg })
                    });
                    const data = await res.json();
                    document.getElementById('loading').remove();

                    if (data.status === 'success') {
                        chatBox.innerHTML += \`<div class="msg"><span class="ai">Gemini 3.5:</span> \${data.response}</div>\`;
                    } else {
                        chatBox.innerHTML += \`<div class="msg" style="color:#f87171;"><span class="ai">Error:</span> \${data.message}</div>\`;
                    }
                } catch(e) {
                    document.getElementById('loading').remove();
                    chatBox.innerHTML += \`<div class="msg" style="color:#f87171;"><span class="ai">Error:</span> Server Communication Failed</div>\`;
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
  `);
});

// Interactive Gemini 3.5 Flash Test Endpoint
app.post('/api/test_chat', async (req, res) => {
  const prompt = req.body.prompt || 'Hello';
  if (!GEMINI_API_KEY) {
    return res.json({ status: 'error', message: 'GEMINI_API_KEY is missing in Vercel settings.' });
  }

  try {
    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
    });
    const data = await response.json();
    if (data.candidates && data.candidates[0]) {
      res.json({ status: 'success', response: data.candidates[0].content.parts[0].text });
    } else {
      res.json({ status: 'error', message: data.error ? data.error.message : JSON.stringify(data) });
    }
  } catch (err) {
    res.json({ status: 'error', message: err.message });
  }
});

// Extension Session Save Endpoint
app.post('/api/save_session', (req, res) => {
  const { gdrive_url, pinterest_sess } = req.body;
  if (!gdrive_url || !pinterest_sess) {
    return res.status(400).json({ status: 'error', message: 'Missing fields.' });
  }
  USER_TENANTS['user_main'] = { gdrive_url, pinterest_sess };
  res.json({ status: 'success', message: 'Synced successfully!' });
});

module.exports = app;
