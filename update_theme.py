import os
import re

html_content = '''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Studio — Resume to Web Portfolio Generator</title>
    <meta name="description" content="Convert resume details into an elegant, single-page web portfolio. Clean, responsive, and customizable.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        /* =============================================
           DESIGN SYSTEM & THEME TOKENS (LIGHT DEFAULT)
           ============================================= */
        :root, [data-theme="light"] {
            --bg-base:       #faf9f6;
            --bg-surface:    #ffffff;
            --bg-raised:     #f1f5f9;
            --bg-overlay:    #ffffff;
            --border:        #e2e8f0;
            --border-hover:  #cbd5e1;
            --accent:        #4f46e5;
            --accent-hover:  #4338ca;
            --accent-subtle: #e0e7ff;
            --accent-green:  #059669;
            --accent-amber:  #d97706;
            --text-primary:  #0f172a;
            --text-secondary:#475569;
            --text-muted:    #64748b;
            --radius-sm:     8px;
            --radius-md:     12px;
            --radius-lg:     16px;
            --radius-xl:     24px;
            --shadow-sm:     0 1px 3px rgba(15,23,42,0.06);
            --shadow-md:     0 6px 20px -4px rgba(15,23,42,0.08);
            --shadow-lg:     0 16px 40px -8px rgba(15,23,42,0.12);
            --transition:    0.2s ease;
        }

        [data-theme="dark"] {
            --bg-base:       #0b0f19;
            --bg-surface:    #151c2c;
            --bg-raised:     #1e293b;
            --bg-overlay:    #1e293b;
            --border:        #334155;
            --border-hover:  #475569;
            --accent:        #6366f1;
            --accent-hover:  #818cf8;
            --accent-subtle: rgba(99,102,241,0.15);
            --accent-green:  #10b981;
            --accent-amber:  #f59e0b;
            --text-primary:  #f8fafc;
            --text-secondary:#94a3b8;
            --text-muted:    #64748b;
            --shadow-sm:     0 1px 3px rgba(0,0,0,0.3);
            --shadow-md:     0 6px 20px rgba(0,0,0,0.4);
            --shadow-lg:     0 16px 40px rgba(0,0,0,0.6);
        }

        *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            transition: background-color var(--transition), color var(--transition);
        }

        h1, h2, h3, h4, .brand-name {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Architectural Grid Substrate */
        .bg-grid {
            position: fixed; inset: 0; z-index: 0;
            background-image:
                linear-gradient(var(--border) 1px, transparent 1px),
                linear-gradient(90deg, var(--border) 1px, transparent 1px);
            background-size: 48px 48px;
            opacity: 0.35;
            pointer-events: none;
        }

        .app-root { position: relative; z-index: 1; min-height: 100vh; display: flex; flex-direction: column; }

        /* =============================================
           WELCOME MODAL
           ============================================= */
        .modal-overlay {
            position: fixed; inset: 0; z-index: 999;
            background: rgba(15,23,42,0.5);
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            display: flex; align-items: center; justify-content: center;
            padding: 20px;
            opacity: 0; pointer-events: none;
            transition: opacity var(--transition);
        }
        .modal-overlay.active { opacity: 1; pointer-events: auto; }
        .modal-card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            max-width: 540px; width: 100%;
            padding: 36px;
            box-shadow: var(--shadow-lg);
            transform: translateY(16px) scale(0.98);
            transition: transform var(--transition);
            text-align: center;
        }
        .modal-overlay.active .modal-card { transform: translateY(0) scale(1); }
        .modal-icon {
            width: 56px; height: 56px; margin: 0 auto 18px;
            background: var(--accent-subtle);
            color: var(--accent);
            border-radius: var(--radius-lg);
            display: flex; align-items: center; justify-content: center;
            font-size: 24px;
        }
        .modal-card h2 { font-size: 1.6em; font-weight: 800; margin-bottom: 8px; color: var(--text-primary); }
        .modal-card p { color: var(--text-secondary); font-size: 0.95em; line-height: 1.6; margin-bottom: 24px; }
        .modal-options { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 18px; }
        @media (max-width: 540px) { .modal-options { grid-template-columns: 1fr; } }
        .modal-option-btn {
            background: var(--bg-base); border: 1px solid var(--border);
            border-radius: var(--radius-md); padding: 18px 14px; cursor: pointer;
            text-align: center; transition: all var(--transition);
        }
        .modal-option-btn:hover { border-color: var(--accent); background: var(--accent-subtle); transform: translateY(-2px); }
        .modal-option-btn i { font-size: 1.5em; margin-bottom: 8px; display: block; color: var(--accent); }
        .modal-option-btn .opt-title { font-weight: 700; font-size: 0.9em; color: var(--text-primary); margin-bottom: 4px; }
        .modal-option-btn .opt-desc { font-size: 0.78em; color: var(--text-muted); line-height: 1.4; }
        .modal-close-link { font-size: 0.82em; color: var(--text-muted); cursor: pointer; text-decoration: underline; }
        .modal-close-link:hover { color: var(--text-primary); }

        /* =============================================
           NAVBAR / HEADER
           ============================================= */
        .topbar {
            position: sticky; top: 0; z-index: 100;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 32px; height: 64px;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border);
            box-shadow: var(--shadow-sm);
        }
        .topbar-brand { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .brand-icon {
            width: 32px; height: 32px;
            background: var(--accent);
            border-radius: var(--radius-sm);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; color: #fff; font-weight: 800;
        }
        .brand-name { font-size: 1.1em; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em; }
        .brand-name span { color: var(--accent); }
        .topbar-right { display: flex; align-items: center; gap: 10px; }

        .save-indicator {
            font-size: 0.78em; font-weight: 600; color: var(--accent-green);
            background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.2);
            padding: 4px 12px; border-radius: 20px; display: flex; align-items: center; gap: 6px;
        }

        /* =============================================
           HERO HEADER
           ============================================= */
        .hero { text-align: center; padding: 40px 24px 28px; max-width: 760px; margin: 0 auto; }
        .hero h1 { font-size: clamp(2em, 4vw, 2.8em); font-weight: 800; letter-spacing: -0.03em; line-height: 1.2; margin-bottom: 10px; color: var(--text-primary); }
        .hero h1 .accent-text { color: var(--accent); }
        .hero-sub { font-size: 1em; color: var(--text-secondary); max-width: 580px; margin: 0 auto 20px; line-height: 1.6; }

        /* =============================================
           MAIN WORKSPACE LAYOUT
           ============================================= */
        .workspace {
            max-width: 1440px; margin: 0 auto;
            padding: 0 28px 60px;
            display: grid; grid-template-columns: 600px 1fr; gap: 28px;
            align-items: start;
        }
        @media (max-width: 1180px) { .workspace { grid-template-columns: 1fr; } }

        /* =============================================
           PANELS & CARDS
           ============================================= */
        .panel {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            overflow: hidden; box-shadow: var(--shadow-md);
        }
        .panel-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 16px 24px; border-bottom: 1px solid var(--border);
            background: var(--bg-raised);
        }
        .panel-title { display: flex; align-items: center; gap: 8px; font-size: 0.9em; font-weight: 700; color: var(--text-primary); }
        .panel-title i { color: var(--accent); }
        .panel-body { padding: 24px; }

        /* =============================================
           SCORE & COMPLETENESS BAR
           ============================================= */
        .score-card {
            background: var(--bg-raised); border: 1px solid var(--border);
            border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 20px;
            display: flex; align-items: center; justify-content: space-between; gap: 14px;
        }
        .score-info { flex: 1; }
        .score-title { font-size: 0.82em; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
        .score-bar-bg { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
        .score-bar-fill { height: 100%; width: 25%; background: var(--accent); transition: width 0.3s ease; border-radius: 3px; }

        /* =============================================
           FORM TAB NAVIGATOR
           ============================================= */
        .form-tabs {
            display: flex; gap: 4px; background: var(--bg-raised);
            padding: 4px; border-radius: var(--radius-md); border: 1px solid var(--border);
            margin-bottom: 20px; overflow-x: auto;
        }
        .tab-btn {
            flex: 1; padding: 9px 12px; border-radius: var(--radius-sm);
            border: none; background: transparent; color: var(--text-secondary);
            font-size: 0.8em; font-weight: 600; cursor: pointer;
            display: flex; align-items: center; justify-content: center; gap: 6px;
            white-space: nowrap; transition: all var(--transition);
        }
        .tab-btn:hover { color: var(--text-primary); background: var(--bg-surface); }
        .tab-btn.active { background: var(--bg-surface); color: var(--accent); box-shadow: var(--shadow-sm); border: 1px solid var(--border); }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* =============================================
           FORM FIELDS
           ============================================= */
        .field-group { margin-bottom: 18px; }
        .field-label-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
        .field-label { font-size: 0.8em; font-weight: 700; color: var(--text-primary); letter-spacing: 0.02em; display: flex; align-items: center; gap: 6px; }
        .field-label i { color: var(--accent); font-size: 0.9em; }
        .btn-ai-enhance {
            font-size: 0.72em; font-weight: 600; color: var(--accent);
            background: var(--accent-subtle); border: 1px solid rgba(79,70,229,0.2);
            padding: 3px 10px; border-radius: 12px; cursor: pointer;
            transition: all var(--transition); display: inline-flex; align-items: center; gap: 4px;
        }
        .btn-ai-enhance:hover { background: var(--accent); color: #fff; }

        .field-input {
            width: 100%; background: var(--bg-surface);
            border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 12px 16px; color: var(--text-primary);
            font-family: 'Inter', sans-serif; font-size: 0.9em; line-height: 1.5;
            outline: none; transition: border-color var(--transition), box-shadow var(--transition);
        }
        .field-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-subtle); }
        .field-input::placeholder { color: var(--text-muted); }
        textarea.field-input { resize: vertical; min-height: 100px; }
        .field-hint-text { font-size: 0.76em; color: var(--text-muted); margin-top: 4px; }

        /* =============================================
           BUTTONS & ACTIONS
           ============================================= */
        .btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            padding: 10px 18px; border-radius: var(--radius-md);
            font-family: 'Inter', sans-serif; font-size: 0.88em; font-weight: 600;
            border: none; cursor: pointer; text-decoration: none;
            transition: all var(--transition); white-space: nowrap; user-select: none;
        }
        .btn:hover { transform: translateY(-1px); opacity: 0.96; }
        .btn:active { transform: translateY(0); }
        .btn-primary { background: var(--accent); color: #fff; box-shadow: 0 4px 14px rgba(79,70,229,0.25); }
        .btn-primary:hover { background: var(--accent-hover); }
        .btn-secondary { background: var(--bg-raised); color: var(--text-primary); border: 1px solid var(--border); }
        .btn-secondary:hover { border-color: var(--border-hover); background: var(--bg-surface); }
        .btn-amber { background: var(--accent-amber); color: #fff; }
        .btn-green { background: var(--accent-green); color: #fff; }
        .btn-sm { padding: 7px 12px; font-size: 0.8em; }
        .btn-full { width: 100%; padding: 14px; font-size: 0.95em; }

        /* =============================================
           THEME SELECTOR GRID
           ============================================= */
        .theme-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
        .theme-card {
            background: var(--bg-base); border: 1px solid var(--border);
            border-radius: var(--radius-md); padding: 14px; cursor: pointer;
            transition: all var(--transition); text-align: left; position: relative;
        }
        .theme-card:hover { border-color: var(--accent); }
        .theme-card.active { border-color: var(--accent); background: var(--accent-subtle); }
        .theme-card h4 { font-size: 0.88em; font-weight: 700; color: var(--text-primary); margin-bottom: 3px; }
        .theme-card p { font-size: 0.76em; color: var(--text-muted); margin-bottom: 8px; }
        .theme-dots { display: flex; gap: 5px; }
        .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }

        /* =============================================
           STATUS BAR
           ============================================= */
        .status-bar {
            margin-top: 14px; padding: 10px 16px; border-radius: var(--radius-md);
            font-size: 0.85em; font-weight: 600; display: none; align-items: center; gap: 8px;
        }
        .status-bar.show { display: flex; }
        .status-bar.success { background: rgba(5,150,105,0.1); border: 1px solid rgba(5,150,105,0.25); color: var(--accent-green); }
        .status-bar.error   { background: rgba(220,38,38,0.1); border: 1px solid rgba(220,38,38,0.25); color: #dc2626; }
        .status-bar.info    { background: var(--accent-subtle); border: 1px solid rgba(79,70,229,0.25); color: var(--accent); }

        /* =============================================
           PREVIEW PANEL (RIGHT SIDE)
           ============================================= */
        .preview-panel { position: sticky; top: 80px; }
        .preview-toolbar {
            display: flex; align-items: center; justify-content: space-between;
            padding: 14px 20px; border-bottom: 1px solid var(--border);
            background: var(--bg-raised);
        }
        .preview-title { font-size: 0.85em; font-weight: 700; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent-green); }
        .preview-actions { display: flex; gap: 8px; align-items: center; }

        .preview-frame {
            height: calc(100vh - 210px); min-height: 540px;
            width: 100%; border: none; background: #fff; display: block;
        }
        .preview-placeholder {
            height: calc(100vh - 210px); min-height: 540px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            gap: 14px; color: var(--text-muted); padding: 40px; text-align: center;
        }
        .preview-placeholder i { font-size: 3em; opacity: 0.35; color: var(--accent); }

        /* =============================================
           DOWNLOAD DROPDOWN MENU
           ============================================= */
        .dropdown-wrapper { position: relative; }
        .dropdown-menu {
            display: none; position: absolute; right: 0; top: calc(100% + 6px);
            background: var(--bg-surface); border: 1px solid var(--border);
            border-radius: var(--radius-md); min-width: 200px;
            box-shadow: var(--shadow-lg); z-index: 200; overflow: hidden;
        }
        .dropdown-menu.open { display: block; animation: dropDown 0.15s ease; }
        @keyframes dropDown { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        .dropdown-item {
            display: flex; align-items: center; gap: 10px; padding: 11px 16px;
            font-size: 0.85em; font-weight: 600; color: var(--text-primary); cursor: pointer;
            border-bottom: 1px solid var(--border); transition: background var(--transition);
        }
        .dropdown-item:last-child { border-bottom: none; }
        .dropdown-item:hover { background: var(--accent-subtle); }
        .dropdown-item .fmt { font-size: 0.75em; color: var(--text-muted); margin-left: auto; }

        /* =============================================
           FOOTER
           ============================================= */
        .footer-strip {
            border-top: 1px solid var(--border); padding: 20px 24px;
            display: flex; align-items: center; justify-content: center; gap: 32px; flex-wrap: wrap;
            background: var(--bg-surface); margin-top: auto;
        }
        .feature-chip { display: flex; align-items: center; gap: 8px; font-size: 0.8em; color: var(--text-secondary); }
        .feature-chip i { color: var(--accent); }

        .spin { animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="bg-grid"></div>

    <!-- WELCOME MODAL -->
    <div class="modal-overlay" id="welcomeModal">
        <div class="modal-card">
            <div class="modal-icon"><i class="fas fa-file-invoice"></i></div>
            <h2>Welcome to Portfolio Studio</h2>
            <p>Convert your resume text into a clean, editable single-page web portfolio. Have you built a portfolio with us before?</p>

            <div class="modal-options">
                <div class="modal-option-btn" onclick="handleWelcomeChoice('new')">
                    <i class="fas fa-user-plus"></i>
                    <div class="opt-title">First Time User</div>
                    <div class="opt-desc">Create a new portfolio from scratch or guided sample</div>
                </div>
                <div class="modal-option-btn" onclick="handleWelcomeChoice('returning')">
                    <i class="fas fa-rotate-left"></i>
                    <div class="opt-title">Returning User</div>
                    <div class="opt-desc">Load & edit your saved resume data instantly</div>
                </div>
            </div>

            <div class="modal-close-link" onclick="closeModal()">Skip to Editor →</div>
        </div>
    </div>

    <div class="app-root">
        <!-- NAVBAR -->
        <nav class="topbar">
            <a href="/" class="topbar-brand">
                <div class="brand-icon">P</div>
                <span class="brand-name">Portfolio<span>Studio</span></span>
            </a>
            <div class="topbar-right">
                <div class="save-indicator" id="saveIndicator"><i class="fas fa-check"></i> Saved</div>
                <button class="btn btn-secondary btn-sm" onclick="toggleDashboardTheme()" id="themeToggleBtn" title="Toggle Dashboard Light/Dark Mode">
                    <i class="fas fa-moon"></i> Dark
                </button>
                <button class="btn btn-secondary btn-sm" onclick="openModal()"><i class="fas fa-user-circle"></i> Welcome</button>
                <button class="btn btn-secondary btn-sm" onclick="exportDataJSON()"><i class="fas fa-file-code"></i> Export JSON</button>
                <button class="btn btn-secondary btn-sm" onclick="document.getElementById('importFileInput').click()"><i class="fas fa-upload"></i> Import</button>
                <input type="file" id="importFileInput" style="display:none" accept=".json" onchange="importDataJSON(event)">
                <a href="/portfolio.html" target="_blank" class="btn btn-secondary btn-sm"><i class="fas fa-external-link-alt"></i> Full View</a>
            </div>
        </nav>

        <!-- HERO HEADER -->
        <header class="hero">
            <h1>Transform Your Resume into a <span class="accent-text">Web Portfolio</span></h1>
            <p class="hero-sub">Fill out your resume details below or load the sample text to generate your customizable portfolio site.</p>
        </header>

        <!-- WORKSPACE (INPUT & PREVIEW) -->
        <main class="workspace">

            <!-- LEFT SIDE: STEPPED INPUT FORM PANEL -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title"><i class="fas fa-edit"></i> Resume Inputs</div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-amber btn-sm" onclick="loadSampleResume()"><i class="fas fa-download"></i> Load Sample</button>
                        <button class="btn btn-secondary btn-sm" onclick="resetForm()"><i class="fas fa-trash"></i> Reset</button>
                    </div>
                </div>

                <div class="panel-body">
                    <!-- SCORE BAR -->
                    <div class="score-card">
                        <div class="score-info">
                            <div class="score-title">
                                <span>Portfolio Completeness</span>
                                <span id="scoreText">0%</span>
                            </div>
                            <div class="score-bar-bg">
                                <div class="score-bar-fill" id="scoreFill"></div>
                            </div>
                        </div>
                    </div>

                    <!-- TAB NAVIGATION -->
                    <div class="form-tabs">
                        <button class="tab-btn active" onclick="switchTab('tab1', this)"><i class="fas fa-user"></i> 1. Profile</button>
                        <button class="tab-btn" onclick="switchTab('tab2', this)"><i class="fas fa-code"></i> 2. Skills & Exp</button>
                        <button class="tab-btn" onclick="switchTab('tab3', this)"><i class="fas fa-folder-open"></i> 3. Projects</button>
                        <button class="tab-btn" onclick="switchTab('tab4', this)"><i class="fas fa-palette"></i> 4. Layout Style</button>
                    </div>

                    <form id="portfolioForm" onsubmit="event.preventDefault(); generatePortfolio();">
                        <textarea id="resumeInput" style="display:none;"></textarea>

                        <!-- TAB 1: PROFILE & SUMMARY -->
                        <div class="tab-content active" id="tab1">
                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-id-card"></i> Full Name</label>
                                </div>
                                <input id="f_name" class="field-input" type="text" placeholder="e.g. Nandini Saraswat" oninput="onFieldChange()">
                            </div>

                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-briefcase"></i> Professional Title</label>
                                </div>
                                <input id="f_title" class="field-input" type="text" placeholder="e.g. Computer Science Student | Web Development Intern" oninput="onFieldChange()">
                            </div>

                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-align-left"></i> Summary</label>
                                    <button type="button" class="btn-ai-enhance" onclick="aiEnhance('summary')"><i class="fas fa-magic"></i> Auto-Format</button>
                                </div>
                                <textarea id="f_summary" class="field-input" rows="4" placeholder="Brief summary of your technical background and career goals..." oninput="onFieldChange()"></textarea>
                            </div>

                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-envelope"></i> Email Address</label>
                                </div>
                                <input id="f_email" class="field-input" type="email" placeholder="contact@example.com" oninput="onFieldChange()">
                            </div>

                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px;">
                                <div class="field-group">
                                    <label class="field-label"><i class="fab fa-linkedin"></i> LinkedIn</label>
                                    <input id="f_linkedin" class="field-input" type="text" placeholder="linkedin.com/in/example" oninput="onFieldChange()">
                                </div>
                                <div class="field-group">
                                    <label class="field-label"><i class="fab fa-github"></i> GitHub</label>
                                    <input id="f_github" class="field-input" type="text" placeholder="github.com/example" oninput="onFieldChange()">
                                </div>
                            </div>
                        </div>

                        <!-- TAB 2: SKILLS & EXPERIENCE -->
                        <div class="tab-content" id="tab2">
                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-tools"></i> Skills (Comma Separated)</label>
                                </div>
                                <input id="f_skills" class="field-input" type="text" placeholder="Python, Java, SQL, HTML/CSS, JavaScript, React, Flask, Git" oninput="onFieldChange()">
                                <div class="field-hint-text">Separate skills with commas</div>
                            </div>

                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-building"></i> Work Experience</label>
                                    <button type="button" class="btn-ai-enhance" onclick="aiEnhance('experience')"><i class="fas fa-magic"></i> Auto-Format</button>
                                </div>
                                <textarea id="f_experience" class="field-input" rows="5" placeholder="Format: Role | Company | Year | Responsibilities
e.g. Web Development Intern | Infosys | 2025 | Developed responsive user interfaces" oninput="onFieldChange()"></textarea>
                                <div class="field-hint-text">Format per line: Role | Company | Year | Responsibilities</div>
                            </div>
                        </div>

                        <!-- TAB 3: PROJECTS & EDUCATION -->
                        <div class="tab-content" id="tab3">
                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-layer-group"></i> Projects</label>
                                    <button type="button" class="btn-ai-enhance" onclick="aiEnhance('projects')"><i class="fas fa-magic"></i> Auto-Format</button>
                                </div>
                                <textarea id="f_projects" class="field-input" rows="5" placeholder="Format: Title | Description | Technologies
e.g. Zenith 2 | Project management platform | Python, Flask, SQL" oninput="onFieldChange()"></textarea>
                            </div>

                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-graduation-cap"></i> Education</label>
                                </div>
                                <textarea id="f_education" class="field-input" rows="3" placeholder="Format: Degree | Institution | Year
e.g. B.Tech Computer Science | GLA University | 2025 - Present" oninput="onFieldChange()"></textarea>
                            </div>
                        </div>

                        <!-- TAB 4: ACHIEVEMENTS & THEME -->
                        <div class="tab-content" id="tab4">
                            <div class="field-group">
                                <div class="field-label-row">
                                    <label class="field-label"><i class="fas fa-trophy"></i> Achievements & Leadership</label>
                                </div>
                                <textarea id="f_achievements" class="field-input" rows="3" placeholder="One entry per line...
e.g. Overall Coordinator, College Hackathon (2025)" oninput="onFieldChange()"></textarea>
                            </div>

                            <div class="field-group">
                                <label class="field-label" style="margin-bottom:12px;"><i class="fas fa-palette"></i> Portfolio Design Theme</label>
                                <div class="theme-grid">
                                    <div class="theme-card active" onclick="selectTheme('4', this)">
                                        <h4>💼 Minimalist</h4>
                                        <p>Clean & Corporate Light (Default)</p>
                                        <div class="theme-dots"><span class="dot" style="background:#f8fafc"></span><span class="dot" style="background:#3b82f6"></span><span class="dot" style="background:#0f172a"></span></div>
                                    </div>
                                    <div class="theme-card" onclick="selectTheme('2', this)">
                                        <h4>📰 Editorial</h4>
                                        <p>Clean Magazine Serif</p>
                                        <div class="theme-dots"><span class="dot" style="background:#ffffff"></span><span class="dot" style="background:#dc2626"></span><span class="dot" style="background:#1c1917"></span></div>
                                    </div>
                                    <div class="theme-card" onclick="selectTheme('1', this)">
                                        <h4>✨ Glassmorphism</h4>
                                        <p>Vibrant Gradient</p>
                                        <div class="theme-dots"><span class="dot" style="background:#a855f7"></span><span class="dot" style="background:#38bdf8"></span><span class="dot" style="background:#0f0c29"></span></div>
                                    </div>
                                    <div class="theme-card" onclick="selectTheme('3', this)">
                                        <h4>💻 Terminal</h4>
                                        <p>Developer Monospace</p>
                                        <div class="theme-dots"><span class="dot" style="background:#0d1117"></span><span class="dot" style="background:#58a6ff"></span><span class="dot" style="background:#7ee787"></span></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- SUBMIT BUTTON -->
                        <div style="margin-top: 20px;">
                            <button type="submit" id="generateBtn" class="btn btn-primary btn-full"><i class="fas fa-globe"></i> Generate & View Portfolio</button>
                        </div>
                    </form>

                    <div id="statusBar" class="status-bar"></div>
                </div>
            </div>

            <!-- RIGHT SIDE: LIVE PREVIEW PANEL -->
            <div class="panel preview-panel">
                <div class="preview-toolbar">
                    <div class="preview-title">
                        <div class="status-dot"></div> Live Webpage Preview
                    </div>
                    <div class="preview-actions">
                        <div class="dropdown-wrapper">
                            <button class="btn btn-green btn-sm" onclick="toggleDownloadDropdown()"><i class="fas fa-download"></i> Download <i class="fas fa-chevron-down" style="font-size:0.7em"></i></button>
                            <div class="dropdown-menu" id="downloadDropdown">
                                <div class="dropdown-item" onclick="downloadAs('html')"><i class="fas fa-code" style="color:#3b82f6"></i> Download HTML <span class="fmt">.html</span></div>
                                <div class="dropdown-item" onclick="downloadAs('pdf')"><i class="fas fa-file-pdf" style="color:#ef4444"></i> Download PDF <span class="fmt">.pdf</span></div>
                                <div class="dropdown-item" onclick="downloadAs('docx')"><i class="fas fa-file-word" style="color:#2563eb"></i> Download Word <span class="fmt">.doc</span></div>
                            </div>
                        </div>
                        <a href="/portfolio.html" target="_blank" class="btn btn-secondary btn-sm"><i class="fas fa-expand"></i> Full Screen</a>
                    </div>
                </div>

                <div id="previewPlaceholder" class="preview-placeholder">
                    <i class="fas fa-desktop"></i>
                    <h3>Your Web Portfolio Preview Will Appear Here</h3>
                    <p>Fill out your details on the left or click "Load Sample", then click "Generate & View Portfolio".</p>
                </div>

                <iframe id="portfolioPreview" class="preview-frame" style="display:none;" src="about:blank"></iframe>
            </div>
        </main>

        <!-- FOOTER -->
        <footer class="footer-strip">
            <div class="feature-chip"><i class="fas fa-save"></i> Local Storage Saved</div>
            <div class="feature-chip"><i class="fas fa-code"></i> Python Backend Server</div>
            <div class="feature-chip"><i class="fas fa-file-download"></i> HTML / PDF / Word Export</div>
        </footer>
    </div>

    <script>
        let selectedThemeChoice = '4';

        // --- DASHBOARD THEME TOGGLE (LIGHT / DARK) ---
        function initDashboardTheme() {
            const savedTheme = localStorage.getItem('portfolio_ai_dashboard_theme') || 'light';
            setDashboardTheme(savedTheme);
        }

        function setDashboardTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('portfolio_ai_dashboard_theme', theme);
            const btn = document.getElementById('themeToggleBtn');
            if (btn) {
                if (theme === 'dark') {
                    btn.innerHTML = '<i class="fas fa-sun"></i> Light';
                } else {
                    btn.innerHTML = '<i class="fas fa-moon"></i> Dark';
                }
            }
        }

        function toggleDashboardTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            setDashboardTheme(next);
        }

        // --- WELCOME MODAL LOGIC ---
        window.addEventListener('DOMContentLoaded', () => {
            initDashboardTheme();
            const hasVisited = localStorage.getItem('portfolio_ai_visited');
            const savedData = localStorage.getItem('portfolio_ai_resume_data');
            
            if (!hasVisited) {
                openModal();
            } else if (savedData) {
                loadSavedData(JSON.parse(savedData));
            }
        });

        function openModal() {
            document.getElementById('welcomeModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('welcomeModal').classList.remove('active');
            localStorage.setItem('portfolio_ai_visited', 'true');
        }

        function handleWelcomeChoice(choice) {
            closeModal();
            if (choice === 'returning') {
                const savedData = localStorage.getItem('portfolio_ai_resume_data');
                if (savedData) {
                    loadSavedData(JSON.parse(savedData));
                    showStatus('success', 'Loaded your saved resume data!');
                    generatePortfolio();
                } else {
                    loadSampleResume();
                }
            } else {
                loadSampleResume();
            }
        }

        // --- TAB NAVIGATION LOGIC ---
        function switchTab(tabId, el) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }

        // --- FIELD PERSISTENCE & SCORE METER ---
        function onFieldChange() {
            updateScore();
            autoSaveData();
        }

        function updateScore() {
            const fields = ['f_name', 'f_title', 'f_summary', 'f_skills', 'f_experience', 'f_education', 'f_projects', 'f_email'];
            let filledCount = 0;
            fields.forEach(id => {
                const el = document.getElementById(id);
                if (el && el.value.trim().length > 0) filledCount++;
            });
            const percent = Math.round((filledCount / fields.length) * 100);
            document.getElementById('scoreText').innerText = percent + '%';
            document.getElementById('scoreFill').style.width = percent + '%';
        }

        function autoSaveData() {
            const data = getFormDataObj();
            localStorage.setItem('portfolio_ai_resume_data', JSON.stringify(data));
            const indicator = document.getElementById('saveIndicator');
            if (indicator) {
                indicator.style.opacity = '1';
                setTimeout(() => { indicator.style.opacity = '0.7'; }, 1000);
            }
        }

        function getFormDataObj() {
            return {
                name: document.getElementById('f_name').value,
                title: document.getElementById('f_title').value,
                summary: document.getElementById('f_summary').value,
                skills: document.getElementById('f_skills').value,
                experience: document.getElementById('f_experience').value,
                education: document.getElementById('f_education').value,
                projects: document.getElementById('f_projects').value,
                achievements: document.getElementById('f_achievements').value,
                email: document.getElementById('f_email').value,
                linkedin: document.getElementById('f_linkedin').value,
                github: document.getElementById('f_github').value,
                theme: selectedThemeChoice
            };
        }

        function loadSavedData(data) {
            if (!data) return;
            document.getElementById('f_name').value = data.name || '';
            document.getElementById('f_title').value = data.title || '';
            document.getElementById('f_summary').value = data.summary || '';
            document.getElementById('f_skills').value = data.skills || '';
            document.getElementById('f_experience').value = data.experience || '';
            document.getElementById('f_education').value = data.education || '';
            document.getElementById('f_projects').value = data.projects || '';
            document.getElementById('f_achievements').value = data.achievements || '';
            document.getElementById('f_email').value = data.email || '';
            document.getElementById('f_linkedin').value = data.linkedin || '';
            document.getElementById('f_github').value = data.github || '';
            if (data.theme) {
                selectedThemeChoice = data.theme;
            }
            updateScore();
        }

        function resetForm() {
            if (confirm("Are you sure you want to reset all input fields?")) {
                document.getElementById('portfolioForm').reset();
                localStorage.removeItem('portfolio_ai_resume_data');
                updateScore();
                showStatus('info', 'Form cleared.');
            }
        }

        // --- AUTO-FORMAT HELPER ---
        function aiEnhance(field) {
            if (field === 'summary') {
                const cur = document.getElementById('f_summary').value;
                if (!cur.trim()) {
                    document.getElementById('f_summary').value = "Motivated and detail-oriented professional with strong technical foundations in computer science, software design, and problem solving. Proven track record of delivering web applications and collaborating on team projects.";
                } else {
                    document.getElementById('f_summary').value = "Driven software specialist specializing in full-stack web solutions and data-driven systems. " + cur.trim();
                }
            } else if (field === 'experience') {
                const cur = document.getElementById('f_experience').value;
                if (!cur.trim()) {
                    document.getElementById('f_experience').value = "Software Engineering Intern | Tech Solutions | 2025 | Developed responsive user interfaces using HTML, CSS, JavaScript and optimized API endpoints.";
                }
            } else if (field === 'projects') {
                const cur = document.getElementById('f_projects').value;
                if (!cur.trim()) {
                    document.getElementById('f_projects').value = "Smart Portfolio Generator | Web app that converts raw text resumes into structured HTML portfolios using Python | Python, HTML, CSS, JavaScript";
                }
            }
            onFieldChange();
            showStatus('success', 'Form text updated!');
        }

        // --- SERIALIZE & GENERATE ---
        function serializeFields() {
            const v = id => document.getElementById(id).value.trim();
            const parts = [
                '__STRUCTURED__',
                'Name: ' + v('f_name'),
                'Title: ' + v('f_title'),
                'Summary: ' + v('f_summary').replace(/\\n/g, ' '),
                'Skills: ' + v('f_skills'),
                'Experience: ' + v('f_experience'),
                'Education: ' + v('f_education'),
                'Projects: ' + v('f_projects'),
                'Achievements: ' + v('f_achievements'),
                'Email: ' + v('f_email'),
                'LinkedIn: ' + v('f_linkedin'),
                'GitHub: ' + v('f_github')
            ];
            const result = parts.join('\\n');
            document.getElementById('resumeInput').value = result;
            return result;
        }

        async function generatePortfolio() {
            const btn = document.getElementById('generateBtn');
            const nameVal = document.getElementById('f_name').value.trim();
            if (!nameVal) {
                showStatus('error', 'Please fill in at least your Full Name before generating!');
                return;
            }

            const payloadText = serializeFields();
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Portfolio...';
            showStatus('info', 'Building portfolio webpage...');

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resume_text: payloadText, theme_choice: selectedThemeChoice })
                });
                const result = await res.json();
                if (result.success) {
                    const iframe = document.getElementById('portfolioPreview');
                    document.getElementById('previewPlaceholder').style.display = 'none';
                    iframe.style.display = 'block';
                    iframe.src = '/portfolio.html?t=' + new Date().getTime();
                    showStatus('success', '✅ Portfolio generated! Click any text in the preview to edit directly.');
                } else {
                    showStatus('error', 'Failed to generate portfolio.');
                }
            } catch (err) {
                showStatus('error', 'Could not reach server.');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-globe"></i> Generate & View Portfolio';
            }
        }

        function selectTheme(choice, el) {
            selectedThemeChoice = choice;
            document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            onFieldChange();
            generatePortfolio();
        }

        // --- SAMPLE LOAD ---
        async function loadSampleResume() {
            try {
                const res = await fetch('/api/get-resume');
                const text = await res.text();
                if (text) {
                    const lines = text.split('\\n').map(l => l.trim()).filter(Boolean);
                    let name='', title='', summary='', skills='', experience=[], education=[], projects=[], achievements=[], email='', linkedin='', github='';
                    let mode = 'header', hIdx = 0;

                    for (const line of lines) {
                        const low = line.toLowerCase();
                        if (low === 'summary' || low === 'professional summary') { mode = 'summary'; continue; }
                        if (low === 'skills') { mode = 'skills'; continue; }
                        if (low === 'experience' || low === 'work experience') { mode = 'experience'; continue; }
                        if (low === 'education') { mode = 'education'; continue; }
                        if (low === 'projects') { mode = 'projects'; continue; }
                        if (low === 'achievements' || low === 'awards' || low === 'awards & leadership') { mode = 'achievements'; continue; }

                        if (mode === 'header') {
                            if (hIdx === 0) name = line;
                            else if (/@|linkedin|github|phone|\\+/i.test(line)) {
                                if (!email) email = (line.match(/[\\w.+-]+@[\\w-]+\\.[\\w.]+/)||[name])[0];
                                if (!linkedin) linkedin = (line.match(/linkedin\\.com\\/\\S+/i)||[''])[0];
                                if (!github) github = (line.match(/github\\.com\\/\\S+/i)||[''])[0];
                            } else if (!title) title = line;
                            hIdx++;
                        }
                        else if (mode === 'summary') summary += (summary ? ' ' : '') + line;
                        else if (mode === 'skills') skills += (skills ? ', ' : '') + line.replace(/^[-•*]\\s*/, '');
                        else if (mode === 'experience') experience.push(line.replace(/^[-•*]\\s*/, ''));
                        else if (mode === 'education') education.push(line.replace(/^[-•*]\\s*/, ''));
                        else if (mode === 'projects') projects.push(line.replace(/^[-•*]\\s*/, ''));
                        else if (mode === 'achievements') achievements.push(line.replace(/^[-•*]\\s*/, ''));
                    }

                    document.getElementById('f_name').value = name;
                    document.getElementById('f_title').value = title;
                    document.getElementById('f_summary').value = summary;
                    document.getElementById('f_skills').value = skills;
                    document.getElementById('f_experience').value = experience.join('\\n');
                    document.getElementById('f_education').value = education.join('\\n');
                    document.getElementById('f_projects').value = projects.join('\\n');
                    document.getElementById('f_achievements').value = achievements.join('\\n');
                    document.getElementById('f_email').value = email || 'contact@example.com';
                    document.getElementById('f_linkedin').value = linkedin || 'linkedin.com/in/example';
                    document.getElementById('f_github').value = github || 'github.com/example';

                    onFieldChange();
                    showStatus('success', 'Sample data loaded!');
                    generatePortfolio();
                }
            } catch (err) {
                showStatus('error', 'Could not load sample.');
            }
        }

        // --- EXPORT & IMPORT JSON ---
        function exportDataJSON() {
            const data = getFormDataObj();
            const jsonStr = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = (data.name ? data.name.replace(/\\s+/g, '_') : 'resume') + '_portfolio.json';
            a.click();
        }

        function importDataJSON(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const data = JSON.parse(event.target.result);
                    loadSavedData(data);
                    autoSaveData();
                    showStatus('success', 'JSON Resume imported successfully!');
                    generatePortfolio();
                } catch (err) {
                    showStatus('error', 'Invalid JSON file.');
                }
            };
            reader.readAsText(file);
        }

        // --- DOWNLOAD DROPDOWN LOGIC ---
        function toggleDownloadDropdown() {
            document.getElementById('downloadDropdown').classList.toggle('open');
        }
        document.addEventListener('click', (e) => {
            const wrapper = document.querySelector('.dropdown-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                document.getElementById('downloadDropdown').classList.remove('open');
            }
        });

        async function downloadAs(format) {
            document.getElementById('downloadDropdown').classList.remove('open');
            showStatus('info', 'Preparing download...');
            if (format === 'html') {
                const a = document.createElement('a');
                a.href = '/portfolio.html?t=' + new Date().getTime();
                a.download = 'portfolio.html';
                a.click();
                showStatus('success', 'HTML file downloaded!');
            } else if (format === 'pdf') {
                const printWin = window.open('/portfolio.html?t=' + new Date().getTime(), '_blank');
                printWin.addEventListener('load', () => setTimeout(() => printWin.print(), 600));
                showStatus('success', 'Print window opened. Select "Save as PDF".');
            } else if (format === 'docx') {
                const a = document.createElement('a');
                a.href = '/api/download-docx';
                a.download = 'portfolio.doc';
                a.click();
                showStatus('success', 'Word document downloaded!');
            }
        }

        function showStatus(type, msg) {
            const bar = document.getElementById('statusBar');
            bar.className = 'status-bar show ' + type;
            bar.innerText = msg;
            setTimeout(() => { bar.classList.remove('show'); }, 6000);
        }
    </script>
</body>
</html>'''

with open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

var_start = main_code.find('WEB_APP_HTML = """')
var_end = main_code.find('"""\n\n# ==========================================================\n# HTTP SERVER REQUEST HANDLER')

if var_start != -1 and var_end != -1:
    new_main = main_code[:var_start] + 'WEB_APP_HTML = """' + html_content + '"""' + main_code[var_end + 3:]
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_main)
    print("Successfully updated main.py with Light/Dark toggleable bespoke design!")
else:
    print("Error: Could not locate WEB_APP_HTML bounds.")
