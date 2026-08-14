# AI-Resume-Screening-Agent 🔍🤖

**AI-Resume-Screening-Agent — Junior AI Research Associate Selection Round (Intermediate Category)**

This repository contains a production-grade, end-to-end **AI-Powered Resume Screening Agent** built to parse multi-format resume files (`.pdf`, `.docx`, `.txt`), extract structured fields (candidate metadata, skills, experience, education), calculate weighted suitability ratings against a job description, and output sorted rankings.

---

## 🎯 One-Sentence Job Description
> "My agent takes a job description and a directory of resumes (PDF, DOCX, or TXT) and produces a ranked list of candidates with a detailed multi-category match score and descriptive recruitment reasoning."

---

## 💎 Key Features

1. **Multi-Format Parsing**: Built-in parsers for `.pdf` (via `pypdf`), `.docx` (via `python-docx`), and `.txt` files.
2. **Double Interface Execution**:
   - **Interactive CLI**: Instantly screens and prints a clean ASCII table of ranks, scores, and details directly in the console, saving results to `output/`.
   - **Premium Web Dashboard**: A gorgeous, glassmorphic dark-themed single-page app displaying stats, metrics progress bars, color-coded tier tags, matching/missing skill cloud pills, and recruiter-ready reasoning.
3. **Hybrid NLP Similarity Engine**: Built from scratch in pure Python, tokenizing, filtering stopwords, and executing TF-IDF vectorization and Cosine Similarity computations.
4. **4-Tier Weighted Suitability Scorer**:
   - **40% Skill Match**: Counts matching skills against job description technical requirements.
   - **30% NLP Semantic Match**: Multi-document TF-IDF cosine similarity percentage.
   - **20% Experience Match**: Compares candidate's years of experience against the job's minimum requirement.
   - **10% Education Match**: Mathematical degree ranking comparison (PhD > Master > Bachelor > Associate > None).
5. **Real-time AI Features via Groq**:
   - **Analyze JD with AI**: Instantly extracts job title, experience bounds, education needs, required/preferred skills, and responsibilities in a structured view.
   - **Improve Resume with AI**: Evaluates ATS compatibility and recommends resume optimizations. Strictly adheres to the **Honesty Rule**: it *never* invents achievements or fake skills. Missing skills are flagged with advice to acquire actual experience before listing them.
6. **Double Intelligence Mode**:
   - **Heuristic Mock Engine (Offline-First)**: Runs completely offline without API keys, using custom regex, token dictionaries, and heuristic scoring. Excellent for quick, foolproof evaluations.
   - **Groq AI Engine**: Leverages the high-speed Groq API (utilizing Llama-3.3-70b-versatile in JSON Mode) to extract high-accuracy structured fields and compile natural language recruiter reasoning summaries.

---

## 📁 Project Structure

```
AI-Resume-Screening-Agent/
│
├── data/
│   ├── resumes/                # Directory containing candidates' resumes
│   └── job_description.txt     # Target Job Description file
│
├── src/
│   ├── parser.py               # Text extraction and cleaning for PDF, DOCX, and TXT
│   ├── extractor.py            # Feature extraction (Heuristics & Groq)
│   ├── similarity.py           # Pure Python TF-IDF and Cosine Similarity
│   ├── scorer.py               # Weighted matching score calculator
│   ├── agent.py                # Pipeline orchestrator
│   └── groq_service.py         # Groq client wrapper, JSON parsing & prompt templates
│
├── static/
│   ├── index.html              # Dashboard frontend HTML
│   ├── style.css               # HSL-based dark glassmorphic styling
│   └── app.js                  # Frontend API bindings and rendering logic
│
├── output/
│   ├── ranked_candidates.csv   # Structured shortlisting report
│   └── results.json            # Deep metadata for UI rendering
│
├── generate_samples.py         # Script to auto-populate 11 test files
├── requirements.txt            # Python dependencies (Flask, groq, python-dotenv, etc.)
├── README.md                   # Instructions and documentation
├── app.py                      # Flask server (Backend API)
└── main.py                     # CLI Entry point
```

---

## 🚀 Foolproof Installation & Setup

Ensure you have **Python 3.8+** installed. In your terminal, run the following commands:

```bash
# 1. Navigate to the project directory
cd "AI-Resume-Screening-Agent"

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
# On Unix/macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 🏃 Execution Options

### Option A: Run Interactive CLI (Command-line)
Run the script below to parse the resumes, perform calculations, and render the sorted ASCII rankings shortlist in your console. It will automatically save `output/ranked_candidates.csv` and `output/results.json`.

```bash
# Default Offline Heuristic Mode
python main.py --provider mock

# Groq LLM Mode (utilizes GROQ_API_KEY from environment or .env file)
python main.py --provider groq
```

### Option B: Run Web Dashboard GUI
Start the local Flask server. It will **automatically ensure that sample candidate resumes and the job description are generated** if the folders are empty:

```bash
python app.py
```
Open your web browser and navigate to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**. 
- You can review and edit the Job Description.
- You can click **Analyze JD with AI** to extract structured job parameters.
- You can drag-and-drop new candidate resumes (`.pdf`, `.docx`, `.txt`) into the drop zone.
- Select your intelligence backend (Mock or Groq Llama-3) and hit **Run Screening Pipeline** to view the results interactively!
- Expand candidate cards to view detailed breakdowns, matching/missing skill cloud badges, suitability reasoning, and run **Improve Resume with AI** to get personalized feedback.
- Download the generated reports by clicking **Export CSV** and **Export JSON**.

---

## ⚙️ Configuration & API Keys
No API key is required to test this application. The project includes a robust **Heuristic Mode** which parses text, matches skills from an extensive tech dictionary, estimates experience and education ranks using regular expressions, and generates automated strengths/gaps bullet points.

To test LLM-enabled intelligence, create a `.env` file in the workspace root with the following configuration:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## 🧠 Design Choices & Engineering Trade-offs

### 1. Pure Python TF-IDF and Cosine Similarity
- **Choice**: Instead of using heavy packages like `scikit-learn` or `numpy` (which compile C-extensions and frequently cause dependency conflicts or platform failures on Windows), we implemented TF-IDF vectorization and Cosine Similarity entirely in pure Python.
- **Trade-off**: For small-to-medium datasets (e.g. 10–100 resumes), the pure Python implementation is extremely fast, fully customizable, and guarantees 100% cross-platform reproducibility with zero compilation risks.

### 2. Custom Regex & Heuristic Fallbacks
- **Choice**: Built a fallback regex extractor in `src/extractor.py` that parses degrees, matches technical skills from a 60+ word dictionary, and aggregates years of experience from career date ranges.
- **Trade-off**: The heuristic parser is highly robust and operates offline. While it may occasionally misinterpret unstructured date formats (e.g. counting overlapping internships twice), it ensures the system remains functional when third-party LLM APIs are unavailable or when reviewer credentials are not set.

### 3. Glassmorphic Vanilla CSS Design system
- **Choice**: Styled the frontend dashboard with vanilla CSS custom properties using HSL colors and glassmorphic backdrop filters, avoiding CSS frameworks like Tailwind.
- **Trade-off**: This approach results in a fast dashboard with zero build steps or package-bundling overhead, rendering clean responsive panels, timeline progress bars, and hover animations immediately on page load.
