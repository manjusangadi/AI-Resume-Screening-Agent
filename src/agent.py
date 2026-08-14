import os
import csv
import json
from typing import Dict, List, Any

from src.parser import parse_file, clean_text
from src.extractor import (
    extract_candidate_info_heuristic,
    extract_candidate_info_llm,
    extract_job_description_requirements
)
from src.similarity import calculate_nlp_similarity
from src.scorer import calculate_scores

class ResumeScreeningAgent:
    def __init__(self, provider: str = "mock", api_key: str = None):
        """
        Initializes the Screening Agent.
        provider: 'mock' (default heuristics) or 'groq'
        api_key: Optional API key for LLM provider
        """
        self.provider = provider.lower()
        if self.provider == "groq":
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
        else:
            self.api_key = None
        
        # Adjust provider if key is missing
        if self.provider == "groq" and not self.api_key:
            print("Warning: Groq API key missing. Falling back to Heuristic Mock mode.")
            self.provider = "mock"

    def set_api_key(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key

    def _generate_heuristic_reasoning(self, scores: Dict[str, Any]) -> str:
        """Generates detailed, structured reasoning based on score components."""
        details = scores["details"]
        matching = scores["matching_skills"]
        missing = scores["missing_skills"]
        cand_exp = details["candidate_experience"]
        req_exp = details["required_experience"]
        cand_edu = details["candidate_education"]
        req_edu = details["required_education"]
        
        strengths = []
        gaps = []
        
        # Analyze experience
        if cand_exp >= req_exp:
            strengths.append(f"Possesses {cand_exp} years of experience, meeting/exceeding the required {req_exp} years.")
        else:
            gaps.append(f"Has {cand_exp} years of experience, falling short of the required {req_exp} years.")
            
        # Analyze education
        from src.scorer import EDU_RANK
        if EDU_RANK.get(cand_edu.lower(), 0) >= EDU_RANK.get(req_edu.lower(), 2):
            strengths.append(f"Highest education ({cand_edu}) satisfies the required minimum ({req_edu}).")
        else:
            gaps.append(f"Highest education ({cand_edu}) is below the preferred minimum ({req_edu}).")
            
        # Analyze skills
        if len(matching) > 0:
            skills_list = ", ".join(matching[:4])
            if len(matching) > 4:
                skills_list += f" and {len(matching) - 4} others"
            strengths.append(f"Strong match for core skills: {skills_list}.")
        else:
            gaps.append("Does not match any of the explicitly required technical skills listed.")
            
        if len(missing) > 0:
            missing_list = ", ".join(missing[:3])
            if len(missing) > 3:
                missing_list += f" and {len(missing) - 3} others"
            gaps.append(f"Lacks key required tech skills: {missing_list}.")
            
        # Format reasoning as bullet points
        strengths_str = " ".join(strengths)
        gaps_str = " ".join(gaps) if gaps else "No major technical gaps identified."
        
        rec = ""
        if scores["final_score"] >= 85.0:
            rec = "Highly recommended. Candidate is a top-tier fit for interviews."
        elif scores["final_score"] >= 65.0:
            rec = "Recommended. Candidate is a strong fit; verify missing skills in screen."
        elif scores["final_score"] >= 45.0:
            rec = "Consider with reservations. Verify capabilities in core gap areas."
        else:
            rec = "Not recommended. Candidate has significant skill and experience mismatches."
            
        reasoning = f"- **Strengths**: {strengths_str}\n- **Gaps**: {gaps_str}\n- **Recommendation**: {rec}"
        return reasoning

    def _generate_llm_reasoning(self, jd_text: str, cand_info: Dict[str, Any], scores: Dict[str, Any]) -> str:
        """Sends candidate details and scores to the LLM to generate descriptive reasoning."""
        if not self.api_key or self.provider == "mock":
            return self._generate_heuristic_reasoning(scores)
            
        if self.provider == "groq":
            try:
                from src.groq_service import GroqService
                from src.extractor import extract_job_description_requirements
                
                jd_reqs = extract_job_description_requirements(jd_text)
                groq_svc = GroqService(api_key=self.api_key)
                return groq_svc.generate_candidate_reasoning(jd_reqs, cand_info, scores)
            except Exception as e:
                print(f"Groq reasoning generation failed: {e}. Using heuristics.")
                return self._generate_heuristic_reasoning(scores)
                
        return self._generate_heuristic_reasoning(scores)

    def screen_resumes(self, resumes_dir: str, jd_filepath: str, output_dir: str = "output") -> List[Dict[str, Any]]:
        """
        Executes the screening pipeline.
        Parses all resumes in resumes_dir against the job description at jd_filepath.
        """
        if not os.path.exists(jd_filepath):
            raise FileNotFoundError(f"Job Description file not found at {jd_filepath}")
            
        if not os.path.exists(resumes_dir):
            raise FileNotFoundError(f"Resumes directory not found at {resumes_dir}")
            
        os.makedirs(output_dir, exist_ok=True)
        
        # Load and clean Job Description
        with open(jd_filepath, "r", encoding="utf-8", errors="ignore") as f:
            jd_raw = f.read()
        jd_clean = clean_text(jd_raw)
        
        # Extract requirements from Job Description
        jd_reqs = extract_job_description_requirements(jd_clean)
        
        # Gather resumes
        resume_files = [
            f for f in os.listdir(resumes_dir)
            if os.path.isfile(os.path.join(resumes_dir, f)) and not f.startswith(".")
        ]
        
        if not resume_files:
            print("No resumes found in the resumes directory.")
            return []
            
        ranked_list = []
        
        # Parse and screen each resume
        for r_file in resume_files:
            filepath = os.path.join(resumes_dir, r_file)
            print(f"Processing resume: {r_file}...")
            
            try:
                # 1. Parse text
                resume_raw = parse_file(filepath)
                resume_clean = clean_text(resume_raw)
                
                # 2. Extract features (Heuristic or LLM)
                if self.provider == "mock":
                    cand_info = extract_candidate_info_heuristic(resume_clean)
                else:
                    cand_info = extract_candidate_info_llm(resume_clean, self.provider, self.api_key)
                    
                # Force fallback name to filename if extractor failed to find a valid name
                if cand_info.get("name") == "Unknown Candidate":
                    base_name = os.path.splitext(r_file)[0]
                    # Make friendly, e.g. "john_doe_outstanding" -> "John Doe Outstanding"
                    cand_info["name"] = base_name.replace("_", " ").title()

                # 3. Calculate NLP similarity (TF-IDF + Cosine)
                nlp_similarity = calculate_nlp_similarity(resume_clean, jd_clean)
                
                # 4. Calculate weighted scores
                scores = calculate_scores(cand_info, jd_reqs, nlp_similarity)
                
                # 5. Generate reasoning (Heuristic or LLM)
                reasoning = self._generate_llm_reasoning(jd_clean, cand_info, scores)
                
                # Compile candidate result record
                record = {
                    "filename": r_file,
                    "name": cand_info["name"],
                    "email": cand_info["email"],
                    "phone": cand_info["phone"],
                    "skills": cand_info["skills"],
                    "education": cand_info["education"],
                    "years_of_experience": cand_info["years_of_experience"],
                    "nlp_similarity": round(nlp_similarity, 3),
                    "skill_score": scores["skill_score"],
                    "nlp_score": scores["nlp_score"],
                    "experience_score": scores["experience_score"],
                    "education_score": scores["education_score"],
                    "final_score": scores["final_score"],
                    "tier": scores["tier"],
                    "matching_skills": scores["matching_skills"],
                    "missing_skills": scores["missing_skills"],
                    "reasoning": reasoning,
                    "resume_text": resume_clean
                }
                
                ranked_list.append(record)
                
            except Exception as e:
                print(f"Error screening {r_file}: {e}")
                
        # Sort candidates by final score in descending order
        ranked_list.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Write outputs
        self._write_outputs(ranked_list, output_dir)
        
        return ranked_list

    def _write_outputs(self, ranked_list: List[Dict[str, Any]], output_dir: str):
        """Saves ranked candidate results to CSV and detailed JSON."""
        # 1. Save JSON
        json_path = os.path.join(output_dir, "results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ranked_list, f, indent=2)
        print(f"Saved detailed JSON results to {json_path}")
        
        # 2. Save CSV
        csv_path = os.path.join(output_dir, "ranked_candidates.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Rank", "Candidate Name", "Match Score (%)", "Suitability Tier", 
                "Years Exp", "Education", "Email", "Phone", "Reasoning Summary"
            ])
            for rank, record in enumerate(ranked_list, 1):
                # Clean up reasoning markdown for single-line CSV cells
                reasoning_flat = record["reasoning"].replace("\n", " | ").replace("*", "")
                writer.writerow([
                    rank,
                    record["name"],
                    record["final_score"],
                    record["tier"],
                    record["years_of_experience"],
                    record["education"],
                    record["email"],
                    record["phone"],
                    reasoning_flat
                ])
        print(f"Saved ranked candidate list to {csv_path}")
