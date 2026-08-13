import re
import json
from app.prompts import RESUME_PROMPT_TEMPLATE, RETRY_TEMPLATE
from app.llm_client import call_llm
from app.checks import check_bullet_retention, run_all_checks

MAX_RETRIES = 2


def format_master_resume_for_prompt(resume) -> str:
    lines = [f"Candidate: {resume.name}"]

    if resume.links:
        lines.append("\nLINKS:")
        for link in resume.links:
            lines.append(f"{link.label}: {link.url}")

    if resume.experience:
        lines.append("\nEXPERIENCE:")
        for job in resume.experience:
            lines.append(f"\n{job.title} at {job.company} ({job.location}), {job.dates}")
            for bullet in job.bullets:
                lines.append(f"- {bullet}")
            if job.other_info:
                lines.append(f"(Note: {job.other_info})")
    else:
        lines.append("\nEXPERIENCE: None listed.")

    if resume.projects:
        lines.append("\nPROJECTS:")
        for project in resume.projects:
            header = project.title
            if project.company:
                header += f" - {project.company}"
            if project.dates:
                header += f" ({project.dates})"
            lines.append(f"\n{header}")
            for bullet in project.bullets:
                lines.append(f"- {bullet}")
            if project.other_info:
                lines.append(f"(Note: {project.other_info})")
    else:
        lines.append("\nPROJECTS: None listed.")

    if resume.certifications:
        lines.append("\nCERTIFICATIONS:")
        for cert in resume.certifications:
            lines.append(f"{cert.title}, {cert.company}, {cert.dates}")

    if resume.skills:
        lines.append(f"\nSKILLS: {', '.join(resume.skills)}")

    if resume.languages:
        lines.append(f"\nLANGUAGES: {', '.join(resume.languages)}")

    if resume.education:
        lines.append("\nEDUCATION:")
        for edu in resume.education:
            lines.append(f"{edu.course}, {edu.school}, {edu.dates}")

    return "\n".join(lines)


def flatten_for_checks(resume_data: dict) -> str:
    lines = [str(resume_data.get("summary") or "")]
    for job in resume_data.get("experience", []):
        for bullet in job.get("bullets", []) or []:
            if bullet:
                lines.append(f"- {str(bullet)}")
    for project in resume_data.get("projects", []):
        for bullet in project.get("bullets", []) or []:
            if bullet:
                lines.append(f"- {str(bullet)}")
    return "\n".join(lines)


def flatten_master_resume_numbers(resume) -> str:
    lines = []
    for job in resume.experience:
        lines.extend(job.bullets)
    for project in resume.projects:
        lines.extend(project.bullets)
    return "\n".join(lines)


def parse_json_safely(raw_output: str) -> dict:
    cleaned = raw_output.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            print("RAW MODEL OUTPUT THAT FAILED TO PARSE:")
            print(raw_output)
            raise e

    print("RAW MODEL OUTPUT THAT FAILED TO PARSE:")
    print(raw_output)
    raise ValueError("No JSON object found in model output")


def generate_and_check(master_resume, job_description, job_title, company, knockout_answers) -> dict:
    formatted_resume = format_master_resume_for_prompt(master_resume)
    source_text_for_checks = flatten_master_resume_numbers(master_resume)

    prompt = RESUME_PROMPT_TEMPLATE.format(
    master_resume=formatted_resume,
    job_description=job_description,
    job_title=job_title,
    company=company,
    knockout_answers=format_knockout_answers_for_prompt(knockout_answers)
    )

    raw_output = call_llm(prompt)
    resume_data = parse_json_safely(raw_output)
    resume_text = flatten_for_checks(resume_data)
    violations = run_all_checks(resume_text, source_text_for_checks, resume_data)

    attempts = 0
    while violations and attempts < MAX_RETRIES:
        retry_prompt = RETRY_TEMPLATE.format(
            draft=json.dumps(resume_data, indent=2),
            violations="\n".join(violations)
        )
        raw_output = call_llm(retry_prompt)
        resume_data = parse_json_safely(raw_output)
        resume_text = flatten_for_checks(resume_data)
        violations = run_all_checks(resume_text, source_text_for_checks, resume_data)
        violations += check_bullet_retention(resume_data, master_resume)
        attempts += 1

    status = "ready" if not violations else "needs_review"

    return {
        "resume_data": resume_data,
        "changelog": resume_data.get("changelog", ""),
        "status": status,
        "violations": violations,
        "attempts": attempts
    }

def format_knockout_answers_for_prompt(knockout_answers: dict) -> str:
    if not knockout_answers:
        return "None provided."
    return "\n".join(f"{k}: {v}" for k, v in knockout_answers.items())