from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class JobIn(BaseModel):
    title: str
    description: str
    required_skills: List[str] = []

class StageIn(BaseModel):
    stage: str

class InterviewIn(BaseModel):
    application_id: int
    interviewer: str
    scheduled_at: datetime
    duration_min: int = 45
    mode: str = "Video"
    notes: Optional[str] = ""
