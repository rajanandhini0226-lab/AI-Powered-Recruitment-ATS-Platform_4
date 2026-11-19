"""Resume parsing, skill extraction and candidate ranking (TF-IDF + skill overlap)."""
import io, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILLS = """python java javascript typescript c++ c# go rust php ruby swift kotlin sql nosql postgresql mysql mongodb redis
react angular vue next.js node.js express django flask fastapi spring html css tailwind docker kubernetes aws azure gcp
terraform jenkins git ci/cd linux rest graphql microservices kafka rabbitmq pandas numpy scikit-learn tensorflow pytorch
nlp machine learning deep learning data analysis tableau power bi excel agile scrum jira figma testing selenium pytest
communication leadership project management""".replace("\n", " ")
SKILL_LIST = sorted(set(re.findall(r"[a-z\+\#\.\/\-]+(?: learning| analysis| bi| management)?", SKILLS)) | {"machine learning", "deep learning", "data analysis", "power bi", "project management"}, key=len, reverse=True)

def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")

def extract_skills(text: str):
    t = " " + text.lower() + " "
    found = set()
    for s in SKILL_LIST:
        if len(s) < 2: continue
        if re.search(r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])", t):
            found.add(s)
    return sorted(found)

def parse_resume(text: str):
    email = re.search(r"[\w\.\-+]+@[\w\.\-]+\.\w+", text)
    phone = re.search(r"(\+?\d[\d\s\-\(\)]{8,14}\d)", text)
    years = [float(y) for y in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", text.lower())]
    first = next((l.strip() for l in text.splitlines() if l.strip()), "Unknown")
    return {
        "name": first[:80],
        "email": email.group(0) if email else None,
        "phone": phone.group(1).strip() if phone else None,
        "skills": extract_skills(text),
        "experience_years": max(years) if years else 0,
    }

def score_candidate(job_description: str, required_skills, resume_text: str, cand_skills):
    req = [s.lower() for s in required_skills] or extract_skills(job_description)
    matched = [s for s in req if s in cand_skills]
    missing = [s for s in req if s not in cand_skills]
    skill_score = len(matched) / len(req) if req else 0.0
    try:
        m = TfidfVectorizer(stop_words="english").fit_transform([job_description, resume_text])
        text_score = float(cosine_similarity(m[0], m[1])[0][0])
    except ValueError:
        text_score = 0.0
    total = round((0.65 * skill_score + 0.35 * text_score) * 100, 1)
    return total, round(skill_score * 100, 1), round(text_score * 100, 1), matched, missing
