# ⚡ Smart LaTeX Resume Generator (Python)

A pure-Python desktop application to generate professional LaTeX resumes — **no JavaScript required**.

Replicates the functionality of [Kishan-Ved/resume_generator](https://github.com/Kishan-Ved/resume_generator) as a native Tkinter app.

## Features

- **Dual-panel layout**: Fill the form on the left, see LaTeX code live on the right
- **All resume sections**: Personal Details, Academic Details (PhD/MTech toggles), Internships, Projects, Technical Skills, Positions of Responsibility, Achievements
- **Add / Edit / Delete** for all list-based sections
- **One-click LaTeX copy** to clipboard → paste into Overleaf and compile
- **AI Enhancement** via Groq API (optional) — improves descriptions with strong action verbs
- **Syntax-highlighted preview** with color-coded LaTeX commands
- **Dark mode UI** with modern styling

## Requirements

- **Python 3.7+** (Tkinter ships with standard Python)
- **No pip installs needed** for core functionality

### Optional (for AI Enhancement)

```bash
pip install requests
```

## Usage

```bash
cd "Resume generator"
python main.py
```

### Steps:
1. Fill in your personal information on the left panel
2. Add internships, projects, skills, PORs, and achievements
3. Click **🚀 Generate LaTeX Code** or **📋 Copy LaTeX to Clipboard**
4. Paste into [Overleaf](https://www.overleaf.com) and compile

## AI Enhancement Setup

1. Get a free API key from [Groq Console](https://console.groq.com/)
2. Edit `secrets.json`:
   ```json
   {
       "GROQ_KEY": "gsk_your_actual_key_here"
   }
   ```
3. Click the **✨ AI Enhance** buttons next to any section

## Project Structure

```
Resume generator/
├── main.py          # Complete application (GUI + LaTeX + AI)
├── secrets.json     # Groq API key (your key here)
└── README.md        # This file
```

## LaTeX Output

The generated LaTeX follows the **CDS IITGN** resume template format and produces a clean, professional one-page resume when compiled.
