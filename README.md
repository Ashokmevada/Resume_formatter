# Resume Tailoring Service

A standalone microservice that takes a job description and a candidate's structured master resume, and produces an **ATS-optimized, human-sounding tailored resume** (JSON + PDF), along with a changelog of which job requirements were matched.

Built as Owner B's component (Resume & Matching) in a 3-owner automated job application pipeline. See [`Job_Application_System_Spec.docx`](./Job_Application_System_Spec.docx) for the full project spec.

> **Status:** In active development / testing. Not yet production-ready — see [Known Limitations](#known-limitations) below.

---

## What it does

1. Accepts a job description + a candidate's structured master resume (JSON)
2. Extracts the JD's must-have and preferred requirements
3. Tailors the resume: selects, reorders, and lightly rewrites bullets to align with the JD's language, without fabricating anything
4. Runs the draft through a set of deterministic quality checks (banned buzzwords, invented numbers, schema shape, completeness, etc.)
5. Retries automatically (up to 2x) if checks fail, feeding back the specific violations
6. Renders the final result into a one-page LaTeX-based PDF, plus saves the structured JSON
7. Returns `{ job_position_id, status, json_path, pdf_path, attempts, violations }`

The resume is written to explicitly **avoid common AI-generated tells** — no buzzwords like "leveraged" or "spearheaded," no em-dashes, no suspiciously round metrics, no uniform bullet rhythm, no invented numbers. Every number in the output must trace back to something literally present in the candidate's master resume.

---

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI + Pydantic |
| Server | Uvicorn |
| LLM | Pluggable — Ollama (local) or hosted (OpenAI / Anthropic) via a single isolated `llm_client.py` |
| PDF rendering | Jinja2 (custom LaTeX delimiters) + `pdflatex` (MiKTeX) |
| Storage | Local disk (placeholder — shared storage not yet wired in) |

---

## Project structure

```
resume-service/
  app/
    main.py          # FastAPI app, request/response schema, endpoint
    prompts.py        # Generation prompt + retry prompt (29 tailoring/quality rules)
    llm_client.py      # Only file that knows which LLM provider is in use
    checks.py         # Deterministic rule checks (buzzwords, fabrication, schema shape, etc.)
    pipeline.py        # Orchestrates: format prompt -> call LLM -> parse -> check -> retry
    storage.py         # Saves JSON + triggers PDF render
    render.py          # Fills the LaTeX template, escapes special chars, compiles PDF
  templates/
    resume_template.tex
  test_data/
    master_resume.json
    job_description.txt
    knockout_answers.json
  storage/             # Generated output (gitignored)
  test_request.py      # Manual test harness
```

---

## Setup

### 1. Python environment

```powershell
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn requests python-docx pydantic jinja2
```

### 2. LaTeX (for PDF rendering)

Install [MiKTeX](https://miktex.org/download), then confirm:
```powershell
pdflatex --version
```

### 3. Choose an LLM provider

**Local (Ollama) — free, no API cost, slower:**
```powershell
ollama pull llama3.1
ollama serve
```

**Hosted (OpenAI or Anthropic) — fast, small per-call cost:**
```powershell
pip install openai        # or: pip install anthropic
setx OPENAI_API_KEY "your-key-here"     # or ANTHROPIC_API_KEY
```
> `setx` only takes effect in **new** terminal windows opened after running it.

Set the matching model name in `app/llm_client.py`.

Full setup details and troubleshooting: see [`Part2_Setup_And_HowToRun.md`](./Part2_Setup_And_HowToRun.md).

---

## Running it

**Terminal 1 — API server:**
```powershell
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — run a test:**
```powershell
python test_request.py
```

To test against a different job, edit `test_data/job_description.txt` and update `job_position_id` / `job_title` / `company` in `test_request.py`.

Check the result:
- Console output: `STATUS`, `ATTEMPTS`, `VIOLATIONS`, `JSON PATH`, `PDF PATH`
- `storage/json/{id}.json` — structured resume data
- `storage/pdf/{id}.pdf` — **always open and review manually**, don't trust `status: ready` alone

---

## Master resume format

```json
{
  "name": "Full Name",
  "contact": { "location": "City, ST", "phone": "...", "email": "..." },
  "links": [ { "label": "LinkedIn", "url": "..." } ],
  "experience": [
    { "title": "...", "company": "...", "location": "...", "dates": "...", "bullets": ["..."], "other_info": null }
  ],
  "projects": [
    { "title": "...", "company": null, "dates": null, "bullets": ["..."], "other_info": "Personal project" }
  ],
  "certifications": [ { "title": "...", "company": "...", "dates": "..." } ],
  "skills": ["..."],
  "languages": ["..."],
  "education": [ { "school": "...", "course": "...", "dates": "..." } ]
}
```

All list fields default to empty — not every candidate has certifications, projects, etc.

---

## Quality rules enforced

The generation prompt (`app/prompts.py`) encodes 29 rules across four categories:

- **Keyword matching** — exact JD phrasing, 8-10 critical phrases mirrored naturally into Experience/Projects bullets
- **Banned language** — no "leveraged," "spearheaded," "results-driven," em-dashes, semicolons in bullets, etc.
- **Bullet structure** — varied length and rhythm, no invented or rounded numbers, real specifics over vague claims
- **Formatting** — single column, no icons, standard fonts/headers, one page (two if 5+ years experience)

Deterministic checks (`app/checks.py`) verify a subset of these automatically before a resume is marked `ready`.

---

## Known limitations

- **Shared storage not implemented** — output currently saves to local disk only; needs Supabase/S3 before another service (Owner A) can reach it across machines
- **No .docx output** — only PDF + JSON are produced; Word output is a known open item
- **No automated check for summary overclaiming** — e.g., implying professional experience from what was actually a personal project; currently requires manual review
- **No persistent status/file_path record** — the API returns this per-call but doesn't store it anywhere pollable
- **LLM-judged quality checks (tone, vagueness) not implemented** — only deterministic/code-based checks exist today

Full development history, every bug encountered, and why each fix was made the way it was: see [`Part3_Development_Log_And_Code_Reference.md`](./Part3_Development_Log_And_Code_Reference.md).

---

## Documentation

- [`Part1_Architecture_Overview.md`](./Part1_Architecture_Overview.md) — design decisions and data flow
- [`Part2_Setup_And_HowToRun.md`](./Part2_Setup_And_HowToRun.md) — full setup and troubleshooting
- [`Part3_Development_Log_And_Code_Reference.md`](./Part3_Development_Log_And_Code_Reference.md) — bug history, model comparisons, cost data

---

## Part of a larger system

This service is Owner B's component in a 3-person automated Workday job application pipeline (Owner A: browser automation / form filling, Owner C: schema, orchestration, dashboard). See the full project spec for the other two owners' scope and the end-to-end workflow.
