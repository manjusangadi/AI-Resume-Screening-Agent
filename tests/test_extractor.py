import pytest
from src.extractor import extract_candidate_info_heuristic

def test_extract_candidate_info_heuristic():
    resume_text = """John Doe
Email: john.doe@example.com
Phone: +1 555-0199
Education: M.S. in Computer Science.

Experience:
Senior Software Engineer (2020 - 2024)
- Programmed in Python, SQL, and deployed with Docker on AWS.
- Built NLP models.
"""
    info = extract_candidate_info_heuristic(resume_text)
    
    assert info["name"] == "John Doe"
    assert info["email"] == "john.doe@example.com"
    assert info["phone"] == "+1 555-0199"
    assert "Python" in info["skills"] or "python" in [s.lower() for s in info["skills"]]
    assert "SQL" in info["skills"] or "sql" in [s.lower() for s in info["skills"]]
    assert info["education"] == "Master"
    assert info["years_of_experience"] > 0.0
