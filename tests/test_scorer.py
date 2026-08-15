import pytest
from src.scorer import calculate_scores

def test_calculate_scores_perfect_match():
    cand_info = {
        "skills": ["Python", "SQL", "Machine Learning"],
        "years_of_experience": 5.0,
        "education": "Master"
    }
    jd_reqs = {
        "required_skills": ["Python", "SQL"],
        "min_experience": 3.0,
        "required_education": "Bachelor"
    }
    nlp_similarity = 1.0  # Perfect similarity
    
    scores = calculate_scores(cand_info, jd_reqs, nlp_similarity)
    
    assert scores["skill_score"] == 100.0
    assert scores["nlp_score"] == 100.0
    assert scores["experience_score"] == 100.0
    assert scores["education_score"] == 100.0
    assert scores["final_score"] == 100.0
    assert scores["tier"] == "Outstanding Match"
    assert "Python" in scores["matching_skills"]
    assert "SQL" in scores["matching_skills"]
    assert len(scores["missing_skills"]) == 0

def test_calculate_scores_partial_match():
    cand_info = {
        "skills": ["Python"],
        "years_of_experience": 1.0,
        "education": "Bachelor"
    }
    jd_reqs = {
        "required_skills": ["Python", "SQL"],
        "min_experience": 2.0,
        "required_education": "Master"
    }
    nlp_similarity = 0.5
    
    scores = calculate_scores(cand_info, jd_reqs, nlp_similarity)
    
    assert scores["skill_score"] == 50.0       # 1 out of 2
    assert scores["nlp_score"] == 50.0         # 0.5 * 100
    assert scores["experience_score"] == 50.0  # 1.0 / 2.0
    assert scores["education_score"] == 66.7   # Bachelor (2) / Master (3) => 2/3 * 100 = 66.67
    
    # Weights: 40% skills (20.0), 30% NLP (15.0), 20% experience (10.0), 10% education (6.67)
    # Total = 51.67 => 51.7
    assert scores["final_score"] == 51.7
    assert scores["tier"] == "Good Match"
    assert "Python" in scores["matching_skills"]
    assert "SQL" in scores["missing_skills"]
