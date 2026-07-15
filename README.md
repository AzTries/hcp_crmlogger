# CRM Logger — AI-First HCP Interaction Module

An AI-first "Log Interaction Screen" for a pharma CRM's Healthcare Professional (HCP) module. Field reps can log meetings with doctors either through a structured form or a conversational AI chat interface, powered by a LangGraph agent.

## Tech Stack

- **Frontend:** React (Vite) + Redux Toolkit
- **Backend:** Python + FastAPI
- **AI Agent Framework:** LangGraph
- **LLM:** Groq — `llama-3.3-70b-versatile` (agent orchestration) and `llama-3.1-8b-instant` (extraction/summarization inside tools)
- **Database:** PostgreSQL (Neon)
- **Font:** Google Inter

### Note on model choice
The assignment specified `gemma2-9b-it`. Groq deprecated this model on August 8, 2025, in favor of `llama-3.1-8b-instant` ([source](https://console.groq.com/docs/deprecations)). We use Groq's recommended replacement for lightweight tasks, and `llama-3.3-70b-versatile` as the main agent brain, since it's significantly more reliable at knowing when to stop calling tools.

## LangGraph Agent

The agent is a single-node loop: an LLM bound to 6 tools, with a conditional edge that routes back to the LLM after every tool call until it decides to respond directly. Full conversation history is sent on every request, so the agent has memory across turns.

### Tools

1. **`log_interaction`** *(required)* — Takes an HCP name and raw free-text notes. Uses the LLM to extract structured fields (topics, sentiment, materials shared) and saves a new interaction record.
2. **`edit_interaction`** *(required)* — Updates a field on an existing interaction by ID.
3. **`detect_adverse_event`** — Scans interaction text for mentions of patient side effects or safety concerns. If detected, flags the record (`ae_flagged = true`) with a summary, for pharmacovigilance review — a real regulatory pattern in pharma CRMs.
4. **`get_interaction_history`** — Retrieves an HCP's past logged interactions, most recent first.
5. **`find_interaction`** — Searches interactions by HCP name and/or keyword. Lets the agent resolve natural references ("the pricing meeting with Dr. Sharma") into an actual ID before editing, instead of requiring the user to know raw database IDs.
6. **`suggest_followups`** — Given interaction notes, suggests 2-3 concrete next-step actions.

## Project Structure

```
crmlogger/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, router registration
│   │   ├── database.py          # Neon Postgres connection
│   │   ├── models.py            # SQLAlchemy models (HCP, Interaction)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── agent/
│   │   │   ├── graph.py         # LangGraph agent definition
│   │   │   └── tools.py         # 6 agent tools
│   │   └── routes/
│   │       ├── chat.py          # POST /api/chat
│   │       ├── interactions.py  # CRUD for interactions
│   │       └── hcps.py          # CRUD for HCPs
│   ├── requirements.txt
│   └── .env                     # DATABASE_URL, GROQ_API_KEY (not committed)
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx / App.css
│   │   ├── store/
│   │   │   ├── store.js
│   │   │   └── interactionsSlice.js
│   │   └── components/
│   │       ├── InteractionForm.jsx
│   │       └── ChatAssistant.jsx
│   └── package.json
└── README.md
```

## How to Run

### Backend

```bash
cd backend
py -3.10 -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create `backend/.env`:
```
DATABASE_URL=your_neon_postgres_connection_string
GROQ_API_KEY=your_groq_api_key
```

```bash
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`. Interactive API docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Send a message to the LangGraph agent |
| GET | `/api/interactions` | List the 8 most recent interactions |
| GET | `/api/interactions/{id}` | Get a single interaction |
| POST | `/api/interactions` | Create an interaction (structured form) |
| PUT | `/api/interactions/{id}` | Update an interaction |
| DELETE | `/api/interactions/{id}` | Delete an interaction |
| GET | `/api/hcps` | List all HCPs |
| POST | `/api/hcps` | Create an HCP |

## Known Limitations

- No authentication — out of scope for this assignment.
- Interaction list is capped at the 8 most recent records for the demo UI (no pagination yet).
- The AI's conversational summaries occasionally paraphrase details loosely (e.g. ordering) even when the underlying tool data is correct; the database and card view are always the source of truth.
