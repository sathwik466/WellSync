# WellSync

Holistic wellness web application with four integrated modules:

| Module | Description | Tech |
|--------|-------------|------|
| **Wellness Chatbot** | Mental wellness Q&A with deep knowledge base context and chat memory | FAISS, Pinecone, MiniLM-L6-v2, Groq LLM (Llama 3.3 70B) / Ollama |
| **Yoga Pose Detection** | Real-time pose correction with visual skeleton overlay | TensorFlow.js, MoveNet SinglePose Thunder |
| **Diet Planner** | Personalized meal plans and recipes from user preferences | Flask + Groq / Llama, MySQL storage |
| **Movie Recommendations** | Mood detection from face / manual selection → visual TMDb movie posters & details | face-api.js, TMDb API, Flask |

**Stack:** React (Vite) · Flask · MySQL

---

## Project Structure

```
wellsync/
├── backend/
│   ├── app.py                  # Flask entry point
│   ├── config.py               # Environment config
│   ├── requirements.txt
│   ├── data/
│   │   ├── knowledge_base.txt  # Mental wellness KB (FAISS indexed)
│   │   └── yoga_poses.json     # Pose definitions + target angles
│   ├── models/database.py      # SQLAlchemy models
│   ├── routes/                 # API endpoints
│   └── services/               # Business logic
│       ├── embedding_service.py   # Sentence Transformers (MiniLM-L6-v2)
│       ├── faiss_service.py       # Knowledge base vector search
│       ├── pinecone_service.py    # Chat history vector store
│       ├── llm_service.py         # Groq LLM (with Ollama fallback)
│       ├── chatbot_service.py
│       ├── diet_service.py
│       └── movie_service.py
└── frontend/
    └── src/
        ├── pages/              # Chatbot, Yoga, Diet, Movies
        ├── components/         # Layout, shared UI
        └── utils/poseUtils.js  # Angle calculation + skeleton drawing
```

---

## Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- **MySQL** 8+
- **Groq API Key** (Recommended for ultra-fast, high-quality responses) — [https://console.groq.com/keys](https://console.groq.com/keys)
- **TMDb API Key** (Optional, for live dynamic movie discovery) — [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
- **Ollama** (Optional fallback for local offline LLM) — [https://ollama.ai](https://ollama.ai)
- **Pinecone account** (Optional, for chat history persistence)

---

## Setup

### 1. MySQL Database

```sql
CREATE DATABASE wellsync;
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY (from https://console.groq.com/keys) and MySQL settings
```

*(Optional)* If using local Ollama instead of Groq:

```bash
ollama pull llama3
ollama serve
# In .env set LLM_PROVIDER=ollama
```

Run the Flask server:

```bash
python app.py
```

Backend runs at `http://localhost:5000`. On first start, FAISS builds an index from `data/knowledge_base.txt`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000` with API proxy to Flask.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chatbot/chat` | Send chat message `{ message, session_id? }` |
| GET | `/api/yoga/poses` | List all yoga poses |
| GET | `/api/yoga/poses/:id` | Get pose details |
| POST | `/api/diet/generate` | Generate meal plan |
| GET | `/api/diet/history/:user_id` | Past diet plans |
| POST | `/api/movies/recommend` | Get movies by mood `{ mood }` |
| GET | `/api/movies/moods` | List supported moods |

---

## Architecture

### Chatbot Flow

```
User message
    → MiniLM-L6-v2 embedding
    → FAISS search (knowledge base chunks)
    → Pinecone search (previous chat in session)
    → Context + message → Llama LLM
    → Response stored in Pinecone
```

### Yoga Detection Flow

```
User selects pose → Camera ON
    → MoveNet Thunder (browser, TensorFlow.js)
    → Keypoint angles calculated
    → Compared to pose target angles
    → Visual skeleton + correction messages
```

### Diet Plan Flow

```
User preferences + ingredients + meal types
    → Llama generates JSON meal plan
    → Saved to MySQL (if user_id provided)
```

### Movie Recommendations Flow

```
Camera → face-api.js expression detection
    → Dominant mood extracted
    → Backend returns mood-matched movie list
```

---

## Environment Variables

See `backend/.env.example` for all options:

- `MYSQL_*` — Database connection
- `PINECONE_API_KEY` / `PINECONE_INDEX_NAME` — Chat history (optional)
- `LLM_API_URL` / `LLM_MODEL` — Ollama or compatible Llama endpoint
- `EMBEDDING_MODEL` — Default `all-MiniLM-L6-v2`

---

## Notes

- **Pinecone** is optional. Without it, chat works but previous conversation context is not persisted across sessions.
- **Yoga** and **Movies** require camera access and run ML models entirely in the browser.
- **Llama** responses depend on Ollama running locally. A fallback message is shown if the LLM is unavailable.
