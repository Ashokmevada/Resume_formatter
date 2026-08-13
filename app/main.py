from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from app.pipeline import generate_and_check
from app.storage import save_json, save_pdf

app = FastAPI()

class ContactInfo(BaseModel):
    location: str
    phone: str
    email: str

class Link(BaseModel):
    label: str
    url: str

class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: str
    dates: str
    bullets: List[str]
    other_info: Optional[str] = None

class ProjectEntry(BaseModel):
    title: str
    company: Optional[str] = None
    dates: Optional[str] = None
    bullets: List[str]
    other_info: Optional[str] = None

class CertificationEntry(BaseModel):
    title: str
    company: str
    dates: str

class EducationEntry(BaseModel):
    school: str
    course: str
    dates: str

class MasterResume(BaseModel):
    name: str
    contact: ContactInfo
    links: List[Link] = []
    experience: List[ExperienceEntry] = []
    projects: List[ProjectEntry] = []
    certifications: List[CertificationEntry] = []
    skills: List[str] = []
    languages: List[str] = []
    education: List[EducationEntry] = []

from typing import Dict

class ResumeRequest(BaseModel):
    job_position_id: str
    job_description: str
    job_title: str
    company: str
    master_resume: MasterResume
    knockout_answers: Dict[str, str] = {}

@app.post("/generate-resume")
def generate_resume(request: ResumeRequest):
    result = generate_and_check(
        master_resume=request.master_resume,
        job_description=request.job_description,
        job_title=request.job_title,
        company=request.company,
        knockout_answers=request.knockout_answers
    )

    json_path = save_json(request.job_position_id, result["resume_data"])
    pdf_path = save_pdf(
        request.job_position_id,
        request.master_resume,
        result["resume_data"],
        request.knockout_answers
    )

    return {
        "job_position_id": request.job_position_id,
        "status": result["status"],
        "json_path": json_path,
        "pdf_path": pdf_path,
        "attempts": result["attempts"],
        "violations": result["violations"]
    }