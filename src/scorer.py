from typing import Dict, Any, List

# Map education names to ranking integers for mathematical comparison
EDU_RANK = {
    'phd': 4,
    'master': 3,
    'bachelor': 2,
    'associate': 1,
    'none': 0
}

def calculate_scores(candidate_info: Dict[str, Any], job_requirements: Dict[str, Any], nlp_similarity: float) -> Dict[str, Any]:
    """
    Computes candidate scores across four categories:
    1. Skill Match (40%)
    2. NLP Similarity (30%)
    3. Experience Match (20%)
    4. Education Match (10%)
    
    Returns a detailed score breakdown and a final weighted percentage.
    """
    # --- 1. Skill Match (40%) ---
    req_skills = [s.lower() for s in job_requirements.get("required_skills", [])]
    cand_skills = [s.lower() for s in candidate_info.get("skills", [])]
    
    matching_skills = []
    missing_skills = []
    
    if req_skills:
        for skill in req_skills:
            if skill in cand_skills:
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)
                
        skill_match_score = (len(matching_skills) / len(req_skills)) * 100.0
    else:
        skill_match_score = 100.0
        
    # --- 2. NLP Similarity (30%) ---
    # Convert similarity (typically 0.0 - 1.0) to a percentage score
    nlp_score = max(0.0, min(100.0, nlp_similarity * 100.0))
    
    # --- 3. Experience Match (20%) ---
    req_exp = float(job_requirements.get("min_experience", 2.0))
    cand_exp = float(candidate_info.get("years_of_experience", 0.0))
    
    if req_exp > 0.0:
        if cand_exp >= req_exp:
            exp_score = 100.0
        else:
            exp_score = (cand_exp / req_exp) * 100.0
    else:
        exp_score = 100.0
        
    # --- 4. Education Match (10%) ---
    req_edu = job_requirements.get("required_education", "Bachelor").lower()
    cand_edu = candidate_info.get("education", "None").lower()
    
    # Resolve ranks
    req_rank = EDU_RANK.get(req_edu, 2)  # default to Bachelor (2) if unknown
    cand_rank = EDU_RANK.get(cand_edu, 0)
    
    if req_rank > 0:
        if cand_rank >= req_rank:
            edu_score = 100.0
        else:
            edu_score = (cand_rank / req_rank) * 100.0
    else:
        edu_score = 100.0
        
    # --- Weighted Final Score ---
    # Weights: 40% Skills, 30% NLP, 20% Experience, 10% Education
    final_score = (
        (0.40 * skill_match_score) +
        (0.30 * nlp_score) +
        (0.20 * exp_score) +
        (0.10 * edu_score)
    )
    
    # Determine Suitability Tier
    if final_score >= 90.0:
        tier = "Outstanding Match"
    elif final_score >= 75.0:
        tier = "Strong Match"
    elif final_score >= 50.0:
        tier = "Good Match"
    else:
        tier = "Low Match"
        
    # Re-capitalize matching/missing skills for readability
    matching_skills_formatted = [s.title() if s not in ['nlp', 'sql', 'tf-idf', 'api', 'aws', 'gcp', 'rest api', 'cli'] else s.upper() for s in matching_skills]
    missing_skills_formatted = [s.title() if s not in ['nlp', 'sql', 'tf-idf', 'api', 'aws', 'gcp', 'rest api', 'cli'] else s.upper() for s in missing_skills]
    
    return {
        "skill_score": round(skill_match_score, 1),
        "nlp_score": round(nlp_score, 1),
        "experience_score": round(exp_score, 1),
        "education_score": round(edu_score, 1),
        "final_score": round(final_score, 1),
        "tier": tier,
        "matching_skills": matching_skills_formatted,
        "missing_skills": missing_skills_formatted,
        "details": {
            "candidate_skills": candidate_info.get("skills", []),
            "candidate_experience": cand_exp,
            "candidate_education": candidate_info.get("education", "None"),
            "required_skills": req_skills,
            "required_experience": req_exp,
            "required_education": req_edu.title()
        }
    }
