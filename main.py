import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai

DEFAULT_PORTFOLIO_DATA = {
    "name": "",
    "headline": "",
    "professional_summary": "",
    "skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "achievements": [],
    "contact": {
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "other_links": [],
    },
}

def clean_resume_text(raw_text: str) -> str:
    """Cleans raw text by removing extra spaces and weird characters."""
    cleaned_text = re.sub(r'[\r\t]', ' ', raw_text)
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    return cleaned_text.strip()

def get_resume_input() -> str:
    """Asks the user how they want to provide their resume content."""
    print("How would you like to enter your resume?")
    print("1. Read from 'resume.txt'")
    print("2. Paste/Type raw text directly")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        file_path = "resume.txt"
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found!")
            return ""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
            
    elif choice == "2":
        print("\nPaste your resume text below (Press Enter, then Ctrl+D or Ctrl+Z and hit Enter to finish):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        return "\n".join(lines)
    else:
        print("Invalid choice.")
        return ""

def configure_gemini():
    """Loads the API key and sets up the Gemini model."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
        exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

def build_prompt(cleaned_text: str) -> str:
    """Builds the strict instruction prompt sent to Gemini."""
    schema = """
    {
        "name": "",
        "headline": "",
        "professional_summary": "",
        "skills": [],
        "education": [{"degree": "", "institution": "", "duration": ""}],
        "experience": [{"role": "", "company": "", "duration": "", "responsibilities": []}],
        "projects": [{"title": "", "description": "", "technologies": []}],
        "achievements": [],
        "contact": {"email": "", "phone": "", "linkedin": "", "github": "", "other_links": []}
    }
    """

    return f"""You are extracting structured portfolio data from a resume.
        Rules:
        - Use ONLY information explicitly present in the resume text below.
        - Do NOT invent or assume any skills, experience, projects, companies, dates, achievements, or links.
        - If information is not present, use an empty string "" or empty list [].
        - Keep the professional summary concise (2-3 sentences) and strictly factual.
        - Respond with VALID JSON ONLY. No markdown code fences, no explanations, no extra text.

        Return JSON matching exactly this structure:
        {schema}

        ---RESUME START---
        {cleaned_text}
        ---RESUME END---
        """

def call_gemini(model, prompt: str) -> str:
    """Sends the prompt to Gemini and returns the raw text response."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error: Could not reach Gemini API. Details: {e}")
        exit(1)

def parse_and_validate_json(raw_response: str) -> dict:
    """Cleans raw API response, converts JSON to Python dictionary safely, and handles missing values."""
    if not raw_response:
        print(
            "Warning: Empty response received. Using default empty portfolio structure."
        )
        return DEFAULT_PORTFOLIO_DATA.copy()

    
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            print(
                "Warning: Parsed output is not a JSON object. Reverting to empty structure."
            )
            return DEFAULT_PORTFOLIO_DATA.copy()
    except (json.JSONDecodeError, TypeError) as e:
        print(
            f"Error parsing JSON from Gemini: {e}. Reverting to default empty values."
        )
        return DEFAULT_PORTFOLIO_DATA.copy()

    
    validated_data = DEFAULT_PORTFOLIO_DATA.copy()
    for key, default_val in DEFAULT_PORTFOLIO_DATA.items():
        val = data.get(key)
        if val is not None:
            validated_data[key] = val

    
    contact_data = validated_data.get("contact", {})
    if not isinstance(contact_data, dict):
        contact_data = {}

    validated_data["contact"] = {
        "email": contact_data.get("email", ""),
        "phone": contact_data.get("phone", ""),
        "linkedin": contact_data.get("linkedin", ""),
        "github": contact_data.get("github", ""),
        "other_links": contact_data.get("other_links", []),
    }

    return validated_data

if __name__ == "__main__":
    raw_content = get_resume_input()
    
    if raw_content:
        cleaned_resume = clean_resume_text(raw_content)
        print("\n--- Cleaned Resume Output ---")
        print(cleaned_resume)

        model = configure_gemini()
        prompt = build_prompt(cleaned_resume)
        raw_response = call_gemini(model, prompt)
        print("\n--- Portfolio Data from API---")
        print(raw_response)
        
        portfolio_data = parse_and_validate_json(raw_response)

        print("\n--- Parsed Python Dictionary (Ready for HTML Template) ---")
        print(portfolio_data)