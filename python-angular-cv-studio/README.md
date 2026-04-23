# Python + Angular CV Studio

This is a new project scaffold (separate from Streamlit) that recreates the same CV workflow using:

- `FastAPI` backend
- `Angular` frontend

It reuses your existing Python business logic from the root project:

- `llm_service.py`
- `cv_generator.py`
- `schema.py`

## Project layout

- `backend/` FastAPI API server
- `frontend/` Angular web app

## Backend setup

From repo root:

```powershell
cd python-angular-cv-studio\backend
..\..\.projectvenv\Scripts\python.exe -m pip install -r requirements.txt
..\..\.projectvenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

If the path spacing in your shell causes issues, use:

```powershell
cd python-angular-cv-studio\backend
& "C:\Users\197405\conversational-NTT-CV\.projectvenv\Scripts\python.exe" -m pip install -r requirements.txt
& "C:\Users\197405\conversational-NTT-CV\.projectvenv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
```

## Frontend setup

In a new terminal:

```powershell
cd python-angular-cv-studio\frontend
npm install
npm start
```

The Angular dev server runs on `http://localhost:4200` and proxies `/api` calls to `http://127.0.0.1:8000`.

## Environment

Your existing root `.env` already contains `OPENAI_API_KEY`.  
Backend imports your root `llm_service.py`, so the same key is used.
