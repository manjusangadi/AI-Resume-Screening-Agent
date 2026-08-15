import re
import json
from typing import Dict, List, Any

# A comprehensive list of technical and business skills to extract heuristically
MASTER_SKILLS = {
    'python', 'pandas', 'numpy', 'scikit-learn', 'sklearn', 'pytorch', 'tensorflow', 'keras',
    'sql', 'postgresql', 'mysql', 'sqlite', 'mongodb', 'redis', 'nosql',
    'flask', 'fastapi', 'django', 'rest api', 'api', 'graphql',
    'javascript', 'typescript', 'react', 'node.js', 'node', 'express', 'html', 'css', 'tailwind',
    'tf-idf', 'cosine similarity', 'nlp', 'natural language processing', 'embeddings', 'nltk',
    'spacy', 'transformers', 'hugging face', 'llm', 'deep learning', 'machine learning', 'ml',
    'git', 'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'devops', 'ci/cd',
    'jira', 'agile', 'scrum', 'salesforce', 'hubspot', 'sales', 'business development',
    'tableau', 'power bi', 'excel', 'powerpoint', 'statistics', 'mathematics', 'linear algebra'
}

DEGREE_MAPPING = {
    'phd': 4, 'doctorate': 4,
    'master': 3, 'm.s.': 3, 'm.sc.': 3, 'mba': 3,
    'bachelor': 2, 'b.s.': 2, 'b.sc.': 2, 'b.a.': 2,
    'associate': 1, 'diploma': 1, 'bootcamp': 1,
    'none': 0
}

def extract_candidate_info_heuristic(text: str) -> Dict[str, Any]:
    """
    Offline heuristic parser using regex and keyword matching.
    Returns structured data about the candidate.
    """
    cleaned_text = text.lower()
    
    # 1. Extract Name (Heuristic: Look at the first line or first non-empty lines)
    name = "Unknown Candidate"
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        # Check if the first line looks like a name (not an email, not too long)
        first_line = lines[0]
        if len(first_line) < 40 and not any(char in first_line for char in ['@', ':', '|', '/']):
            name = first_line
        elif len(lines) > 1:
            second_line = lines[1]
            if len(second_line) < 40 and not any(char in second_line for char in ['@', ':', '|', '/']):
                name = second_line

    # 2. Extract Email (Regex)
    email = "N/A"
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        email = email_match.group(0)

    # 3. Extract Phone (Regex)
    phone = "N/A"
    phone_match = re.search(r'\+?\d[\d\s\(\)\.\-]{8,}\d', text)
    if phone_match:
        phone = phone_match.group(0)

    # 4. Extract Skills (Keyword Matching)
    found_skills = []
    # Tokenize text into lower words/phrases
    for skill in MASTER_SKILLS:
        # Use word boundaries, but handle special cases like .js, c++, c#, rest api
        if skill in ['node.js', 'rest api', 'tailwind css', 'power bi']:
            if skill in cleaned_text:
                found_skills.append(skill)
        elif skill == 'c++':
            if 'c++' in cleaned_text:
                found_skills.append(skill)
        elif skill == 'c#':
            if 'c#' in cleaned_text:
                found_skills.append(skill)
        elif skill == 'ml':
            # Avoid matching ml in words, use word boundary
            if re.search(r'\bml\b', cleaned_text):
                found_skills.append('machine learning')
        elif skill == 'nlp':
            if re.search(r'\bnlp\b', cleaned_text):
                found_skills.append('nlp')
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, cleaned_text):
                # Standardize spelling
                if skill == 'sklearn':
                    found_skills.append('scikit-learn')
                elif skill == 'node':
                    found_skills.append('node.js')
                else:
                    found_skills.append(skill)
                    
    # Deduplicate and sort
    found_skills = sorted(list(set(found_skills)))

    # 5. Extract Education (Degree Hierarchy)
    highest_degree = "None"
    degree_rank = -1
    for deg_keyword, rank in DEGREE_MAPPING.items():
        # Match word boundaries or abbreviations
        if deg_keyword in ['m.s.', 'm.sc.', 'b.s.', 'b.sc.', 'b.a.']:
            pattern = re.escape(deg_keyword)
        else:
            pattern = r'\b' + deg_keyword + r'\b'
            
        if re.search(pattern, cleaned_text):
            if rank > degree_rank:
                degree_rank = rank
                # Store readable title
                if rank == 4: highest_degree = "PhD"
                elif rank == 3: highest_degree = "Master"
                elif rank == 2: highest_degree = "Bachelor"
                elif rank == 1: highest_degree = "Associate / Bootcamp"

    # 6. Extract Years of Experience (Regex search for numbers preceding 'years experience' etc.)
    years_exp = 0.0
    
    # Pattern A: "5 years", "3.5 years of experience", "4+ years"
    pattern_a = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b', cleaned_text)
    if pattern_a:
        # Convert to float and take the maximum found
        try:
            years_exp = max(float(x) for x in pattern_a)
        except ValueError:
            pass
            
    # Pattern B: Parse dates like (2020 - 2023) or 2018 - Present and sum them up
    # This is a fallback/refinement heuristic
    date_ranges = re.findall(r'\b(20\d{2})\b\s*(?:-|to)\s*\b(20\d{2}|present|current)\b', cleaned_text)
    calculated_years = 0.0
    for start, end in date_ranges:
        start_yr = int(start)
        if end in ['present', 'current']:
            end_yr = 2026  # Current year mockup matching local time
        else:
            end_yr = int(end)
        diff = max(0.0, float(end_yr - start_yr))
        # Cap unreasonable differences
        if diff < 15.0:
            calculated_years += diff
            
    if calculated_years > years_exp:
        years_exp = calculated_years

    # If no experience matches and the profile has 'senior' in name or summary, default to a sensible number
    if years_exp == 0.0:
        if 'senior' in cleaned_text:
            years_exp = 5.0
        elif 'lead' in cleaned_text:
            years_exp = 7.0
        elif 'intern' in cleaned_text or 'junior' in cleaned_text:
            years_exp = 0.5
        else:
            years_exp = 1.0  # Default minimum

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": found_skills,
        "education": highest_degree,
        "years_of_experience": round(years_exp, 1)
    }

def extract_candidate_info_llm(text: str, provider: str, api_key: str) -> Dict[str, Any]:
    """
    Leverages Groq to extract structured fields from the resume text.
    Only supports 'groq' provider. Falls back to offline heuristics on failure.
    """
    if provider.lower() != "groq":
        return extract_candidate_info_heuristic(text)
        
    try:
        from src.groq_service import GroqService, parse_json_safely
        groq_svc = GroqService(api_key=api_key)
        
        system_prompt = """
            You are an expert recruitment system parsing a candidate's resume.
            Extract the following details from the resume text:
            1. Candidate Name
            2. Email Address
            3. Phone Number
            4. Technical and Soft Skills (as a list)
            5. Highest Education Degree (select from: PhD, Master, Bachelor, Associate, None)
            6. Years of Professional Experience (as a floating-point number, e.g. 3.5. Estimate from dates if not explicitly stated)

            Return ONLY a valid JSON object with the following keys:
            {
            "name": "...",
            "email": "...",
            "phone": "...",
            "skills": ["...", "..."],
            "education": "...",
            "years_of_experience": 0.0
            }
            Do not write any markdown blocks (like ```json), commentary, or extra text. Just return the raw JSON.
        """

        user_prompt = f"Resume Content:\n\n{text}"
        response_text = groq_svc._call_groq(system_prompt, user_prompt, json_mode=True)
        return parse_json_safely(response_text)
    except Exception as e:
        print(f"Groq parsing failed: {e}. Falling back to heuristics.")
        return extract_candidate_info_heuristic(text)

def extract_job_description_requirements(jd_text: str) -> Dict[str, Any]:
    """
    Heuristically extracts key parameters from the job description for the scoring engine:
    - Required Skills (list)
    - Minimum Experience Years (float)
    - Required Education Level (PhD, Master, Bachelor, etc.)
    """
    cleaned_jd = jd_text.lower()
    
    # 1. Skills
    required_skills = []
    for skill in MASTER_SKILLS:
        if skill in ['node.js', 'rest api', 'tailwind css', 'power bi']:
            if skill in cleaned_jd:
                required_skills.append(skill)
        elif skill == 'c++':
            if 'c++' in cleaned_jd:
                required_skills.append(skill)
        elif skill == 'ml':
            if re.search(r'\bml\b', cleaned_jd):
                required_skills.append('machine learning')
        elif skill == 'nlp':
            if re.search(r'\bnlp\b', cleaned_jd):
                required_skills.append('nlp')
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, cleaned_jd):
                if skill == 'sklearn':
                    required_skills.append('scikit-learn')
                elif skill == 'node':
                    required_skills.append('node.js')
                else:
                    required_skills.append(skill)
                    
    required_skills = sorted(list(set(required_skills)))
    # If no skills found, default to standard ones matching our mock prompt
    if not required_skills:
        required_skills = ['python', 'pandas', 'sql', 'machine learning', 'nlp']

    # 2. Experience
    min_years = 0.0
    exp_match = re.search(r'(?:at least|minimum|experience of)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b', cleaned_jd)
    if exp_match:
        min_years = float(exp_match.group(1))
    else:
        # Check for numeric items
        numbers = re.findall(r'\b(\d)\b\s*years?', cleaned_jd)
        if numbers:
            min_years = float(numbers[0])
            
    if min_years == 0.0:
        min_years = 2.0  # Default sensible minimum

    # 3. Education
    required_edu = "Bachelor"
    degree_rank = -1
    for deg_keyword, rank in DEGREE_MAPPING.items():
        if deg_keyword in ['m.s.', 'm.sc.', 'b.s.', 'b.sc.', 'b.a.']:
            pattern = re.escape(deg_keyword)
        else:
            pattern = r'\b' + deg_keyword + r'\b'
            
        if re.search(pattern, cleaned_jd):
            if rank > degree_rank:
                degree_rank = rank
                if rank == 4: required_edu = "PhD"
                elif rank == 3: required_edu = "Master"
                elif rank == 2: required_edu = "Bachelor"
                elif rank == 1: required_edu = "Associate"

    return {
        "required_skills": required_skills,
        "min_experience": min_years,
        "required_education": required_edu
    }
