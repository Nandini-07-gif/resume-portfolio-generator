import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
import re
from datetime import datetime

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


"""
Portfolio Generator Module
Handles generating portfolio.html from JSON data
"""


def remove_section(html_content, section_id):
    """
    Remove an entire section from HTML if it has no content
    
    Args:
        html_content (str): HTML content
        section_id (str): ID of section to remove
    
    Returns:
        str: HTML content with section removed
    """
    # Pattern to match entire section including its content
    pattern = r'<section id="' + section_id + r'">.*?</section>'
    html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)
    return html_content


def generate_html(data):
    """
    Generate portfolio.html from JSON data using template.html
    
    Args:
        data (dict): Parsed JSON data from Gemini
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read template
        print("📄 Reading template.html...")
        with open('template.html', 'r', encoding='utf-8') as file:
            html_template = file.read()
        
        # Replace basic information
        html_content = html_template
        
        # Handle different field names
        heading = data.get('heading', data.get('headline', 'Professional'))
        
        html_content = html_content.replace('{NAME}', data.get('name', 'Not Specified'))
        html_content = html_content.replace('{HEADING}', heading)
        html_content = html_content.replace('{SUMMARY}', data.get('professional_summary', data.get('summary', '')))
        html_content = html_content.replace('{DATE}', datetime.now().strftime('%B %d, %Y'))
        
        # ----- 1. CONTACT & LINKS SECTION -----
        print("📋 Processing contact section...")
        contact = data.get('contact', {})
        if contact and any(contact.values()):
            contact_html = ''
            
            if contact.get('email'):
                contact_html += f"""
                <div class="contact-item">
                    <i class="fas fa-envelope"></i>
                    <a href="mailto:{contact['email']}">{contact['email']}</a>
                </div>"""
            
            if contact.get('phone'):
                contact_html += f"""
                <div class="contact-item">
                    <i class="fas fa-phone"></i>
                    <a href="tel:{contact['phone']}">{contact['phone']}</a>
                </div>"""
            
            if contact.get('linkedin'):
                linkedin_url = contact['linkedin']
                if not linkedin_url.startswith('http'):
                    linkedin_url = 'https://' + linkedin_url
                contact_html += f"""
                <div class="contact-item">
                    <i class="fab fa-linkedin"></i>
                    <a href="{linkedin_url}" target="_blank">LinkedIn</a>
                </div>"""
            
            if contact.get('github'):
                github_url = contact['github']
                if not github_url.startswith('http'):
                    github_url = 'https://' + github_url
                contact_html += f"""
                <div class="contact-item">
                    <i class="fab fa-github"></i>
                    <a href="{github_url}" target="_blank">GitHub</a>
                </div>"""
            
            if contact.get('website'):
                website_url = contact['website']
                if not website_url.startswith('http'):
                    website_url = 'https://' + website_url
                contact_html += f"""
                <div class="contact-item">
                    <i class="fas fa-globe"></i>
                    <a href="{website_url}" target="_blank">Website</a>
                </div>"""
            
            html_content = html_content.replace('{CONTACT_CONTENT}', contact_html)
        else:
            print("   ℹ️ No contact information found - hiding section")
            html_content = remove_section(html_content, 'contact')
        
        # ----- 2. SKILLS SECTION -----
        print("🛠️ Processing skills section...")
        skills_list = data.get('skills', [])
        if skills_list and len(skills_list) > 0:
            skills_html = ''
            for skill in skills_list:
                skills_html += f'<span class="skill-tag">{skill}</span>\n                '
            html_content = html_content.replace('{SKILLS_CONTENT}', skills_html)
            print(f"   ✅ Found {len(skills_list)} skills")
        else:
            print("   ℹ️ No skills found - hiding section")
            html_content = remove_section(html_content, 'skills')
        
        # ----- 3. EXPERIENCE SECTION -----
        print("💼 Processing experience section...")
        experience_list = data.get('experience', [])
        if experience_list and len(experience_list) > 0:
            exp_html = ''
            for exp in experience_list:
                # Handle both 'role' and 'title' fields
                role = exp.get('role', exp.get('title', ''))
                company = exp.get('company', '')
                
                # Handle responsibilities
                responsibilities = exp.get('responsibilities', [])
                if isinstance(responsibilities, list) and responsibilities:
                    resp_text = ' | '.join(responsibilities)
                else:
                    resp_text = exp.get('description', '')
                
                exp_html += f"""
                <div class="experience-item">
                    <h3>{role} at {company}</h3>
                    <p class="date">{exp.get('duration', exp.get('dates', ''))}</p>
                    <p class="description">{resp_text}</p>
                </div>
                """
            html_content = html_content.replace('{EXPERIENCE_CONTENT}', exp_html)
            print(f"   ✅ Found {len(experience_list)} experience entries")
        else:
            print("   ℹ️ No experience found - hiding section")
            html_content = remove_section(html_content, 'experience')
        
        # ----- 4. EDUCATION SECTION -----
        print("🎓 Processing education section...")
        education_list = data.get('education', [])
        if education_list and len(education_list) > 0:
            edu_html = ''
            for edu in education_list:
                edu_html += f"""
                <div class="education-item">
                    <h3>{edu.get('degree', '')}</h3>
                    <p class="institution">{edu.get('institution', '')}</p>
                    <p class="date">{edu.get('duration', edu.get('year', ''))}</p>
                </div>
                """
            html_content = html_content.replace('{EDUCATION_CONTENT}', edu_html)
            print(f"   ✅ Found {len(education_list)} education entries")
        else:
            print("   ℹ️ No education found - hiding section")
            html_content = remove_section(html_content, 'education')
        
        # ----- 5. PROJECTS SECTION -----
        print("🚀 Processing projects section...")
        projects_list = data.get('projects', [])
        if projects_list and len(projects_list) > 0:
            projects_html = ''
            for project in projects_list:
                # Handle both 'title' and 'name' fields
                project_name = project.get('title', project.get('name', ''))
                project_desc = project.get('description', '')
                
                techs = project.get('technologies', [])
                tech_html = ''
                if techs and len(techs) > 0:
                    tech_html = '<div class="technologies">'
                    for tech in techs:
                        tech_html += f'<span class="tech-tag">{tech}</span>'
                    tech_html += '</div>'
                
                projects_html += f"""
                <div class="project-item">
                    <h3>{project_name}</h3>
                    <p class="description">{project_desc}</p>
                    {tech_html}
                </div>
                """
            html_content = html_content.replace('{PROJECTS_CONTENT}', projects_html)
            print(f"   ✅ Found {len(projects_list)} projects")
        else:
            print("   ℹ️ No projects found - hiding section")
            html_content = remove_section(html_content, 'projects')
        
        # ----- 6. ACHIEVEMENTS SECTION (FIXED) -----
        print("🏆 Processing achievements section...")
        achievements_list = data.get('achievements', [])
        if achievements_list and len(achievements_list) > 0:
            achievements_html = ''
            for achievement in achievements_list:
                # ✅ FIX: Check if achievement is a string or dictionary
                if isinstance(achievement, str):
                    # If it's a string, display it directly
                    achievements_html += f"""
                    <div class="achievement-item">
                        <h3>🏅 {achievement}</h3>
                    </div>
                    """
                elif isinstance(achievement, dict):
                    # If it's a dictionary, extract fields
                    title = achievement.get('title', achievement.get('name', ''))
                    description = achievement.get('description', '')
                    year = achievement.get('year', '')
                    
                    achievements_html += f"""
                    <div class="achievement-item">
                        <h3>{title}</h3>
                        <p class="description">{description}</p>
                        <p class="date">{year}</p>
                    </div>
                    """
                else:
                    # Fallback for any other type
                    achievements_html += f"""
                    <div class="achievement-item">
                        <h3>{str(achievement)}</h3>
                    </div>
                    """
            
            html_content = html_content.replace('{ACHIEVEMENTS_CONTENT}', achievements_html)
            print(f"   ✅ Found {len(achievements_list)} achievements")
        else:
            print("   ℹ️ No achievements found - hiding section")
            html_content = remove_section(html_content, 'achievements')
        
        # Remove any remaining placeholders
        html_content = html_content.replace('{CONTACT_CONTENT}', '')
        html_content = html_content.replace('{SKILLS_CONTENT}', '')
        html_content = html_content.replace('{EXPERIENCE_CONTENT}', '')
        html_content = html_content.replace('{EDUCATION_CONTENT}', '')
        html_content = html_content.replace('{PROJECTS_CONTENT}', '')
        html_content = html_content.replace('{ACHIEVEMENTS_CONTENT}', '')
        
        # Clean up extra whitespace
        html_content = re.sub(r'\n\s*\n', '\n', html_content)
        
        # Write to file
        print("💾 Saving portfolio.html...")
        with open('portfolio.html', 'w', encoding='utf-8') as file:
            file.write(html_content)
        
        print("✅ portfolio.html generated successfully!")
        return True
        
    except FileNotFoundError:
        print("❌ Error: template.html not found!")
        print("📝 Please make sure template.html exists in the same directory.")
        return False
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        return False
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
        
        generate_html(portfolio_data)
