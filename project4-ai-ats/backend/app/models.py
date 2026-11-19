from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))
    resume_text = Column(Text)
    skills = Column(JSON, default=list)
    experience_years = Column(Float, default=0)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    stage = Column(String(30), default="Applied")
    score = Column(Float, default=0)
    skill_score = Column(Float, default=0)
    text_score = Column(Float, default=0)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    interviewer = Column(String(200), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer, default=45)
    mode = Column(String(50), default="Video")
    notes = Column(Text, default="")
    application = relationship("Application", back_populates="interviews")
