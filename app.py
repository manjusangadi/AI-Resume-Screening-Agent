import os
import sys
import shutil
import json
from uuid import uuid4
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Add workspace directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import ResumeScreeningAgent
from src.groq_service import GroqService

app = Flask(__name__, static_folder="static", static_url_path="")

# Ensure sample data exists on startup
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
JD_PATH = os.path.join(DATA_DIR, "job_description.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

def ensure_sample_data():
    """Generates sample data programmatically if directories are empty."""
    os.makedirs(RESUMES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check if we need to generate samples
    has_resumes = any(os.path.isfile(os.path.join(RESUMES_DIR, f)) for f in os.listdir(RESUMES_DIR) if not f.startswith("."))
    has_jd = os.path.exists(JD_PATH)
    
    if not has_resumes or not has_jd:
        print("[*] Sample data missing or empty. Auto-generating sample profiles and job description...")
        try:
            import generate_samples
            generate_samples.main()
        except Exception as e:
            print(f"[!] Failed to auto-generate samples: {e}")

# Call sample ensuring logic
ensure_sample_data()

def analyze_jd_heuristically(jd_text: str) -> dict:
    """Heuristic fallback for JD analysis when Groq is not configured."""
    from src.extractor import extract_job_description_requirements
    reqs = extract_job_description_requirements(jd_text)
    
    # Guess title
    title = "Junior AI Research Associate & Python Engineer"
    lines = [l.strip() for l in jd_text.split('\n') if l.strip()]
    for line in lines[:3]:
        if "title" in line.lower() or "role" in line.lower():
            title = line.split(":")[-1].strip()
            break
            
    # Guess responsibilities
    responsibilities = []
    for line in lines:
        if line.strip().startswith("-") or line.strip().startswith("*"):
            if any(kw in line.lower() for kw in ["work on", "responsib", "develop", "build", "maintain"]):
                responsibilities.append(line.strip()[1:].strip())
                
    return {
        "job_title": title,
        "required_skills": reqs["required_skills"],
        "preferred_skills": ["Machine Learning", "NLP"] if "python" in reqs["required_skills"] else [],
        "minimum_experience": int(reqs["min_experience"]),
        "maximum_experience": None,
        "education_requirements": [reqs["required_education"]],
        "responsibilities": responsibilities[:5] if responsibilities else ["Develop AI agents", "Build data pipelines"],
        "keywords": reqs["required_skills"]
    }

def improve_resume_heuristically(resume_text: str, jd_text: str, candidate_result: dict) -> dict:
    """Heuristic fallback for Resume Improvement when Groq is not configured."""
    matching = candidate_result.get("matching_skills", [])
    missing = candidate_result.get("missing_skills", [])
    
    strengths = [f"Strong background in {', '.join(matching[:3])}" if matching else "Standard technical background."]
    missing_areas = [f"Gain proficiency in {s} (Learn this skill and add it to your resume only after gaining genuine knowledge or experience)." for s in missing]
    
    project_suggestions = []
    for m in missing[:3]:
        project_suggestions.append(f"Build a portfolio project utilizing {m} to demonstrate competency.")
        
    bullet_improvements = [
        "Action Verb: Rewrite experience bullet points starting with strong action verbs (e.g., 'Developed', 'Engineered', 'Optimized'). Example rewrite based only on existing information.",
        "Metrics: Quantify achievements (e.g. 'Improved model efficiency by 20%') where possible. Example rewrite based only on existing information."
    ]
    
    return {
        "current_match_summary": f"The candidate has a match score of {candidate_result.get('final_score')}% and is categorized as a {candidate_result.get('tier')}.",
        "strengths": strengths,
        "missing_or_weak_areas": missing_areas if missing_areas else ["No major required skills missing."],
        "keywords_to_highlight": matching[:5] if matching else ["Python", "SQL"],
        "resume_improvements": ["Formatting: Ensure a clean, single-column layout for ATS compatibility.", "Skills Section: Group technical skills by category (Languages, Libraries, Databases)."],
        "project_suggestions": project_suggestions if project_suggestions else ["Expand on your existing projects by adding unit tests or dockerizing them."],
        "bullet_point_improvements": bullet_improvements,
        "ats_tips": ["Save and upload your resume as PDF or DOCX format.", "Keep section headers standard (e.g., 'Experience', 'Education', 'Skills')."],
        "priority_action_plan": {
            "high": [f"Learn and apply missing skills: {', '.join(missing[:2])}" if missing else "Polish project descriptions."],
            "medium": ["Rewrite experience bullets with action verbs."],
            "low": ["Format resume sections standardly."]
        }
    }

@app.route("/")
def index():
    """Serves the dashboard home page."""
    return send_from_directory("static", "index.html")

@app.route("/api/job-description", methods=["GET"])
def get_jd():
    """Returns the current active Job Description."""
    ensure_sample_data()
    if os.path.exists(JD_PATH):
        try:
            with open(JD_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            return jsonify({"success": True, "job_description": content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "Job Description file not found"}), 404

@app.route("/api/job-description", methods=["POST"])
def save_jd():
    """Updates the active Job Description."""
    data = request.json or {}
    content = data.get("job_description", "").strip()
    if not content:
        return jsonify({"success": False, "error": "Job Description cannot be empty"}), 400
        
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(JD_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"success": True, "message": "Job Description updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/analyze-jd", methods=["POST"])
def analyze_jd():
    """Extracts job requirements in real-time using Groq (or heuristics as fallback)."""
    data = request.json or {}
    jd_text = data.get("job_description", "").strip()
    if not jd_text:
        return jsonify({"success": False, "error": "Job description is empty"}), 400
        
    # Read API Key from environment or request headers
    api_key = os.getenv("GROQ_API_KEY")
    groq_svc = GroqService(api_key=api_key)
    
    try:
        if groq_svc.is_available():
            analysis = groq_svc.analyze_job_description(jd_text)
        else:
            analysis = analyze_jd_heuristically(jd_text)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to analyze Job Description: {str(e)}"}), 500

@app.route("/api/improve-resume", methods=["POST"])
def improve_resume():
    """Analyzes resume and provides detailed, honest improvement metrics."""
    data = request.json or {}
    resume_text = data.get("resume_text", "").strip()
    jd_text = data.get("job_description", "").strip()
    candidate_result = data.get("candidate_result", {})
    
    if not resume_text:
        return jsonify({"success": False, "error": "Resume text is empty"}), 400
    if not jd_text:
        return jsonify({"success": False, "error": "Job description is empty"}), 400
        
    api_key = os.getenv("GROQ_API_KEY")
    groq_svc = GroqService(api_key=api_key)
    
    try:
        if groq_svc.is_available():
            suggestions = groq_svc.improve_resume(resume_text, jd_text, candidate_result)
        else:
            suggestions = improve_resume_heuristically(resume_text, jd_text, candidate_result)
        return jsonify({"success": True, "suggestions": suggestions})
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to optimize resume: {str(e)}"}), 500

@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    """
    Returns the sorted list of candidates.
    If results have already been computed, read them.
    Otherwise, run a quick screening in mock mode.
    """
    results_json = os.path.join(OUTPUT_DIR, "results.json")
    if os.path.exists(results_json):
        try:
            with open(results_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify({"success": True, "candidates": data})
        except Exception:
            pass
            
    # Trigger auto-screening if results.json is missing
    return trigger_screen()

@app.route("/api/screen", methods=["POST"])
def trigger_screen():
    """Triggers the screening agent algorithm."""
    data = request.json or {}
    provider = data.get("provider", "mock")
    api_key = data.get("api_key", "").strip()
    
    # Prioritize dashboard input, fallback to env variable if blank
    if provider == "groq" and not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        
    agent = ResumeScreeningAgent(provider=provider, api_key=api_key if api_key else None)
    
    try:
        results = agent.screen_resumes(resumes_dir=RESUMES_DIR, jd_filepath=JD_PATH, output_dir=OUTPUT_DIR)
        return jsonify({
            "success": True, 
            "provider": agent.provider,
            "candidates": results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_resumes():
    """Endpoint for uploading resumes securely, generating unique names to prevent overwriting."""
    if "resumes" not in request.files:
        return jsonify({"success": False, "error": "No files provided in request"}), 400
        
    files = request.files.getlist("resumes")
    saved_count = 0
    errors = []
    
    for f in files:
        if f.filename == "":
            continue
            
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in [".txt", ".pdf", ".docx"]:
            errors.append(f"Skipped {f.filename}: unsupported format.")
            continue
            
        try:
            # Clean filename to avoid directory traversal
            clean_name = secure_filename(f.filename)
            name_without_ext, extension = os.path.splitext(clean_name)
            # Append a short unique identifier prefix/suffix to prevent overwrites
            unique_name = f"{name_without_ext}_{uuid4().hex[:8]}{extension}"
            
            filepath = os.path.join(RESUMES_DIR, unique_name)
            f.save(filepath)
            saved_count += 1
        except Exception as e:
            errors.append(f"Failed to save {f.filename}: {str(e)}")
            
    return jsonify({
        "success": True, 
        "message": f"Successfully uploaded {saved_count} resumes.",
        "errors": errors
    })

@app.route("/api/download/csv", methods=["GET"])
def download_csv():
    """Serves the generated shortlisting CSV report."""
    csv_file = "ranked_candidates.csv"
    if os.path.exists(os.path.join(OUTPUT_DIR, csv_file)):
        return send_from_directory(OUTPUT_DIR, csv_file, as_attachment=True)
    return jsonify({"success": False, "error": "CSV report not generated yet. Run the screening first."}), 404

@app.route("/api/download/json", methods=["GET"])
def download_json():
    """Serves the generated detailed JSON report."""
    json_file = "results.json"
    if os.path.exists(os.path.join(OUTPUT_DIR, json_file)):
        return send_from_directory(OUTPUT_DIR, json_file, as_attachment=True)
    return jsonify({"success": False, "error": "JSON report not generated yet. Run the screening first."}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
