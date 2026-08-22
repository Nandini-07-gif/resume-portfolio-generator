import os
import re
import json
import sys
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from dotenv import load_dotenv

# Base directory of the script file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Reconfigure stdout to utf-8 if possible for Windows terminal compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Safe import for google.generativeai
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    genai = None
    HAS_GEMINI = False

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

SAMPLE_PORTFOLIO_DATA = {
    "name": "Nandini Saraswat",
    "headline": "Computer Science Student | Web Development Intern",
    "professional_summary": "First-year Computer Science undergraduate specializing in AI, Analytics, and Full-Stack Web Development. Experienced in building Python backends, web applications, and predictive machine learning models.",
    "skills": ["Python", "Java", "SQL", "HTML/CSS", "JavaScript", "Flask", "React", "Vite", "Git", "MySQL", "Gemini API", "Public Speaking", "Team Coordination", "Event Management"],
    "education": [{"degree": "Bachelor of Technology in Computer Science (AI & Analytics)", "institution": "GLA University, Mathura", "duration": "2025 - Present"}],
    "experience": [{"role": "Web Development Intern", "company": "Infosys Prodigy", "duration": "2025", "responsibilities": ["Developed responsive web interfaces and assisted with backend features.", "Collaborated on web application features using modern HTML, CSS, and JavaScript."]}],
    "projects": [
        {"title": "Zenith 2", "description": "Project Management & Collaboration Platform built using Python and Flask.", "technologies": ["Python", "Flask", "SQL"]},
        {"title": "AI Insurance Claim Verification Agent", "description": "Automated verification system using public registries to validate claim data.", "technologies": ["Python", "Gemini API"]}
    ],
    "achievements": ["Overall Coordinator, College Hackathon (2025)", "Founder / Team Lead, Aashayein Social Cause Club"],
    "contact": {"email": "contact@example.com", "phone": "", "linkedin": "linkedin.com/in/example", "github": "github.com/example", "other_links": []}
}

THEME_MAP = {
    "1": ("theme-glassmorphism", "Glassmorphism Creative"),
    "2": ("theme-cyberpunk", "White Modern Editorial"),
    "3": ("theme-terminal", "Developer Terminal"),
    "4": ("theme-minimalist", "Modern Minimalist"),
}

def clean_resume_text(raw_text: str) -> str:
    """Cleans raw text by removing extra spaces and weird characters."""
    cleaned_text = re.sub(r'[\r\t]', ' ', raw_text)
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    return cleaned_text.strip()

def configure_gemini():
    """Loads the API key and sets up the Gemini model."""
    if not HAS_GEMINI:
        return None
    env_path = os.path.join(BASE_DIR, ".env")
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None

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
        print(f"[ERROR] Could not reach Gemini API. Details: {e}")
        return ""

def parse_and_validate_json(raw_response: str) -> dict:
    """Cleans raw API response, converts JSON to Python dictionary safely, and handles missing values."""
    if not raw_response:
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
            return DEFAULT_PORTFOLIO_DATA.copy()
    except (json.JSONDecodeError, TypeError):
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

def remove_section(html_content, section_id):
    """Remove an entire section from HTML if it has no content"""
    pattern = r'<section id="' + section_id + r'">.*?</section>'
    return re.sub(pattern, '', html_content, flags=re.DOTALL)

def generate_html(data, theme_class="theme-glassmorphism"):
    """Generate portfolio.html from JSON data using template.html and chosen theme_class"""
    try:
        template_file = os.path.join(BASE_DIR, 'template.html')
        with open(template_file, 'r', encoding='utf-8') as file:
            html_template = file.read()
        
        html_content = html_template.replace('{THEME_CLASS}', theme_class)
        heading = data.get('heading', data.get('headline', 'Professional'))
        
        html_content = html_content.replace('{NAME}', data.get('name', 'Not Specified'))
        html_content = html_content.replace('{HEADING}', heading)
        html_content = html_content.replace('{SUMMARY}', data.get('professional_summary', data.get('summary', '')))
        html_content = html_content.replace('{DATE}', datetime.now().strftime('%B %d, %Y'))
        
        # 1. Contact Section
        contact = data.get('contact', {})
        if contact and any(contact.values()):
            contact_html = ''
            if contact.get('email'):
                contact_html += f'<div class="contact-item"><i class="fas fa-envelope"></i><a href="mailto:{contact["email"]}">{contact["email"]}</a></div>'
            if contact.get('phone'):
                contact_html += f'<div class="contact-item"><i class="fas fa-phone"></i><a href="tel:{contact["phone"]}">{contact["phone"]}</a></div>'
            if contact.get('linkedin'):
                l_url = contact['linkedin'] if contact['linkedin'].startswith('http') else 'https://' + contact['linkedin']
                contact_html += f'<div class="contact-item"><i class="fab fa-linkedin"></i><a href="{l_url}" target="_blank">LinkedIn</a></div>'
            if contact.get('github'):
                g_url = contact['github'] if contact['github'].startswith('http') else 'https://' + contact['github']
                contact_html += f'<div class="contact-item"><i class="fab fa-github"></i><a href="{g_url}" target="_blank">GitHub</a></div>'
            html_content = html_content.replace('{CONTACT_CONTENT}', contact_html)
        else:
            html_content = remove_section(html_content, 'contact')
        
        # 2. Skills Section
        skills_list = data.get('skills', [])
        if skills_list:
            skills_html = ''.join([f'<span class="skill-tag">{s}</span>\n' for s in skills_list])
            html_content = html_content.replace('{SKILLS_CONTENT}', skills_html)
        else:
            html_content = remove_section(html_content, 'skills')
        
        # 3. Experience Section
        experience_list = data.get('experience', [])
        if experience_list:
            exp_html = ''
            for exp in experience_list:
                role = exp.get('role', exp.get('title', ''))
                company = exp.get('company', '')
                resps = exp.get('responsibilities', [])
                resp_text = ' | '.join(resps) if isinstance(resps, list) and resps else exp.get('description', '')
                exp_html += f'<div class="experience-item"><h3>{role} at {company}</h3><p class="date">{exp.get("duration", "")}</p><p class="description">{resp_text}</p></div>\n'
            html_content = html_content.replace('{EXPERIENCE_CONTENT}', exp_html)
        else:
            html_content = remove_section(html_content, 'experience')
        
        # 4. Education Section
        education_list = data.get('education', [])
        if education_list:
            edu_html = ''
            for edu in education_list:
                edu_html += f'<div class="education-item"><h3>{edu.get("degree", "")}</h3><p class="institution">{edu.get("institution", "")}</p><p class="date">{edu.get("duration", "")}</p></div>\n'
            html_content = html_content.replace('{EDUCATION_CONTENT}', edu_html)
        else:
            html_content = remove_section(html_content, 'education')
        
        # 5. Projects Section
        projects_list = data.get('projects', [])
        if projects_list:
            proj_html = ''
            for proj in projects_list:
                name = proj.get('title', proj.get('name', ''))
                desc = proj.get('description', '')
                techs = proj.get('technologies', [])
                t_html = '<div class="technologies">' + ''.join([f'<span class="tech-tag">{t}</span>' for t in techs]) + '</div>' if techs else ''
                proj_html += f'<div class="project-item"><h3>{name}</h3><p class="description">{desc}</p>{t_html}</div>\n'
            html_content = html_content.replace('{PROJECTS_CONTENT}', proj_html)
        else:
            html_content = remove_section(html_content, 'projects')
        
        # 6. Achievements Section
        achievements_list = data.get('achievements', [])
        if achievements_list:
            ach_html = ''
            for ach in achievements_list:
                if isinstance(ach, str):
                    ach_html += f'<div class="achievement-item"><h3>🏅 {ach}</h3></div>\n'
                elif isinstance(ach, dict):
                    ach_html += f'<div class="achievement-item"><h3>{ach.get("title","")}</h3><p class="description">{ach.get("description","")}</p><p class="date">{ach.get("year","")}</p></div>\n'
            html_content = html_content.replace('{ACHIEVEMENTS_CONTENT}', ach_html)
        else:
            html_content = remove_section(html_content, 'achievements')
        
        # Clean remaining placeholders & whitespace
        for placeholder in ['{CONTACT_CONTENT}', '{SKILLS_CONTENT}', '{EXPERIENCE_CONTENT}', '{EDUCATION_CONTENT}', '{PROJECTS_CONTENT}', '{ACHIEVEMENTS_CONTENT}']:
            html_content = html_content.replace(placeholder, '')
        html_content = re.sub(r'\n\s*\n', '\n', html_content)
        
        output_file = os.path.join(BASE_DIR, 'portfolio.html')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(html_content)
        
        return True
    except Exception as e:
        print(f"[ERROR] HTML Generation failed: {e}")
        return False

# ==========================================================
# WEB APPLICATION DASHBOARD HTML
# ==========================================================
WEB_APP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Resume-to-Portfolio Web Application</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #0b0f19; color: #f3f4f6; min-height: 100vh; padding: 30px 20px; }
        .app-container { max-width: 1250px; margin: 0 auto; }
        .app-header { text-align: center; margin-bottom: 35px; }
        .app-header h1 { font-size: 2.6em; font-weight: 800; background: linear-gradient(135deg, #a855f7, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        .app-header p { color: #9ca3af; font-size: 1.05em; }
        .grid-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        @media (max-width: 992px) { .grid-layout { grid-template-columns: 1fr; } }
        .card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 30px; backdrop-filter: blur(12px); box-shadow: 0 15px 35px rgba(0,0,0,0.3); }
        .card h2 { font-size: 1.3em; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; color: #38bdf8; justify-content: space-between; }
        .btn-action { background: linear-gradient(135deg, #3b82f6, #a855f7); color: #fff; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 0.88em; display: inline-flex; align-items: center; gap: 8px; text-decoration: none; }
        .btn-action:hover { opacity: 0.95; transform: translateY(-2px); }
        .btn-sample { background: linear-gradient(135deg, #f59e0b, #d97706); }
        textarea { width: 100%; height: 260px; background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; padding: 15px; color: #e5e7eb; font-family: inherit; font-size: 0.95em; line-height: 1.6; resize: vertical; margin-bottom: 20px; }
        textarea:focus { outline: none; border-color: #a855f7; box-shadow: 0 0 15px rgba(168, 85, 247, 0.3); }
        .theme-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 18px; }
        .theme-card { background: rgba(255, 255, 255, 0.03); border: 2px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 16px; cursor: pointer; transition: all 0.25s; text-align: left; position: relative; }
        .theme-card:hover { border-color: #38bdf8; transform: translateY(-3px); }
        .theme-card.active { border-color: #a855f7; background: rgba(168, 85, 247, 0.14); box-shadow: 0 0 20px rgba(168, 85, 247, 0.3); }
        .theme-card h3 { font-size: 1.02em; font-weight: 700; margin-bottom: 4px; color: #fff; }
        .theme-card p { font-size: 0.82em; color: #9ca3af; }
        .color-dots { display: flex; gap: 6px; margin-top: 8px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }

        .sample-preview-box { background: rgba(0, 0, 0, 0.35); border: 1px dashed rgba(168, 85, 247, 0.4); border-radius: 12px; padding: 16px; margin-bottom: 22px; }
        .sample-preview-box h4 { font-size: 0.95em; font-weight: 700; color: #a855f7; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
        .sample-preview-box p { font-size: 0.88em; color: #cbd5e1; line-height: 1.5; }

        .preview-box { height: 560px; width: 100%; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; overflow: hidden; background: #fff; }
        iframe { width: 100%; height: 100%; border: none; }
        .status-msg { margin-top: 15px; font-weight: 600; font-size: 0.95em; text-align: center; }
        .status-msg.success { color: #4ade80; }
        .status-msg.error { color: #f87171; }

        /* Download Dropdown */
        .dropdown-wrapper { position: relative; display: inline-block; }
        .btn-download-main { background: linear-gradient(135deg, #10b981, #059669); color: #fff; border: none; padding: 10px 20px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 0.9em; display: inline-flex; align-items: center; gap: 8px; transition: all 0.2s; }
        .btn-download-main:hover { opacity: 0.95; transform: translateY(-2px); }
        .dropdown-menu { display: none; position: absolute; right: 0; top: calc(100% + 6px); background: #1e293b; border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; min-width: 220px; box-shadow: 0 15px 40px rgba(0,0,0,0.5); z-index: 100; overflow: hidden; }
        .dropdown-menu.open { display: block; animation: fadeDown 0.2s ease; }
        @keyframes fadeDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
        .dropdown-item { display: flex; align-items: center; gap: 10px; padding: 13px 18px; color: #e2e8f0; cursor: pointer; transition: background 0.15s; font-size: 0.92em; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .dropdown-item:last-child { border-bottom: none; }
        .dropdown-item:hover { background: rgba(168, 85, 247, 0.15); }
        .dropdown-item i { width: 18px; text-align: center; }
        .dropdown-item .fmt-label { font-size: 0.75em; font-weight: 400; color: #94a3b8; margin-left: auto; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="app-header">
            <h1>✨ AI Resume-to-Portfolio Web Application</h1>
            <p>Type your own resume text or load sample data, choose a template theme, and download in your preferred format!</p>
        </div>

        <div class="grid-layout">
            <!-- Left Panel: User Text Area & Theme Options -->
            <div class="card">
                <h2>
                    <span><i class="fas fa-edit"></i> Resume Content</span>
                    <button class="btn-action btn-sample" onclick="loadSampleResume()"><i class="fas fa-file-download"></i> Load Sample from resume.txt</button>
                </h2>

                <textarea id="resumeInput" placeholder="Type or paste your own resume text here..."></textarea>

                <h2><i class="fas fa-palette"></i> Portfolio Design Theme</h2>
                <div class="theme-grid">
                    <div class="theme-card active" onclick="selectTheme('1', this)">
                        <h3>✨ Option 1</h3>
                        <p>Glassmorphism Creative</p>
                        <div class="color-dots"><span class="dot" style="background:#a855f7"></span><span class="dot" style="background:#38bdf8"></span><span class="dot" style="background:#0f0c29"></span></div>
                    </div>
                    <div class="theme-card" onclick="selectTheme('2', this)">
                        <h3>📰 Option 2</h3>
                        <p>White Modern Editorial</p>
                        <div class="color-dots"><span class="dot" style="background:#ffffff"></span><span class="dot" style="background:#dc2626"></span><span class="dot" style="background:#1c1917"></span></div>
                    </div>
                    <div class="theme-card" onclick="selectTheme('3', this)">
                        <h3>💻 Option 3</h3>
                        <p>Developer Terminal</p>
                        <div class="color-dots"><span class="dot" style="background:#0d1117"></span><span class="dot" style="background:#58a6ff"></span><span class="dot" style="background:#7ee787"></span></div>
                    </div>
                    <div class="theme-card" onclick="selectTheme('4', this)">
                        <h3>💼 Option 4</h3>
                        <p>Modern Minimalist</p>
                        <div class="color-dots"><span class="dot" style="background:#f8fafc"></span><span class="dot" style="background:#3b82f6"></span><span class="dot" style="background:#0f172a"></span></div>
                    </div>
                </div>

                <!-- Theme Contents Sample Info Box -->
                <div class="sample-preview-box">
                    <h4 id="sampleTitle"><i class="fas fa-info-circle"></i> Theme Contains (Option 1: Glassmorphism Creative)</h4>
                    <p id="sampleDesc">Vibrant purple & blue gradients with translucent frosted-glass panels, backdrop blur effects, glowing skill badges, and modern floating card animations.</p>
                </div>

                <div id="statusMessage" class="status-msg"></div>
            </div>

            <!-- Right Panel: Live Webpage Preview & Download Dropdown -->
            <div class="card">
                <h2>
                    <span><i class="fas fa-desktop"></i> Live Portfolio Preview</span>
                    <div style="display: flex; gap: 8px;">
                        <div class="dropdown-wrapper">
                            <button class="btn-download-main" onclick="toggleDropdown()"><i class="fas fa-download"></i> Download <i class="fas fa-chevron-down" style="font-size:0.7em"></i></button>
                            <div class="dropdown-menu" id="downloadDropdown">
                                <div class="dropdown-item" onclick="downloadAs('html')"><i class="fas fa-code" style="color:#38bdf8"></i> Download as HTML <span class="fmt-label">.html</span></div>
                                <div class="dropdown-item" onclick="downloadAs('pdf')"><i class="fas fa-file-pdf" style="color:#f87171"></i> Download as PDF <span class="fmt-label">.pdf</span></div>
                                <div class="dropdown-item" onclick="downloadAs('docx')"><i class="fas fa-file-word" style="color:#3b82f6"></i> Download as Word <span class="fmt-label">.doc</span></div>
                            </div>
                        </div>
                        <a href="/portfolio.html" target="_blank" class="btn-action"><i class="fas fa-external-link-alt"></i> Full Tab</a>
                    </div>
                </h2>
                <div class="preview-box">
                    <iframe id="portfolioPreview" src="/portfolio.html"></iframe>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedThemeChoice = "1";

        const themeSamples = {
            "1": {
                title: "Theme Contains (Option 1: Glassmorphism Creative)",
                desc: "Vibrant purple & blue ambient gradients, translucent frosted glass panels (backdrop-filter: blur), gradient badges, and floating card animations. Perfect for UI/UX & Creative Devs."
            },
            "2": {
                title: "Theme Contains (Option 2: White Modern Editorial)",
                desc: "Pure white canvas background, elegant serif Playfair Display headings, crimson red double lines, and newspaper-style quotes. Distinct magazine design."
            },
            "3": {
                title: "Theme Contains (Option 3: Developer Terminal)",
                desc: "Retro macOS-style CLI code editor window with red/yellow/green control buttons, monospace Fira Code font, dark syntax backdrop, and blinking cursor footer."
            },
            "4": {
                title: "Theme Contains (Option 4: Modern Minimalist)",
                desc: "Clean light slate background, Inter typography, crisp indigo badge tags, corporate section dividers, and clean executive card elevation."
            }
        };

        // Ensure portfolio is generated before any action
        async function ensureGenerated() {
            let resumeText = document.getElementById('resumeInput').value.trim();
            if (!resumeText) {
                try {
                    const res = await fetch('/api/get-resume');
                    resumeText = await res.text();
                } catch(e) {}
            }
            if (!resumeText) return false;
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resume_text: resumeText, theme_choice: selectedThemeChoice })
                });
                const result = await response.json();
                return result.success;
            } catch(e) { return false; }
        }

        async function selectTheme(choice, element) {
            selectedThemeChoice = choice;
            document.querySelectorAll('.theme-card').forEach(card => card.classList.remove('active'));
            element.classList.add('active');

            const sample = themeSamples[choice];
            if (sample) {
                document.getElementById('sampleTitle').innerHTML = '<i class="fas fa-info-circle"></i> ' + sample.title;
                document.getElementById('sampleDesc').innerText = sample.desc;
            }

            const ok = await ensureGenerated();
            if (ok) {
                document.getElementById('portfolioPreview').src = '/portfolio.html?t=' + new Date().getTime();
            }
        }

        async function loadSampleResume() {
            const statusDiv = document.getElementById('statusMessage');
            try {
                const res = await fetch('/api/get-resume');
                const text = await res.text();
                if (text) {
                    document.getElementById('resumeInput').value = text;
                    statusDiv.className = 'status-msg success';
                    statusDiv.innerText = '✅ Sample resume loaded! You can edit it above.';
                    const ok = await ensureGenerated();
                    if (ok) {
                        document.getElementById('portfolioPreview').src = '/portfolio.html?t=' + new Date().getTime();
                    }
                }
            } catch (err) {
                alert('Could not read resume.txt.');
            }
        }

        // Download dropdown toggle
        function toggleDropdown() {
            document.getElementById('downloadDropdown').classList.toggle('open');
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            const wrapper = document.querySelector('.dropdown-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                document.getElementById('downloadDropdown').classList.remove('open');
            }
        });

        async function downloadAs(format) {
            document.getElementById('downloadDropdown').classList.remove('open');
            const statusDiv = document.getElementById('statusMessage');

            const resumeText = document.getElementById('resumeInput').value.trim();
            if (!resumeText) {
                statusDiv.className = 'status-msg error';
                statusDiv.innerText = '❌ Please enter resume text or load sample first!';
                return;
            }

            statusDiv.className = 'status-msg';
            statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating & preparing download...';

            // First ensure portfolio is generated with latest text + theme
            const ok = await ensureGenerated();
            if (!ok) {
                statusDiv.className = 'status-msg error';
                statusDiv.innerText = '❌ Failed to generate portfolio.';
                return;
            }

            document.getElementById('portfolioPreview').src = '/portfolio.html?t=' + new Date().getTime();

            if (format === 'html') {
                const a = document.createElement('a');
                a.href = '/portfolio.html?t=' + new Date().getTime();
                a.download = 'portfolio.html';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                statusDiv.className = 'status-msg success';
                statusDiv.innerText = '✅ HTML file downloading!';
            }
            else if (format === 'pdf') {
                // Open portfolio in new window and trigger browser print (Save as PDF)
                const printWin = window.open('/portfolio.html?t=' + new Date().getTime(), '_blank');
                printWin.addEventListener('load', () => {
                    setTimeout(() => { printWin.print(); }, 600);
                });
                statusDiv.className = 'status-msg success';
                statusDiv.innerText = '✅ Print dialog opened — choose "Save as PDF" to download!';
            }
            else if (format === 'docx') {
                // Download Word .doc from server
                const a = document.createElement('a');
                a.href = '/api/download-docx';
                a.download = 'portfolio.doc';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                statusDiv.className = 'status-msg success';
                statusDiv.innerText = '✅ Word document downloading!';
            }
        }
    </script>
</body>
</html>"""

# ==========================================================
# HTTP SERVER REQUEST HANDLER
# ==========================================================
class WebAppHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path).path

        if url_path == '/' or url_path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(WEB_APP_HTML.encode('utf-8'))

        elif url_path == '/api/get-resume':
            resume_file = os.path.join(BASE_DIR, 'resume.txt')
            content = ""
            if os.path.exists(resume_file):
                with open(resume_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif url_path == '/api/download-docx':
            # Generate a Word-compatible .doc file from portfolio.html
            portfolio_path = os.path.join(BASE_DIR, 'portfolio.html')
            style_path = os.path.join(BASE_DIR, 'style.css')
            if os.path.exists(portfolio_path):
                with open(portfolio_path, 'r', encoding='utf-8') as f:
                    portfolio_html = f.read()
                # Read CSS to inline it
                css_content = ""
                if os.path.exists(style_path):
                    with open(style_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                # Wrap in Word-compatible MHTML format
                word_html = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml><![endif]-->
<style>{css_content}</style>
</head>
{portfolio_html[portfolio_html.find('<body'):]}"""
                doc_bytes = word_html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/msword')
                self.send_header('Content-Disposition', 'attachment; filename="portfolio.doc"')
                self.send_header('Content-Length', str(len(doc_bytes)))
                self.end_headers()
                self.wfile.write(doc_bytes)
            else:
                self.send_error(404, "portfolio.html not found. Generate it first.")

        elif url_path == '/portfolio.html' or url_path == '/style.css':
            file_name = url_path.lstrip('/')
            file_path = os.path.join(BASE_DIR, file_name)
            if os.path.exists(file_path):
                content_type = 'text/html; charset=utf-8' if file_name.endswith('.html') else 'text/css; charset=utf-8'
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File Not Found")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == '/api/generate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode('utf-8'))
                resume_text = payload.get('resume_text', '')
                theme_choice = payload.get('theme_choice', '1')

                cleaned_resume = clean_resume_text(resume_text)
                theme_class, theme_name = THEME_MAP.get(theme_choice, THEME_MAP["1"])

                portfolio_data = None
                model = configure_gemini()

                if model:
                    prompt = build_prompt(cleaned_resume)
                    raw_resp = call_gemini(model, prompt)
                    if raw_resp:
                        portfolio_data = parse_and_validate_json(raw_resp)

                if not portfolio_data:
                    portfolio_data = SAMPLE_PORTFOLIO_DATA.copy()
                    if cleaned_resume:
                        lines = cleaned_resume.splitlines()
                        if lines:
                            portfolio_data["name"] = lines[0].strip()

                success = generate_html(portfolio_data, theme_class)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response_json = json.dumps({'success': success, 'theme': theme_name})
                self.wfile.write(response_json.encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

def run_web_app(port=5000):
    """Starts the Web Application Server on http://localhost:PORT"""
    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, WebAppHandler)
    except OSError:
        port = 8000
        server_address = ('', port)
        httpd = HTTPServer(server_address, WebAppHandler)

    app_url = f"http://localhost:{port}/"
    print("\n========================================================")
    print(f"🚀 Web Application is running live at: {app_url}")
    print("   Open this URL in your web browser to use the Web UI!")
    print("========================================================\n")

    try:
        webbrowser.open(app_url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Web Application server stopped.")

if __name__ == "__main__":
    run_web_app()
