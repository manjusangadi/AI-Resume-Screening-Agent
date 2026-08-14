import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env
load_dotenv()

# Add current directory to path to ensure src can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import ResumeScreeningAgent

def print_banner():
    banner = """
============================================================
                 AI-RESUME-SCREENING-AGENT                  
       Evaluating Suitability, Rankings & AI Reasoning       
============================================================
"""
    print(banner)

def print_ascii_table(candidates):
    """Renders a beautifully formatted ASCII table of candidate ranks."""
    if not candidates:
        print("No candidates found or scored.")
        return
        
    print("\nRANKINGS SHORTLIST:")
    print("+" + "-"*4 + "+" + "-"*22 + "+" + "-"*13 + "+" + "-"*15 + "+" + "-"*10 + "+")
    print("| " + "Rank".ljust(2) + " | " + "Candidate Name".ljust(20) + " | " + "Match Score".ljust(11) + " | " + "Match Tier".ljust(13) + " | " + "Experience".ljust(8) + " |")
    print("+" + "-"*4 + "+" + "-"*22 + "+" + "-"*13 + "+" + "-"*15 + "+" + "-"*10 + "+")
    
    for rank, cand in enumerate(candidates, 1):
        name_str = cand["name"][:20].ljust(20)
        score_str = f"{cand['final_score']}%".rjust(10).ljust(11)
        tier_str = cand["tier"][:13].ljust(13)
        exp_str = f"{cand['years_of_experience']} yrs".rjust(7).ljust(8)
        
        print(f"| {str(rank).ljust(2)} | {name_str} | {score_str} | {tier_str} | {exp_str} |")
        
    print("+" + "-"*4 + "+" + "-"*22 + "+" + "-"*13 + "+" + "-"*15 + "+" + "-"*10 + "+")
    print("\nDetailed Reasoning for top candidates:")
    
    # Print detailed reasoning for top 3 candidates
    for rank, cand in enumerate(candidates[:3], 1):
        print(f"\n{rank}. {cand['name']} (Score: {cand['final_score']}%)")
        print("-" * (len(cand['name']) + 16))
        print(f"Skills Score: {cand['skill_score']}% | NLP Score: {cand['nlp_score']}% | Exp Score: {cand['experience_score']}% | Edu Score: {cand['education_score']}%")
        print(f"Matching Skills: {', '.join(cand['matching_skills'])}")
        if cand['missing_skills']:
            print(f"Missing Required Skills: {', '.join(cand['missing_skills'])}")
        print("Recruiter/AI Summary:")
        # Indent reasoning
        for line in cand['reasoning'].split('\n'):
            print(f"  {line}")

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="AI-Resume-Screening-Agent CLI")
    parser.add_argument("--provider", default="mock", choices=["mock", "groq"], help="AI Provider to use (choices: mock, groq)")
    parser.add_argument("--key", default="", help="Groq API Key (overrides environment variable)")
    parser.add_argument("--resumes", default="data/resumes", help="Directory containing resumes (default: data/resumes)")
    parser.add_argument("--jd", default="data/job_description.txt", help="Path to Job Description file (default: data/job_description.txt)")
    parser.add_argument("--output", default="output", help="Directory for outputs (default: output)")
    
    args = parser.parse_args()
    
    # Path validations
    if not os.path.exists(args.jd):
        print(f"[!] Error: Job Description file not found at '{args.jd}'")
        sys.exit(1)
        
    if not os.path.exists(args.resumes):
        print(f"[!] Error: Resumes directory not found at '{args.resumes}'")
        sys.exit(1)
        
    # Instantiate agent
    api_key = args.key or os.getenv("GROQ_API_KEY")
    agent = ResumeScreeningAgent(provider=args.provider, api_key=api_key)
    
    print(f"[*] Starting resume screening pipeline using provider: '{agent.provider.upper()}'")
    print(f"[*] Job Description: {args.jd}")
    print(f"[*] Resumes Directory: {args.resumes}")
    
    try:
        results = agent.screen_resumes(
            resumes_dir=args.resumes,
            jd_filepath=args.jd,
            output_dir=args.output
        )
        
        print(f"\n[+] Pipeline completed. Screened {len(results)} resumes.")
        print_ascii_table(results)
        
    except Exception as e:
        print(f"\n[!] Error during screening: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
