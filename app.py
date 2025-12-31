import streamlit as st
import os
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed

from email_listener.gmail import fetch_resumes_from_mail
from resume_parser.filereader import extract_text
from resume_parser.textcleaner import clean_text
from nlp_engine.extractor import extract_skills, extract_experience
from matcher.role_req import ROLE_REQUIREMENTS
from matcher.matcher import calculate_match


st.set_page_config("Automated Resume Screening System", layout="wide")
st.title("🎯 Automated Resume Screening System")

with st.sidebar:
    st.subheader("Filters")
    designation = st.selectbox("Select Designation", list(ROLE_REQUIREMENTS.keys()))
    max_apps = st.slider("Number of Applications", 1, 5000, 10)
    ats_threshold = st.slider("ATS Threshold", 0, 100, 70)
    process_btn = st.button("Fetch & Process Applications")

MAX_WORKERS = min(4, os.cpu_count() or 2)

def fast_skill_filter(text, required_skills):
    text = text.lower()
    return any(skill.lower() in text for skill in required_skills)

def process_resume(file_path, required_skills, min_exp, ats_threshold):
    try:
        raw_text = extract_text(file_path)
        text = clean_text(raw_text[:8000])

        skills = extract_skills(text)
        experience, explanation = extract_experience(text)
        exp_years = experience if isinstance(experience, int) else 0

        score, missing = calculate_match(
            skills, required_skills, exp_years, min_exp
        )

        reasons = []
        if score < ats_threshold:
            reasons.append("ATS score below threshold")
        if exp_years < min_exp:
            reasons.append("Low experience")
        if missing:
            reasons.append("Missing skills")

        return {
            "file": os.path.basename(file_path),
            "path": file_path,
            "score": score,
            "status": "Shortlisted" if not reasons else "Rejected",
            "experience": experience,
            "skills": skills,
            "missing": missing,
            "reasons": reasons,
            "exp_explanation": explanation
        }

    except Exception as e:
        return {
            "file": os.path.basename(file_path),
            "path": None,
            "score": 0,
            "status": "Rejected",
            "experience": "Not processed",
            "skills": [],
            "missing": [],
            "reasons": [str(e)],
            "exp_explanation": "Error while processing resume"
        }

if process_btn:
    st.info("⏳ Fetching resumes...")

    os.makedirs("resumes", exist_ok=True)

    emails_checked, resume_files = fetch_resumes_from_mail(max_apps)

    required_skills = ROLE_REQUIREMENTS[designation]["skills"]
    min_exp = ROLE_REQUIREMENTS[designation]["min_experience"]

    stage1_pass = []
    early_rejected = []

    for file_path in resume_files:
        try:
            raw_text = extract_text(file_path)
            text = clean_text(raw_text[:4000])

            if fast_skill_filter(text, required_skills):
                stage1_pass.append(file_path)
            else:
                early_rejected.append({
                    "file": os.path.basename(file_path),
                    "path": file_path,
                    "score": 0,
                    "status": "Rejected",
                    "experience": "Not processed",
                    "skills": [],
                    "missing": required_skills,
                    "reasons": ["Missing required skills"],
                    "exp_explanation": "Rejected in fast skill filter"
                })

        except Exception:
            early_rejected.append({
                "file": os.path.basename(file_path),
                "path": None,
                "score": 0,
                "status": "Rejected",
                "experience": "Not processed",
                "skills": [],
                "missing": [],
                "reasons": ["File read error"],
                "exp_explanation": "Error during fast filtering"
            })

    processed = []
    progress = st.progress(0)
    status_text = st.empty()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(
                process_resume,
                path,
                required_skills,
                min_exp,
                ats_threshold
            )
            for path in stage1_pass
        ]

        for i, future in enumerate(as_completed(futures)):
            processed.append(future.result())
            progress.progress((i + 1) / max(1, len(stage1_pass)))
            status_text.text(
                f"Processing {i + 1} / {len(stage1_pass)} shortlisted resumes..."
            )

    progress.empty()
    status_text.empty()

    processed.extend(early_rejected)

    shortlisted = [p for p in processed if p["status"] == "Shortlisted"]
    rejected = [p for p in processed if p["status"] == "Rejected"]

    st.subheader("📊 Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Processed", len(processed))
    c2.metric("Shortlisted", len(shortlisted))
    c3.metric("Rejected", len(rejected))

    st.subheader("✅ Shortlisted Candidates")
    for p in shortlisted:
        with st.expander(f"{p['file']} | Score: {p['score']}"):
            st.write("**Experience:**", p["experience"])
            st.write("**Skills:**", ", ".join(p["skills"]) or "—")
            st.write("**Explanation:**", p["exp_explanation"])
            if p["path"]:
                with open(p["path"], "rb") as f:
                    st.download_button(
                        "📄 Download Resume",
                        f,
                        file_name=p["file"],
                        key=str(uuid4())
                    )

    st.subheader("❌ Rejected Candidates")
    for p in rejected:
        with st.expander(f"{p['file']} | Score: {p['score']}"):
            st.write("**Rejection Reasons:**", ", ".join(p["reasons"]))
            st.write("**Skills Found:**", ", ".join(p["skills"]) or "—")
            st.write("**Missing Skills:**", ", ".join(p["missing"]) or "—")
            st.write("**Experience Explanation:**", p["exp_explanation"])
            if p["path"]:
                with open(p["path"], "rb") as f:
                    st.download_button(
                        "📄 Download Resume",
                        f,
                        file_name=p["file"],
                        key=str(uuid4())
                    )
