import re

import re

BANNED_WORDS = [
    "spearhead", "leverage", "orchestrate", "streamline", "foster",
    "seamless", "robust", "dynamic", "passionate about", "results-driven",
    "detail-oriented", "proven track record"
]

def check_banned_words(resume_text: str) -> list[str]:
    violations = []
    lower_text = resume_text.lower()
    for word in BANNED_WORDS:
        # word boundary match catches leverage/leveraged/leveraging/leverages, etc.
        pattern = r"\b" + re.escape(word) + r"\w*"
        if re.search(pattern, lower_text):
            violations.append(f"Banned word/phrase found: '{word}' (or a variant)")
    return violations

def check_em_dashes(resume_text: str) -> list[str]:
    if "—" in resume_text or "--" in resume_text:
        return ["Em-dash found in resume text"]
    return []

def check_semicolons(resume_text: str) -> list[str]:
    bullet_lines = [line for line in resume_text.split("\n") if line.strip().startswith(("-", "•"))]
    violations = []
    for line in bullet_lines:
        if ";" in line:
            violations.append(f"Semicolon found in bullet: '{line.strip()[:60]}...'")
    return violations

def check_repeated_verbs(resume_text: str) -> list[str]:
    bullet_lines = [line.strip() for line in resume_text.split("\n") if line.strip().startswith(("-", "•"))]
    seen_verbs = {}
    violations = []
    for line in bullet_lines:
        words = line.lstrip("-• ").split()
        if not words:
            continue
        first_word = words[0].lower()
        seen_verbs[first_word] = seen_verbs.get(first_word, 0) + 1
    for verb, count in seen_verbs.items():
        if count > 1:
            violations.append(f"Verb '{verb}' used to open {count} bullets")
    return violations

def check_number_fabrication(resume_text: str, master_resume: str) -> list[str]:
    resume_numbers = set(re.findall(r"\d+\.?\d*", resume_text))
    source_numbers = set(re.findall(r"\d+\.?\d*", master_resume))
    fabricated = resume_numbers - source_numbers
    if fabricated:
        return [f"Number(s) in resume not found in master resume: {', '.join(fabricated)}"]
    return []

def check_completeness(resume_data: dict) -> list[str]:
    violations = []
    if not resume_data.get("summary", "").strip():
        violations.append("Missing or empty summary")
    for i, job in enumerate(resume_data.get("experience", [])):
        if not job.get("bullets"):
            violations.append(f"Experience entry {i+1} ('{job.get('title', '?')}') has no bullets")
        if not job.get("dates"):
            violations.append(f"Experience entry {i+1} ('{job.get('title', '?')}') missing dates")
    for i, project in enumerate(resume_data.get("projects", [])):
        if not project.get("bullets"):
            violations.append(f"Project entry {i+1} ('{project.get('title', '?')}') has no bullets")
    if not resume_data.get("skills"):
        violations.append("Skills list is empty")
    return violations

def run_all_checks(resume_text: str, master_resume: str, resume_data: dict = None) -> list[str]:
    violations = []
    violations += check_banned_words(resume_text)
    violations += check_em_dashes(resume_text)
    violations += check_semicolons(resume_text)
    violations += check_repeated_verbs(resume_text)
    violations += check_number_fabrication(resume_text, master_resume)
    if resume_data is not None:
        violations += check_schema_shape(resume_data)
        violations += check_completeness(resume_data)
    return violations

def check_schema_shape(resume_data: dict) -> list[str]:
    violations = []
    allowed_keys = {"summary", "experience", "projects", "skills", "changelog"}
    actual_keys = set(resume_data.keys())
    unexpected = actual_keys - allowed_keys
    if unexpected:
        violations.append(f"Unexpected top-level key(s) found: {', '.join(unexpected)}. Only use: summary, experience, projects, skills, changelog")

    experience = resume_data.get("experience", [])
    if not isinstance(experience, list):
        violations.append("'experience' must be a list of objects, not a string or other type")
    else:
        for i, job in enumerate(experience):
            if not isinstance(job, dict):
                violations.append(f"Experience item {i+1} must be an object with title/company/dates/bullets, not a string")

    projects = resume_data.get("projects", [])
    if not isinstance(projects, list):
        violations.append("'projects' must be a list of objects, not a string or other type")
    else:
        for i, project in enumerate(projects):
            if not isinstance(project, dict):
                violations.append(f"Project item {i+1} must be an object with title/bullets, not a string")

    return violations

def check_bullet_retention(resume_data: dict, master_resume) -> list[str]:
    violations = []
    master_bullet_count = sum(len(job.bullets) for job in master_resume.experience) + \
                           sum(len(p.bullets) for p in master_resume.projects)
    resume_bullet_count = sum(len(job.get("bullets", [])) for job in resume_data.get("experience", [])) + \
                          sum(len(p.get("bullets", [])) for p in resume_data.get("projects", []))

    if master_bullet_count > 0:
        retention_ratio = resume_bullet_count / master_bullet_count
        if retention_ratio < 0.7:
            violations.append(
                f"Only {resume_bullet_count} of {master_bullet_count} master resume bullets retained "
                f"({retention_ratio:.0%}) — likely over-compressed, check for unnecessary content cuts"
            )
    return violations
