import os

from resume_parser.filereader import extract_text
from resume_parser.textcleaner import clean_text
from nlp_engine.nlpprocessor import process_text
from nlp_engine.extractor import (
    extract_skills,
    extract_experience,
    extract_certifications,
    extract_objective,
    extract_projects
)
from matcher.role_req import ROLE_REQUIREMENTS
from matcher.matcher import calculate_match
from scoring.scorer import decide


def process_resume_cli(file_path):
    raw_text = extract_text(file_path)
    text = clean_text(raw_text)
    doc = process_text(text)

    candidate = {
        "skills": extract_skills(doc),
        "experience": extract_experience(text),
        "certifications": extract_certifications(text),
        "objective": extract_objective(text),
        "projects": extract_projects(text),
    }

    score = calculate_match(candidate, ROLE_REQUIREMENTS)
    status = decide(score)

    return {
        "file": os.path.basename(file_path),
        "skills": candidate["skills"],
        "experience": candidate["experience"],
        "certifications": candidate["certifications"],
        "objective": candidate["objective"],
        "projects": candidate["projects"],
        "score": score,
        "status": status,
    }


def run_pipeline():
    resumes_dir = "resumes"

    if not os.path.exists(resumes_dir):
        return

    for file in os.listdir(resumes_dir):
        if not file.lower().endswith((".pdf", ".docx")):
            continue

        path = os.path.join(resumes_dir, file)
        result = process_resume_cli(path)

        print(
            f"{result['file']} → "
            f"{result['status']} | "
            f"Score: {result['score']}"
        )


if __name__ == "__main__":
    run_pipeline()
