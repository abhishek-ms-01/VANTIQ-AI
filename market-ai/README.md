# MARKET AI

A personal real-time market analysis and trade setup application.

## Structure
- `frontend/`: React Vite application
- `backend/`: FastAPI Python application

## Getting Started

### Backend
1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate` (or `.\venv\Scripts\Activate.ps1` on Windows)
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys
6. `uvicorn main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
