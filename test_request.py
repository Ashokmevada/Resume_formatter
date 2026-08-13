import json
import requests

with open("test_data/master_resume.json", "r", encoding="utf-8") as f:
    master_resume = json.load(f)

with open("test_data/job_description.txt", "r", encoding="utf-8") as f:
    job_description = f.read()

with open("test_data/knockout_answers.json", "r", encoding="utf-8") as f:
    knockout_answers = json.load(f)

payload = {
    "job_position_id": "test-002",
    "job_title": "Forecast Analyst",
    "company": "Canadian Tire",
    "job_description": job_description,
    "master_resume": master_resume,
    "knockout_answers": knockout_answers
}

response = requests.post("http://localhost:8000/generate-resume", json=payload)

try:
    result = response.json()
except Exception:
    print("Server did not return valid JSON. Raw response:")
    print(response.status_code, response.text)
    raise

print("STATUS:", result.get("status"))
print("ATTEMPTS:", result.get("attempts"))
print("VIOLATIONS:", result.get("violations"))
print("JSON PATH:", result.get("json_path"))
print("PDF PATH:", result.get("pdf_path"))