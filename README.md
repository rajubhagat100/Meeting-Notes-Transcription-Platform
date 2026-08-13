# Meeting Notes & Transcription Platform (Fireflies.ai Clone)

A highly polished, premium, fullstack clone of the Fireflies.ai workspace built as an SDE Fullstack Assignment. It features a responsive Next.js frontend, a Python FastAPI backend, and a SQLite database.

## Live Deployments

- **Frontend (Vercel)**: [https://meeting-notes-transcription-platform-iota.vercel.app/](https://meeting-notes-transcription-platform-iota.vercel.app/)
- **Backend API (Render)**: [https://meeting-notes-transcription-platform-zgvd.onrender.com/](https://meeting-notes-transcription-platform-zgvd.onrender.com/)
  - Swagger Documentation: [https://meeting-notes-transcription-platform-zgvd.onrender.com/docs](https://meeting-notes-transcription-platform-zgvd.onrender.com/docs)
  - API Health Status: [https://meeting-notes-transcription-platform-zgvd.onrender.com/api/health](https://meeting-notes-transcription-platform-zgvd.onrender.com/api/health)

## Architecture & Features at a Glance

```
┌────────────────────────────────┐
│      Next.js Client (3000)     │
└──────────────┬─────────────────┘
               │ HTTP REST
               ▼
┌────────────────────────────────┐
│      FastAPI Server (8000)     │
└──────────────┬─────────────────┘
               │ SQLAlchemy ORM
               ▼
┌────────────────────────────────┐
│      SQLite DB (meetings.db)   │
└────────────────────────────────┘
```

1. **Meetings Library (Dashboard)**: Responsive dashboard showing cards for past meetings, searchable by keyword/participants, filterable by topics/participants, and sortable by recency.
2. **Interactive Transcript**: Side-by-side split screen in the detail view. Clicking a sentence seeks the player timeline, and playing the video highlights active sentences dynamically. Supports text search with real-time match highlighting.
3. **AI Notes**: Generates summary overview, structured outline/chapters (clicking a chapter seeks the player timeline), and action items.
4. **Task Management (CRUD)**: Mark action items completed, delete items, or add new ones manually.
5. **Ask AI Chatbot**: Context-aware chatbot letting users ask questions about the transcript. Answers are generated using Gemini if an API key is available, falling back to keyword search.
6. **Comments & Highlighting**: Highlight/star specific segments or add nested inline comments on transcript sentences.
7. **Document Exporters**: Export meeting details, summaries, action items, and transcripts as Plain Text (`.txt`), Markdown (`.md`), or custom-styled PDF (`.pdf`).

---

## Technical Stack

- **Frontend**: Next.js 15 (TypeScript, App Router, React 19)
- **Styling**: Custom CSS variables, glassmorphic themes (dark mode default, toggleable to light mode)
- **Backend**: Python 3 (FastAPI)
- **Database**: SQLite (SQLAlchemy ORM)
- **AI Services**: Optional integration with Gemini API (via HTTP requests)

---

## Database Schema Design

The SQLite database contains 6 interconnected tables:

1. **`meetings`**:
   - `id` (INTEGER, Primary Key)
   - `title` (VARCHAR)
   - `date` (VARCHAR, ISO string)
   - `duration_seconds` (INTEGER)
   - `participants` (TEXT, serialized JSON list of strings)
   - `video_url` (VARCHAR, path/URL)
   - `created_at` (DATETIME)

2. **`transcript_segments`**:
   - `id` (INTEGER, Primary Key)
   - `meeting_id` (INTEGER, Foreign Key -> `meetings.id` with CASCADE delete)
   - `speaker` (VARCHAR)
   - `start_time` (FLOAT)
   - `end_time` (FLOAT)
   - `text` (TEXT)
   - `highlighted` (BOOLEAN, default False)

3. **`comments`**:
   - `id` (INTEGER, Primary Key)
   - `segment_id` (INTEGER, Foreign Key -> `transcript_segments.id` with CASCADE delete)
   - `author` (VARCHAR)
   - `text` (TEXT)
   - `created_at` (DATETIME)

4. **`summaries`**:
   - `id` (INTEGER, Primary Key)
   - `meeting_id` (INTEGER, Foreign Key -> `meetings.id` with CASCADE delete, UNIQUE)
   - `overview` (TEXT)
   - `chapters` (TEXT, serialized JSON list of outlines: `[{"title", "summary", "start_time", "end_time"}]`)
   - `key_topics` (TEXT, serialized JSON list of topic strings)

5. **`action_items`**:
   - `id` (INTEGER, Primary Key)
   - `meeting_id` (INTEGER, Foreign Key -> `meetings.id` with CASCADE delete)
   - `text` (TEXT)
   - `completed` (BOOLEAN, default False)
   - `assignee` (VARCHAR, nullable)

6. **`chat_messages`**:
   - `id` (INTEGER, Primary Key)
   - `meeting_id` (INTEGER, Foreign Key -> `meetings.id` with CASCADE delete)
   - `sender` (VARCHAR, 'user' or 'ai')
   - `message` (TEXT)
   - `created_at` (DATETIME)

---

## Setup & Installation

### 1. Backend Setup (FastAPI)

1. Navigate to the `backend` folder:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```
4. (Optional) Configure Gemini API Key:
   Create a `.env` file or export the environment variable:
   ```powershell
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_api_key_here"
   # Linux/macOS
   export GEMINI_API_KEY="your_api_key_here"
   ```
5. Seed the database with high-quality mock data:
   ```powershell
   python seed.py
   ```
6. Run the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   The API will be available at `http://127.0.0.1:8000`. Swagger API docs will be at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup (Next.js)

1. Navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```
2. Install npm dependencies:
   ```powershell
   npm install
   ```
3. Run the development server:
   ```powershell
   npm run dev
   ```
   Open `http://localhost:3000` in your web browser.

---

## Core Workflows & Logic

### 1. Time-Seeking Sync
- **Transcript to Player**: Clicking a segment calls a handler triggering `mediaPlayer.currentTime = start_time`.
- **Player to Transcript**: The HTML5 player fires `onTimeUpdate`, which sets the current time state. The UI finds the segment where `currentTime` falls between `start_time` and `end_time` and dynamically attaches the `.active` class to highlight it.

### 2. Interactive Search
- On search, the client filters transcript items matching keywords using regular expressions, dynamically wrapping matching text segments in `<span class="highlight-match">` tags.

### 3. File upload & parsing
- The API accepts file uploads (e.g. `.vtt` WebVTT files or simple `.txt` formats).
- Standard voice cues (`<v SpeakerName>text</v>`) or timestamps (`[00:10] Speaker: text` / `Speaker: text`) are automatically parsed into segments.

---

## Assumptions & Mocking

- **Authentication**: Authentication is mocked to assume a default logged-in user (`Raju Bhagat`, SDE Fullstack role) for actions like commenting.
- **Audio/Video Media**: Since speech-to-text is out of scope, uploading a transcript generates mock media timelines backed by standard placeholder assets (e.g. Big Buck Bunny MP4 clip) or custom-seeded timelines.
- **LLM Summary**: If `GEMINI_API_KEY` is not present, a custom programmatic parser extracts action items (using keywords like *should*, *todo*, *need to*) and creates structured chapters dynamically.

---

## Roadmap & Planned Features (Coming Soon)

We plan to expand this Fireflies.ai clone with the following next-level features:
- **Real-Time Video Conferencing Bot**: Integration of an automated bot that joins Zoom, Google Meet, and Microsoft Teams calls via calendar invites, recording and transcribing meetings live.
- **Advanced Speaker Analytics Dashboard**: Interactive graphs illustrating speaker talk-time ratios, speaking speeds (words-per-minute), and real-time sentiment analysis of each segment.
- **Slack & Microsoft Teams Notifications**: Auto-post meeting overview summaries and lists of action items directly to corresponding project channels on communication platforms.
- **Enterprise Collaborative Workspaces**: Multi-tenant spaces with team administration roles, file-sharing links, and project permissions.
- **Multilingual Support**: Real-time translation of transcripts and AI summaries across 40+ languages (e.g. Spanish, German, French, Hindi).
- **Soundbites & Clips Generator**: Ability to highlight a transcript section and extract/share an audio-visual snippet with team members immediately.
- **Two-way CRM Integration**: Push action items directly to Jira, Salesforce, HubSpot, and Asana.
