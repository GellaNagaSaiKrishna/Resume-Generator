import streamlit as st
import requests
import json

def latex_escape(text):
    if not text:
        return ""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("%", "\\%"),
        ("&", "\\&"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def ai_enhance(section_type, text_content, groq_key):
    if not groq_key:
        st.warning("Please configure your GROQ API key in application secrets.")
        return None
    system_prompt = (
        f"You are a professional resume writing assistant. Improve the following {section_type} descriptions for a professional resume. "
        "Make them more impactful, use strong action verbs, quantify results where possible, and keep each description concise (1-2 lines max). "
        "Return ONLY the improved text plain descriptions with no extra commentary."
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_content},
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"AI Enhancement Failed: {str(e)}")
        return None

st.set_page_config(layout="wide", page_title="Smart LaTeX Resume Generator")

if "internships" not in st.session_state: st.session_state.internships = []
if "projects" not in st.session_state: st.session_state.projects = []
if "skills" not in st.session_state: st.session_state.skills = []
if "pors" not in st.session_state: st.session_state.pors = []
if "achievements" not in st.session_state: st.session_state.achievements = []

try:
    groq_key = st.secrets["GROQ_KEY"]
except:
    groq_key = ""

st.title("⚡ Smart LaTeX Resume Generator")
st.markdown("Fill out your details on the left panel to update the compilable LaTeX code template instantly on the right panel.")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("👤 Personal Details")
    name = st.text_input("Full Name", placeholder="Enter your name")
    year = st.text_input("Current Year", placeholder="e.g., Second Year Undergraduate")
    program = st.text_input("Program / Discipline", placeholder="e.g., Computer Science Engineering")
    email = st.text_input("Email Address")
    contact = st.text_input("Contact Number")
    github = st.text_input("GitHub Profile URL")
    linkedin = st.text_input("LinkedIn Profile URL")
    website = st.text_input("Personal Website URL")

    st.header("🎓 Academic Details")
    has_phd = st.checkbox("Include PhD Profile Row")
    if has_phd:
        phd_inst = st.text_input("PhD Institute Name")
        phd_spec = st.text_input("PhD Specialization")
        phd_marks = st.text_input("PhD CPI / Marks")
        phd_year = st.text_input("PhD Graduation/Duration Year")

    has_mtech = st.checkbox("Include M.Tech Profile Row")
    if has_mtech:
        mtech_inst = st.text_input("M.Tech Institute Name")
        mtech_spec = st.text_input("M.Tech Specialization")
        mtech_marks = st.text_input("M.Tech CPI / Marks")
        mtech_year = st.text_input("M.Tech Graduation/Duration Year")

    st.subheader("Undergraduate & Schooling")
    btech_inst = st.text_input("B.Tech Institute Name", value="Indian Institute of Technology Gandhinagar")
    btech_spec = st.text_input("B.Tech Specialization")
    btech_marks = st.text_input("B.Tech CPI / %")
    by_year = st.text_input("B.Tech Graduation Year")

    c12_inst = st.text_input("Class XII School Name / Board")
    c12_spec = st.text_input("Class XII Stream / Subjects", value="Physics, Chemistry, Maths")
    c12_marks = st.text_input("Class XII Percentage / CGPA")
    c12_year = st.text_input("Class XII Passing Year")

    c10_inst = st.text_input("Class X School Name / Board")
    c10_spec = st.text_input("Class X Stream/Subjects")
    c10_marks = st.text_input("Class X Percentage / CGPA")
    c10_year = st.text_input("Class X Passing Year")

    st.header("💼 Internships")
    with st.form("internship_form", clear_on_submit=True):
        int_title = st.text_input("Internship Title Position")
        int_info = st.text_input("Company / Organization Name")
        int_link = st.text_input("Verification Link (Optional)")
        int_desc1 = st.text_input("Core Responsibility Line 1")
        int_desc2 = st.text_input("Core Responsibility Line 2 (Optional)")
        int_year = st.text_input("Duration Timeframe")
        if st.form_submit_button("➕ Add Internship Entry"):
            if int_title:
                st.session_state.internships.append({
                    "title": int_title, "info": int_info, "link": int_link,
                    "desc1": int_desc1, "desc2": int_desc2, "year": int_year
                })

    for idx, item in enumerate(st.session_state.internships):
        st.markdown(f"**{item['title']}** at *{item['info']}* ({item['year']})")
        if st.button(f"🗑️ Remove Entry {idx+1}", key=f"del_int_{idx}"):
            st.session_state.internships.pop(idx)
            st.hybrid_code_rerun() if hasattr(st, "hybrid_code_rerun") else st.rerun()

    st.header("🚀 Projects")
    with st.form("project_form", clear_on_submit=True):
        proj_title = st.text_input("Project Title")
        proj_info = st.text_input("Project Guide / Advisor / Tech Stack")
        proj_link = st.text_input("Project Repository URL (Optional)")
        proj_desc1 = st.text_input("Technical Breakdown Line 1")
        proj_desc2 = st.text_input("Technical Breakdown Line 2 (Optional)")
        proj_year = st.text_input("Development Timeline")
        if st.form_submit_button("➕ Add Project Entry"):
            if proj_title:
                st.session_state.projects.append({
                    "title": proj_title, "info": proj_info, "link": proj_link,
                    "desc1": proj_desc1, "desc2": proj_desc2, "year": proj_year
                })

    for idx, item in enumerate(st.session_state.projects):
        st.markdown(f"**{item['title']}** — *{item['info']}* ({item['year']})")
        if st.button(f"🗑️ Remove Project {idx+1}", key=f"del_proj_{idx}"):
            st.session_state.projects.pop(idx)
            st.hybrid_code_rerun() if hasattr(st, "hybrid_code_rerun") else st.rerun()

    st.header("🛠️ Technical Skills")
    with st.form("skill_form", clear_on_submit=True):
        s_type = st.text_input("Skill Classification", placeholder="e.g., Programming Languages, Frameworks")
        s_desc = st.text_input("Specific Tech Skills", placeholder="e.g., Python, C++, Docker, React")
        if st.form_submit_button("➕ Add Skill Row"):
            if s_type:
                st.session_state.skills.append({"type": s_type, "desc": s_desc})

    for idx, item in enumerate(st.session_state.skills):
        st.markdown(f"**{item['type']}**: {item['desc']}")
        if st.button(f"🗑️ Remove Skill Category {idx+1}", key=f"del_skill_{idx}"):
            st.session_state.skills.pop(idx)
            st.hybrid_code_rerun() if hasattr(st, "hybrid_code_rerun") else st.rerun()

    st.header("🎗️ Positions of Responsibility")
    with st.form("por_form", clear_on_submit=True):
        por_name = st.text_input("Leadership Position Title")
        por_desc1 = st.text_input("Impact Activity Line 1")
        por_desc2 = st.text_input("Impact Activity Line 2 (Optional)")
        por_year = st.text_input("Active Tenure")
        if st.form_submit_button("➕ Add Role Entry"):
            if por_name:
                st.session_state.pors.append({
                    "name": por_name, "desc1": por_desc1, "desc2": por_desc2, "year": por_year
                })

    for idx, item in enumerate(st.session_state.pors):
        st.markdown(f"**{item['name']}** ({item['year']})")
        if st.button(f"🗑️ Remove Role {idx+1}", key=f"del_por_{idx}"):
            st.session_state.pors.pop(idx)
            st.hybrid_code_rerun() if hasattr(st, "hybrid_code_rerun") else st.rerun()

    st.header("🏆 Achievements & Extracurriculars")
    with st.form("ach_form", clear_on_submit=True):
        ach_name = st.text_input("Achievement Detail Description")
        if st.form_submit_button("➕ Add Distinction Entry"):
            if ach_name:
                st.session_state.achievements.append({"name": ach_name})

    for idx, item in enumerate(st.session_state.achievements):
        st.markdown(f"• {item['name']}")
        if st.button(f"🗑️ Remove Distinction {idx+1}", key=f"del_ach_{idx}"):
            st.session_state.achievements.pop(idx)
            st.hybrid_code_rerun() if hasattr(st, "hybrid_code_rerun") else st.rerun()

with col2:
    st.header("📑 Production-Ready LaTeX Code")
    st.caption("Hover over the box top-right corner to copy data instantly into Overleaf.")

    L = []
    L.append(r"\documentclass[a4paper,10pt]{article}")
    L.append(r"\usepackage[top=0.1cm, bottom=0.3cm, left=0.3cm, right=1.1cm, nohead, nofoot]{geometry}")
    L.append(r"\usepackage{graphicx}")
    L.append(r"\usepackage{url}")
    L.append(r"\usepackage{palatino}")
    L.append(r"\usepackage{booktabs}")
    L.append(r"\usepackage{hyperref}")
    L.append(r"\fontfamily{SansSerif}")
    L.append(r"\selectfont")
    L.append(r"\usepackage[T1]{fontenc}")
    L.append(r"\usepackage[utf8]{inputenc}")
    L.append(r"\usepackage{color}")
    L.append(r"\definecolor{mygrey}{gray}{0.75}")
    L.append(r"\textheight = 29.1 cm")
    L.append(r"\raggedbottom")
    L.append(r"\setlength{\tabcolsep}{0in}")
    L.append(r"\newcommand{\isep}{-2 pt}")
    L.append(r"\newcommand{\lsep}{-0.6cm}")
    L.append(r"\newcommand{\psep}{-0.6cm}")
    L.append(r"\renewcommand{\labelitemii}{$\circ$}")
    L.append(r"\pagestyle{empty}")
    L.append(r"\newcommand{\resitem}[1]{\item #1 \vspace{-2pt}}")
    L.append(r"\newcommand{\resheading}[1]{{\small \colorbox{mygrey}{\begin{minipage}{0.965\textwidth}{\textbf{#1 \vphantom{p\^{E}}}}\end{minipage}}}}")
    L.append(r"\begin{document}")
    L.append(r"\hspace{0.75cm}\\[-0.54cm]")

    L.append(rf"\textbf{{{latex_escape(name)}}} \\")
    L.append(rf"\indent {latex_escape(year)} \hfill \href{{mailto:{email}}}{{{latex_escape(email)}}}\\")
    L.append(rf"\indent Discipline of {latex_escape(program)} \hfill {latex_escape(contact)} \\")
    L.append(rf"\indent Indian Institute of Technology, Gandhinagar \hfill")
    L.append(rf"\underline{{\href{{{linkedin}}}{{LinkedIn}}}} | \underline{{\href{{{github}}}{{Github}}}} | \underline{{\href{{{website}}}{{Website}}}}")
    L.append(r"\\")

    L.append(r"\indent \resheading{\textbf{ACADEMIC DETAILS} }\\[\lsep]")
    L.append(r"\\ \\")
    L.append(r"\indent \begin{tabular}{ p{1.7cm} @{\hskip 0.08in} p{5.254cm} @{\hskip 0.08in} p{7.054cm} @{\hskip 0.09in} p{2.554cm} @{\hskip 0.08in} p{1.72cm} }")
    L.append(r"\toprule")
    L.append(r"\textbf{Degree} & \textbf{Specialization} & \textbf{Institute} & \textbf{Year} & \textbf{CPI/\%} \\")
    L.append(r"\midrule")

    if has_phd:
        L.append(rf"PhD & \textit{{{latex_escape(phd_spec)}}} & {latex_escape(phd_inst)} & {latex_escape(phd_year)} & {latex_escape(phd_marks)} \\")
    if has_mtech:
        L.append(rf"M.Tech. & \textit{{{latex_escape(mtech_spec)}}} & {latex_escape(mtech_inst)} & {latex_escape(mtech_year)} & {latex_escape(mtech_marks)} \\")

    L.append(rf"B.Tech. & \textit{{{latex_escape(btech_spec)}}} & {latex_escape(btech_inst)} & {latex_escape(by_year)} & {latex_escape(btech_marks)} \\")
    L.append(rf"Class XII & \textit{{{latex_escape(c12_spec)}}} & {latex_escape(c12_inst)} & {latex_escape(c12_year)} & {latex_escape(c12_marks)} \\")
    L.append(rf"Class X & {latex_escape(c10_spec)} & {latex_escape(c10_inst)} & {latex_escape(c10_year)} & {latex_escape(c10_marks)} \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabular}")

    if st.session_state.internships:
        L.append(r"\resheading{\textbf{ INTERNSHIPS} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize}\itemsep\isep")
        for it in st.session_state.internships:
            t = latex_escape(it["title"])
            info = latex_escape(it["info"])
            link = it["link"]
            yr = latex_escape(it["year"])
            d1 = latex_escape(it["desc1"])
            d2 = latex_escape(it["desc2"])
            if link:
                L.append(rf"\item \textbf{{{t}}} \href{{{link}}}{{{info}}} \hfill \textit{{{yr}}}")
            else:
                L.append(rf"\item \textbf{{{t}}} {info} \hfill \textit{{{yr}}}")
            L.append(r"\begin{itemize}\itemsep\isep")
            if d1: L.append(rf"\item {d1}")
            if d2: L.append(rf"\item {d2}")
            L.append(r"\end{itemize}")
        L.append(r"\end{itemize}")

    if st.session_state.projects:
        L.append(r"\resheading{\textbf{ PROJECTS} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize}\itemsep\isep")
        for p in st.session_state.projects:
            t = latex_escape(p["title"])
            info = latex_escape(p["info"])
            link = p["link"]
            yr = latex_escape(p["year"])
            d1 = latex_escape(p["desc1"])
            d2 = latex_escape(p["desc2"])
            if link:
                L.append(rf"\item \textbf{{{t}}} \href{{{link}}}{{{info}}} \hfill \textit{{{yr}}}")
            else:
                L.append(rf"\item \textbf{{{t}}} {info} \hfill \textit{{{yr}}}")
            L.append(r"\begin{itemize}\itemsep\isep")
            if d1: L.append(rf"\item {d1}")
            if d2: L.append(rf"\item {d2}")
            L.append(r"\end{itemize}")
        L.append(r"\end{itemize}")

    if st.session_state.skills:
        L.append(r"\resheading{\textbf{TECHNICAL SKILLS} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize} \itemsep \isep")
        for s in st.session_state.skills:
            L.append(rf"\item \textbf{{{latex_escape(s['type'])}:}} {latex_escape(s['desc'])}")
        L.append(r"\end{itemize}")

    if st.session_state.pors:
        L.append(r"\resheading{\textbf{POSITIONS OF RESPONSIBILITY} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize} \itemsep \isep")
        for por in st.session_state.pors:
            n = latex_escape(por["name"])
            yr = latex_escape(por["year"])
            d1 = latex_escape(por["desc1"])
            d2 = latex_escape(por["desc2"])
            L.append(rf"\item \textbf{{{n}}} \hfill \textit{{{yr}}}")
            L.append(r"\begin{itemize}\itemsep\isep")
            if d1: L.append(rf"\item {d1}")
            if d2: L.append(rf"\item {d2}")
            L.append(r"\end{itemize}")
        L.append(r"\end{itemize}")

    if st.session_state.achievements:
        L.append(r"\resheading{\textbf{ACHIEVEMENTS} }")
        L.append(r"\begin{itemize}\itemsep\isep")
        for ach in st.session_state.achievements:
            L.append(rf"\item {latex_escape(ach['name'])}")
        L.append(r"\end{itemize}")

    L.append(r"\end{document}")
    latex_code = "\n".join(L)

    st.code(latex_code, language="latex")

    if groq_key:
        st.subheader("✨ AI Acceleration Matrix")
        if st.button("Enhance Structured Resume Draft Descriptions"):
            all_descriptions = []
            for it in st.session_state.internships:
                if it["desc1"]: all_descriptions.append(f"Internship Responsibility: {it['desc1']}")
            for p in st.session_state.projects:
                if p["desc1"]: all_descriptions.append(f"Project Breakdown: {p['desc1']}")
            if all_descriptions:
                enhanced = ai_enhance("resume bullet points", "\n".join(all_descriptions), groq_key)
                if enhanced:
                    st.success("Action-verb optimized variations generated:")
                    st.text_area("Optimized Output Options", value=enhanced, height=200)
            else:
                st.info("Add text descriptions inside your internships or projects sections to allow optimization.")
