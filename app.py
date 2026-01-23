import os
import time
import json
import base64
import streamlit as st
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

from resume_parser.filereader import extract_text
from config.settings import SUPPORTED_FILES

MAX_WORKERS = max(4, (os.cpu_count() or 4) - 1)
CACHE_DIR = ".cache"
MAX_TEXT_CHARS = 12000
MAX_FILE_SIZE_MB = 3

os.makedirs(CACHE_DIR, exist_ok=True)

ROLE_SKILLS = {
    "Python Developer": ["python", "django", "flask", "fastapi", "sql", "git"],
    "Java Developer": ["java", "spring", "hibernate", "sql"],
    "Frontend Developer": ["html", "css", "javascript", "react"],
    "Data Analyst": ["sql", "excel", "power bi", "python"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "linux"],
    "AI Engineer": ["python", "machine learning", "tensorflow", "pytorch"],
    "Full Stack Developer": ["html", "css", "javascript", "react", "node", "sql"],

    "HR Executive": [
        "screening", "onboarding", "document verification", "email management",
        "scheduling meetings", "coordination", "mis preparation", "records",
        "communication", "ms office"
    ]

    "HR Executive": [ "recruitment", "talent acquisition", "onboarding",
    "payroll", "employee engagement", "compliance", "hr analytics"]

}

LOCATIONS = {
    "Any": [],
    "Hyderabad": ["hyderabad", "hyd"],
    "Bangalore": ["bangalore", "bengaluru"],
    "Chennai": ["chennai"],
    "Pune": ["pune"],
    "Delhi": ["delhi"],
    "India": ["india"]
}

# ---------------- PDF VIEWER HELPER ----------------

def show_pdf_base64(pdf_bytes):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="800px"
        style="border: none;">
    </iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

# ---------------- QUERY PARAM HANDLER ----------------

params = st.query_params
selected_resume = params.get("resume")

if selected_resume:
    full_path = None

    for root, _, files in os.walk("resumes"):
        if selected_resume in files:
            full_path = os.path.join(root, selected_resume)
            break

    if full_path and os.path.exists(full_path):
        with open(full_path, "rb") as f:
            pdf_bytes = f.read()

        st.set_page_config(layout="wide")
        st.markdown("## 📄 Resume Viewer")

        st.download_button(
            "⬇️ Download Resume",
            pdf_bytes,
            file_name=selected_resume,
            mime="application/pdf"
        )

        show_pdf_base64(pdf_bytes)

        st.markdown("[⬅ Back to Results](./)")
        st.stop()

    else:
        st.error("Resume file not found")
        st.stop()

# ---------------- CORE LOGIC ----------------

def is_within_date_range(file_path, date_filter):
    if date_filter == "All":
        return True

    modified_time = os.path.getmtime(file_path)
    now = time.time()

    if date_filter == "Last 7 Days":
        return (now - modified_time) <= 7 * 24 * 60 * 60
    if date_filter == "Last 30 Days":
        return (now - modified_time) <= 30 * 24 * 60 * 60
    if date_filter == "Last 90 Days":
        return (now - modified_time) <= 90 * 24 * 60 * 60

    return True


def skill_match(text, skills):
    text = text.lower()
    found = [s for s in skills if s in text]
    missing = [s for s in skills if s not in text]
    score = int((len(found) / len(skills)) * 100)
    return score, found, missing


def location_match(text, location):
    if location == "Any":
        return True
    text = text.lower()
    return any(k in text for k in LOCATIONS[location])


def process_resume(file_path, skills, threshold, location, role):
    name = os.path.basename(file_path)
    cache_key = f"{name}_{role}_{location}_{threshold}.json"
    cache_path = os.path.join(CACHE_DIR, cache_key)

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    if os.path.getsize(file_path) > MAX_FILE_SIZE_MB * 1024 * 1024:
        return {
            "file": name,
            "file_path": file_path,
            "status": "Rejected",
            "reason": "File too large"
        }

    try:
        text = extract_text(file_path)[:MAX_TEXT_CHARS]

        if not text or len(text) < 200:
            result = {
                "file": name,
                "file_path": file_path,
                "status": "Rejected",
                "reason": "Unreadable resume"
            }

        elif not location_match(text, location):
            result = {
                "file": name,
                "file_path": file_path,
                "status": "Rejected",
                "reason": "Location mismatch"
            }

        else:
            score, found, missing = skill_match(text, skills)

            if score < threshold:
                result = {
                    "file": name,
                    "file_path": file_path,
                    "status": "Rejected",
                    "score": score,
                    "reason": "ATS below threshold",
                    "missing_skills": ", ".join(missing)
                }
            else:
                result = {
                    "file": name,
                    "file_path": file_path,
                    "status": "Shortlisted",
                    "score": score,
                    "skills_found": ", ".join(found)
                }

        with open(cache_path, "w") as f:
            json.dump(result, f)

        return result

    except Exception as e:
        return {
            "file": name,
            "file_path": file_path,
            "status": "Rejected",
            "reason": str(e)
        }

# ---------------- UI ----------------

st.set_page_config(layout="wide")
st.title("🎯 Automated Resume Screening System")

with st.sidebar:
    st.subheader("Filters")
    role = st.selectbox("Designation", list(ROLE_SKILLS.keys()))
    location = st.selectbox("Location", list(LOCATIONS.keys()))
    date_filter = st.selectbox(
        "Application Date",
        ["All", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
    )
    max_apps = st.slider("Applications", 100, 5000, 2000)
    threshold = st.slider("ATS Threshold", 1, 100, 70)
    start_btn = st.button("🚀 Fetch & Process")


def make_clickable(df):
    df = df.copy()
    df["Resume"] = df["file"].apply(
        lambda f: f'<a href="?resume={f}">{f}</a>'
    )
    return df.drop(columns=["file", "file_path"], errors="ignore")


if start_btn:
    resumes = [
        os.path.join("resumes", f)
        for f in os.listdir("resumes")
        if f.lower().endswith(SUPPORTED_FILES)
        and is_within_date_range(os.path.join("resumes", f), date_filter)
    ][:max_apps]

    if not resumes:
        st.warning("No resumes found for selected filters")
        st.stop()

    skills = ROLE_SKILLS[role]
    start_time = time.time()

    progress = st.progress(0)
    status_text = st.empty()

    shortlisted, rejected = [], []

    with ProcessPoolExecutor(MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_resume, f, skills, threshold, location, role)
            for f in resumes
        ]

        for i, future in enumerate(as_completed(futures), 1):
            res = future.result()
            if res["status"] == "Shortlisted":
                shortlisted.append(res)
            else:
                rejected.append(res)

            progress.progress(i / len(resumes))
            status_text.text(f"Processing {i}/{len(resumes)} resumes")

    elapsed = (time.time() - start_time) / 60

    st.success(f"✅ Completed in {elapsed:.2f} minutes")

    c1, c2, c3 = st.columns(3)
    c1.metric("Processed", len(resumes))
    c2.metric("Shortlisted", len(shortlisted))
    c3.metric("Rejected", len(rejected))

    st.subheader("✅ Shortlisted Candidates")
    if shortlisted:
        short_df = pd.DataFrame(shortlisted)
        short_df = make_clickable(short_df)
        st.markdown(short_df.to_html(escape=False), unsafe_allow_html=True)
    else:
        st.info("No shortlisted candidates")

    st.subheader("❌ Rejected Candidates (with reasons)")
    if rejected:
        rej_df = pd.DataFrame(rejected)
        rej_df = make_clickable(rej_df)
        st.markdown(rej_df.to_html(escape=False), unsafe_allow_html=True)
    else:
        st.info("No rejected candidates")
