import os
import json
from app.render import render_pdf

JSON_DIR = "storage/json"


def save_json(job_position_id: str, resume_data: dict) -> str:
    os.makedirs(JSON_DIR, exist_ok=True)
    file_path = os.path.join(JSON_DIR, f"{job_position_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(resume_data, f, indent=2, ensure_ascii=False)
    return file_path


def save_pdf(job_position_id: str, master_resume, resume_data: dict, knockout_answers: str) -> str:
    return render_pdf(master_resume, resume_data, knockout_answers, job_position_id)