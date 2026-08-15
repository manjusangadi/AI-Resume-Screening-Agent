import os
import json
import re
from typing import Dict, Any, List
from groq import Groq
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def parse_json_safely(raw_text: str) -> Dict[str, Any]:
    """
    Extracts and parses a JSON object from raw LLM output.
    Handles markdown blocks (e.g. ```json ... ```), leading/trailing text,
    and returns a clean Python dictionary.
    """
    cleaned = raw_text.strip()
    
    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```(?:json)?\n|```$', '', cleaned, flags=re.MULTILINE).strip()
        
    # Extract outer-most braces in case of conversational wrapper text
    brace_start = cleaned.find('{')
    brace_end = cleaned.rfind('}')
    
    if brace_start != -1 and brace_end != -1:
        cleaned = cleaned[brace_start:brace_end + 1]
        
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[!] JSON parsing failed for raw output:\n{raw_text}\nError: {e}")
        raise ValueError(f"Failed to parse structured JSON from LLM: {str(e)}")

class GroqService:
    def __init__(self, api_key: str = None):
        """
        Initializes the Groq client.
        Uses GROQ_API_KEY from parameter, .env, or system environment.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
    def is_available(self) -> bool:
        """Returns True if a Groq API key is configured."""
        return bool(self.api_key)
        
    def _call_groq(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """
        Executes a call to the Groq API.
        Includes robust error handling for missing keys, network errors, and rate limits.
        """
        if not self.is_available():
            raise ValueError("Groq API key is not configured. Set GROQ_API_KEY in the environment or .env file.")
            
        client = Groq(api_key=self.api_key)
        
        extra_args = {}
        if json_mode:
            extra_args["response_format"] = {"type": "json_object"}
            
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1 if json_mode else 0.3,
                **extra_args
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[!] Groq API call error: {e}")
            raise RuntimeError(f"Groq API Error: {str(e)}")

    def analyze_job_description(self, jd_text: str) -> Dict[str, Any]:
        """
        Uses Groq LLM to extract structured requirements from the Job Description.
        """
        system_prompt = """
            You are an expert AI recruiter parsing a Job Description.
            Extract the requirements and return a valid JSON object with the following schema:
            {
            "job_title": "string or empty",
            "required_skills": ["list of strings"],
            "preferred_skills": ["list of strings"],
            "minimum_experience": integer (default 0 if not specified),
            "maximum_experience": integer or null,
            "education_requirements": ["list of strings"],
            "responsibilities": ["list of strings"],
            "keywords": ["list of key terms/technologies"]
            }

            Respond ONLY with the raw JSON object. Do not include conversational wrapper, introductory explanation or markdown code fences.
        """
        
        user_prompt = f"Job Description:\n\n{jd_text}"
        
        response_text = self._call_groq(system_prompt, user_prompt, json_mode=True)
        return parse_json_safely(response_text)

    def generate_candidate_reasoning(self, jd_requirements: Dict[str, Any], cand_info: Dict[str, Any], scores: Dict[str, Any]) -> str:
        """
        Generates a professional recruiter analysis paragraph for a candidate.
        If suitable, includes a specific Groq Llama-3.1 citation.
        """
        system_prompt = "You are a professional recruitment advisor. Provide objective candidate evaluation as a single cohesive paragraph."
        
        user_prompt = f"""
        Job Description Requirements:
            - Skills: {jd_requirements.get('required_skills', [])}
            - Min Experience: {jd_requirements.get('min_experience', 0)} years
            - Min Education: {jd_requirements.get('required_education', 'Bachelor')}

        Candidate Profile:
            - Name: {cand_info['name']}
            - Extracted Skills: {cand_info['skills']}
            - Experience: {cand_info['years_of_experience']} years
            - Education: {cand_info['education']}
            - Matching Skills: {scores['matching_skills']}
            - Missing Required Skills: {scores['missing_skills']}
            - Match Score: {scores['final_score']}% (Tier: {scores['tier']})

        Write a professional recruitment analysis for this candidate.
        The analysis must be a single cohesive paragraph (around 4-6 sentences) summarizing:
        1. Key strengths and experience comparison.
        2. Matching skills and missing/weak skills.
        3. A clear hiring recommendation (proceed, skip, hold) matching their Score of {scores['final_score']}% and Tier of {scores['tier']}.

        If the candidate is suitable (Tier is Good Match or Outstanding Match), describe their strong points, and you MUST explicitly state in the paragraph: "Groq's Llama-3.1 LLM was used to generate this suitability assessment."
        If the candidate is not suitable, describe their skill/experience gaps and recommend not proceeding.

        Do not write any markdown bullets, lists, headings, or conversational intros. Just output the single clean paragraph."""
        
        content = self._call_groq(system_prompt, user_prompt, json_mode=False)
        # Ensure it fits the bullet list format of the UI
        if not content.startswith("-"):
            content = f"- **Groq Llama-3.1 Suitability Report**: {content}"
        return content

    def improve_resume(self, resume_text: str, job_description: str, candidate_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides ATS optimization tips and resume improvements based on candidate performance.
        Strictly respects the Honesty Rule (no fabrication).
        """
        system_prompt = """
        You are an expert ATS (Applicant Tracking System) optimizer and professional resume writer.
        Evaluate the candidate's resume against the Job Description and provide constructive, honest suggestions for improvement.

        CRITICAL HONESTY RULE:
        - NEVER invent or fabricate fake work experience, fake projects, fake certifications, fake skills, fake education, or fake achievements.
        - Do not make up achievements or fake metrics/numbers.
        - If suggesting a rewrite for a project or experience, base it ONLY on existing information in their profile, and label it clearly as: "Example rewrite based only on existing information".
        - If the candidate is missing a required skill, say: "Learn this skill and add it to your resume only after gaining genuine knowledge or experience."

        Return a valid JSON object with the following schema:
        {
            "current_match_summary": "One or two sentences summarizing their current fit.",
            "strengths": ["list of existing strengths found in their resume"],
            "missing_or_weak_areas": ["list of areas they need to improve or learn"],
            "keywords_to_highlight": ["list of keywords from the JD they have but should emphasize"],
            "resume_improvements": ["general layout/structure improvements"],
            "project_suggestions": ["practical projects they can build to gain missing skills"],
            "bullet_point_improvements": ["suggestions to improve their experience bullet points (e.g., action verbs)"],
            "ats_tips": ["ATS-specific formatting/parsing optimization tips"],
            "priority_action_plan": {
                "high": ["high priority actions they should take"],
                "medium": ["medium priority actions"],
                "low": ["low priority actions"]
            }
        }

        Respond ONLY with the JSON object. Do not add markdown code blocks or additional text.
        """

        user_prompt = f"""
        Job Description:
            {job_description}

        Candidate Profile Details:
            - Name: {candidate_result.get('name')}
            - Education: {candidate_result.get('education')}
            - Years of Experience: {candidate_result.get('years_of_experience')}
            - Skills Extracted: {candidate_result.get('skills')}
            - Matching Skills: {candidate_result.get('matching_skills')}
            - Missing Required Skills: {candidate_result.get('missing_skills')}
            - Match Score: {candidate_result.get('final_score')}%

        Raw Resume Text:
            {resume_text}
        """

        response_text = self._call_groq(system_prompt, user_prompt, json_mode=True)
        return parse_json_safely(response_text)
