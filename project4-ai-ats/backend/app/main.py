from datetime import timedelta
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, nlp
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI Recruitment & ATS Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def app_out(a: models.Application):
    c = a.candidate
    return {"id": a.id, "job_id": a.job_id, "stage": a.stage, "score": a.score, "skill_score": a.skill_score,
            "text_score": a.text_score, "matched_skills": a.matched_skills, "missing_skills": a.missing_skills,
            "candidate": {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
                          "skills": c.skills, "experience_years": c.experience_years}}

# ---------- Jobs ----------
@app.post("/jobs")
def create_job(j: schemas.JobIn, db: Session = Depends(get_db)):
    skills = [s.strip().lower() for s in j.required_skills if s.strip()] or nlp.extract_skills(j.description)
    job = models.Job(title=j.title, description=j.description, required_skills=skills)
    db.add(job); db.commit(); db.refresh(job)
    return {"id": job.id, "title": job.title, "required_skills": job.required_skills}

@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    return [{"id": j.id, "title": j.title, "description": j.description, "required_skills": j.required_skills,
             "applicants": len(j.applications)} for j in db.query(models.Job).order_by(models.Job.id.desc())]

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    db.delete(job); db.commit(); return {"ok": True}

# ---------- Resume upload, parsing & scoring ----------
@app.post("/jobs/{job_id}/apply")
async def apply(job_id: int, file: UploadFile = File(...), name: str = Form(None), db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    text = nlp.extract_text(file.filename, await file.read())
    if not text.strip(): raise HTTPException(400, "Could not read any text from the resume")
    p = nlp.parse_resume(text)
    cand = models.Candidate(name=name or p["name"], email=p["email"], phone=p["phone"], resume_text=text,
                            skills=p["skills"], experience_years=p["experience_years"])
    db.add(cand); db.flush()
    total, sk, tx, matched, missing = nlp.score_candidate(job.description, job.required_skills, text, p["skills"])
    a = models.Application(job_id=job.id, candidate_id=cand.id, score=total, skill_score=sk, text_score=tx,
                           matched_skills=matched, missing_skills=missing)
    db.add(a); db.commit(); db.refresh(a)
    return app_out(a)

@app.get("/jobs/{job_id}/ranking")
def ranking(job_id: int, db: Session = Depends(get_db)):
    apps = db.query(models.Application).filter_by(job_id=job_id).order_by(models.Application.score.desc()).all()
    return [app_out(a) for a in apps]

@app.get("/jobs/{job_id}/pipeline")
def pipeline(job_id: int, db: Session = Depends(get_db)):
    out = {s: [] for s in models.STAGES}
    for a in db.query(models.Application).filter_by(job_id=job_id).order_by(models.Application.score.desc()):
        out[a.stage].append(app_out(a))
    return out

@app.patch("/applications/{app_id}/stage")
def set_stage(app_id: int, body: schemas.StageIn, db: Session = Depends(get_db)):
    if body.stage not in models.STAGES: raise HTTPException(400, f"Stage must be one of {models.STAGES}")
    a = db.get(models.Application, app_id)
    if not a: raise HTTPException(404, "Application not found")
    a.stage = body.stage; db.commit(); return app_out(a)

# ---------- Interview scheduling (with conflict detection) ----------
@app.post("/interviews")
def schedule(i: schemas.InterviewIn, db: Session = Depends(get_db)):
    a = db.get(models.Application, i.application_id)
    if not a: raise HTTPException(404, "Application not found")
    end = i.scheduled_at + timedelta(minutes=i.duration_min)
    for ex in db.query(models.Interview).filter_by(interviewer=i.interviewer):
        ex_end = ex.scheduled_at + timedelta(minutes=ex.duration_min)
        if i.scheduled_at < ex_end and ex.scheduled_at < end:
            raise HTTPException(409, f"{i.interviewer} already has an interview at {ex.scheduled_at:%Y-%m-%d %H:%M}")
    iv = models.Interview(**i.model_dump()); db.add(iv)
    if a.stage in ("Applied", "Screening"): a.stage = "Interview"
    db.commit(); db.refresh(iv)
    return {"id": iv.id}

@app.get("/interviews")
def interviews(db: Session = Depends(get_db)):
    return [{"id": i.id, "interviewer": i.interviewer, "scheduled_at": i.scheduled_at, "duration_min": i.duration_min,
             "mode": i.mode, "notes": i.notes, "candidate": i.application.candidate.name,
             "job": i.application.job.title} for i in db.query(models.Interview).order_by(models.Interview.scheduled_at)]

@app.delete("/interviews/{iid}")
def cancel(iid: int, db: Session = Depends(get_db)):
    iv = db.get(models.Interview, iid)
    if iv: db.delete(iv); db.commit()
    return {"ok": True}

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    apps = db.query(models.Application).all()
    return {"jobs": db.query(models.Job).count(), "applications": len(apps),
            "avg_score": round(sum(a.score for a in apps) / len(apps), 1) if apps else 0,
            "by_stage": {s: sum(1 for a in apps if a.stage == s) for s in models.STAGES}}
