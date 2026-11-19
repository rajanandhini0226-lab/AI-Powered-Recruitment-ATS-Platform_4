# 🎯 AI-Powered Recruitment & ATS Platform

Applicant Tracking System with NLP-based resume parsing, candidate ranking, hiring pipeline and interview scheduling.

**Stack:** React (Vite) · Python · FastAPI · PostgreSQL · scikit-learn (TF-IDF / cosine similarity)

## Features
| Feature | Implementation |
|---|---|
| Resume parsing & ranking | PDF/DOCX/TXT → text → name, email, phone, skills, years of experience (`backend/app/nlp.py`) |
| Skill matching with job description | Match score = 65% skill overlap + 35% TF-IDF cosine similarity; shows matched & missing skills |
| Hiring pipeline visualization | Drag-and-drop Kanban (Applied → Screening → Interview → Offer → Hired / Rejected) |
| Interview scheduling | Schedule/cancel interviews with interviewer double-booking (conflict) detection |
| Dashboard stats | Jobs, applications, average score, hires |

## Run with Docker
```bash
docker compose up --build
```
Frontend: http://localhost:5173 · API docs (Swagger): http://localhost:8000/docs

## Run locally (no Docker)
```bash
# backend (uses SQLite unless DATABASE_URL is set)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload
# PostgreSQL: export DATABASE_URL=postgresql://user:pass@localhost:5432/ats

# frontend
cd frontend && npm install && npm run dev
```
Try it: create a job → upload files from `sample-data/` → view ranking → drag cards in Pipeline → schedule an interview.

## API summary
`POST /jobs` · `GET /jobs` · `POST /jobs/{id}/apply` (multipart file) · `GET /jobs/{id}/ranking` · `GET /jobs/{id}/pipeline` ·
`PATCH /applications/{id}/stage` · `POST /interviews` · `GET /interviews` · `GET /stats`

## Future improvements
JWT auth + roles, spaCy NER / embedding models, email invitations, calendar sync.
