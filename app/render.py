from multiprocessing import context
import os
import subprocess
from jinja2 import Environment, FileSystemLoader

latex_jinja_env = Environment(
    block_start_string='\\BLOCK{',
    block_end_string='}',
    variable_start_string='\\VAR{',
    variable_end_string='}',
    comment_start_string='\\#{',
    comment_end_string='}',
    trim_blocks=True,
    lstrip_blocks=True,
    loader=FileSystemLoader('templates')
)


def escape_latex(value) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace('\\', r'\textbackslash{}')
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text


def build_contact_line(master_resume) -> str:
    parts = [
        escape_latex(master_resume.contact.location),
        escape_latex(master_resume.contact.phone),
        f"\\href{{mailto:{master_resume.contact.email}}}{{{escape_latex(master_resume.contact.email)}}}"
    ]
    for link in master_resume.links:
        parts.append(f"\\href{{https://{link.url}}}{{{escape_latex(link.label)}}}")
    return " $|$ ".join(parts)


def build_knockout_lines(knockout_answers: dict) -> str:
    if not knockout_answers:
        return ""

    selected = []
    if knockout_answers.get("work_authorization"):
        selected.append(knockout_answers["work_authorization"])
    if knockout_answers.get("location"):
        selected.append(knockout_answers["location"])

    if not selected:
        return ""

    escaped = [escape_latex(v) for v in selected]
    return " $|$ ".join(escaped)

def build_render_context(master_resume, resume_data: dict, knockout_answers: str) -> dict:
    context = {
        "name": escape_latex(master_resume.name),
        "contact_line": build_contact_line(master_resume),
        "knockout_lines": build_knockout_lines(knockout_answers),
        "summary": escape_latex(resume_data.get("summary", "")),
        "experience": [],
        "projects": [],
        "skills_line": "",
        "certifications": [],
        "education": [],
    }

    for job in resume_data.get("experience", []):
        context["experience"].append({
            "title": escape_latex(job.get("title", "")),
            "company": escape_latex(job.get("company", "")),
            "location": escape_latex(job.get("location", "")),
            "dates": escape_latex(job.get("dates", "")),
            "bullets": [escape_latex(b) for b in job.get("bullets", [])]
        })

    for project in resume_data.get("projects", []):
        context["projects"].append({
            "title": escape_latex(project.get("title", "")),
            "dates": escape_latex(project.get("dates", "")),
            "bullets": [escape_latex(b) for b in project.get("bullets", [])]
        })

    skills = resume_data.get("skills", [])
    context["skills"] = skills
    context["skills_line"] = ", ".join(escape_latex(s) for s in skills)

    for cert in master_resume.certifications:
        context["certifications"].append({
            "title": escape_latex(cert.title),
            "company": escape_latex(cert.company),
            "dates": escape_latex(cert.dates)
        })

    for edu in master_resume.education:
        context["education"].append({
            "school": escape_latex(edu.school),
            "course": escape_latex(edu.course),
            "dates": escape_latex(edu.dates)
        })

    return context


def render_pdf(master_resume, resume_data: dict, knockout_answers: str, job_position_id: str) -> str:
    context = build_render_context(master_resume, resume_data, knockout_answers)

    template = latex_jinja_env.get_template("resume_template.tex")
    tex_content = template.render(**context)

    os.makedirs("storage/tex", exist_ok=True)
    os.makedirs("storage/pdf", exist_ok=True)

    tex_path = os.path.join("storage/tex", f"{job_position_id}.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    subprocess.run(
        ["pdflatex", "-output-directory=storage/pdf", "-interaction=nonstopmode", tex_path],
        check=True,
        capture_output=True
    )

    return os.path.join("storage/pdf", f"{job_position_id}.pdf")