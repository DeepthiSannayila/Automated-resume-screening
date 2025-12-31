import re
from datetime import datetime
from nlp_engine.nlpprocessor import nlp

SKILLS_DB = {
    "python", "java", "sql", "mysql", "postgresql", "mongodb",
    "django", "flask", "fastapi",
    "aws", "azure", "gcp",
    "docker", "kubernetes",
    "linux", "git", "github",
    "html", "css", "javascript",
    "react", "node", "spring",
    "machine learning", "deep learning", "nlp"
}

def extract_skills(text):
    if not text:
        return []

    text = text.lower()
    skills_found = set()

    # Fast exact phrase matching for multi-word skills
    for skill in SKILLS_DB:
        if " " in skill and skill in text:
            skills_found.add(skill)

    # Token-based matching for single-word skills
    doc = nlp(text)
    for token in doc:
        if token.text in SKILLS_DB:
            skills_found.add(token.text)

    return list(skills_found)


def extract_experience(text):
    if not text:
        return "Not mentioned", "Resume text empty"

    text = text.lower()
    current_year = datetime.now().year
    experience_years = []

    patterns = [
        r"(20\d{2})\s*-\s*(20\d{2})",
        r"(20\d{2})\s*-\s*(present|current)"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                start_year = int(match[0])

                if isinstance(match, tuple) and len(match) > 1:
                    if match[1] in ("present", "current"):
                        end_year = current_year
                    else:
                        end_year = int(match[1])
                else:
                    end_year = current_year

                if 1950 <= start_year <= end_year <= current_year:
                    experience_years.append(end_year - start_year)

            except Exception:
                continue

    if experience_years:
        total_exp = max(experience_years)
        explanation = (
            f"Experience calculated using year ranges found in resume. "
            f"Maximum continuous experience identified: {total_exp} years."
        )
        return total_exp, explanation

    return "Not mentioned", "No valid experience date ranges found in resume."
