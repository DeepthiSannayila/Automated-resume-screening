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
from matcher.matcher import calculate_match
from matcher.role_req import ROLE_REQUIREMENTS

def analyze_resume(file_path, ats_threshold):
    raw_text = extract_text(file_path)
    text = clean_text(raw_text)
    doc = process_text(text)

    skills = extract_skills(doc)
    experience = extract_experience(text)
    certifications = extract_certifications(text)
    objective = extract_objective(text)
    projects = extract_projects(text)

    reasons = []

    if not set(skills) & set(ROLE_REQUIREMENTS["required_skills"]):
        reasons.append("Required skills not matched")

    if experience < ROLE_REQUIREMENTS["min_experience"]:
        reasons.append("Insufficient experience")

    if not projects:
        reasons.append("No relevant projects found")

    score = calculate_match(
        {
            "skills": skills,
            "experience": experience,
            "certifications": certifications,
            "objective": objective,
            "projects": projects
        },
        ROLE_REQUIREMENTS
    )

    status = "Shortlisted" if score >= ats_threshold else "Rejected"

    if status == "Shortlisted":
        reasons = ["Meets role requirements"]

    return {
        "skills": skills,
        "experience": experience,
        "certifications": certifications,
        "objective": objective,
        "projects": projects,
        "score": score,
        "status": status,
        "reasons": reasons
    }
