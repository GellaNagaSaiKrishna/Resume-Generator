"""
Smart LaTeX Resume Generator — Pure Python (Tkinter)
Replicates https://github.com/Kishan-Ved/resume_generator with zero JavaScript.

Run:  python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import uuid
import re

# Optional: AI enhancement via Groq
try:
    import requests as req_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ─── Colour palette (light theme matching the original website) ────
BG_FORM   = "#d9d9d9"       # Left panel background
BG_WHITE  = "#ffffff"        # Right panel / inputs
BG_GREY   = "#c0c0c0"        # Section headers in preview
FG_BLACK  = "#000000"
FG_DARK   = "#222222"
FG_DIM    = "#666666"
ACCENT    = "#333333"
LINK_BLUE = "#0066cc"
BTN_DARK  = "#212529"
BTN_HOVER = "#444444"


# ═══════════════════════════════════════════════════════════════════
#  Scrollable Frame helper
# ═══════════════════════════════════════════════════════════════════
class ScrollableFrame(tk.Frame):
    """A vertically-scrollable frame for Tkinter."""

    def __init__(self, parent, bg="#ffffff", **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._win, width=event.width)

    def _bind_mousewheel(self, _):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ═══════════════════════════════════════════════════════════════════
#  LaTeX escaping helper
# ═══════════════════════════════════════════════════════════════════
def latex_escape(text: str) -> str:
    """Escape special LaTeX characters in user text."""
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


# ═══════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════
class ResumeGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Resume Generator")
        self.root.geometry("1400x850")
        self.root.minsize(1000, 600)
        self.root.configure(bg=BG_FORM)

        # ── Data stores ─────────────────────────────────
        self.internships = []
        self.projects = []
        self.skills = []
        self.pors = []
        self.achievements = []

        # Editing indices (None = adding new)
        self._editing_intern_idx = None
        self._editing_project_idx = None
        self._editing_skill_idx = None
        self._editing_por_idx = None
        self._editing_ach_idx = None

        # ── Groq API key ────────────────────────────────
        self.groq_key = self._load_groq_key()

        # ── Build UI ────────────────────────────────────
        self._build_ui()

    # ─── Groq key ──────────────────────────────────────
    def _load_groq_key(self):
        secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.json")
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, "r") as f:
                    data = json.load(f)
                return data.get("GROQ_KEY", "")
            except Exception:
                return ""
        return ""

    # ─── Build UI ──────────────────────────────────────
    def _build_ui(self):
        # Main horizontal split using PanedWindow
        paned = tk.PanedWindow(self.root, orient="horizontal", bg="#aaaaaa",
                                sashwidth=4, sashrelief="raised", bd=0)
        paned.pack(fill="both", expand=True)

        # ═══ LEFT PANEL — Scrollable Form ═══════════════
        left_outer = tk.Frame(paned, bg=BG_FORM, bd=0)
        paned.add(left_outer, width=480, minsize=380)

        self.left_scroll = ScrollableFrame(left_outer, bg=BG_FORM)
        self.left_scroll.pack(fill="both", expand=True)
        self.form = self.left_scroll.inner

        # ═══ RIGHT PANEL — Resume Preview ═══════════════
        right_outer = tk.Frame(paned, bg=BG_WHITE, bd=0)
        paned.add(right_outer, minsize=400)

        self.right_scroll = ScrollableFrame(right_outer, bg=BG_WHITE)
        self.right_scroll.pack(fill="both", expand=True)
        self.preview_frame = self.right_scroll.inner

        # ── Build form sections (left) ──────────────────
        self._build_form_header()
        self._build_personal_section()
        self._build_academic_section()
        self._build_internship_section()
        self._build_project_section()
        self._build_skills_section()
        self._build_por_section()
        self._build_achievements_section()

        # ── Build preview (right) ───────────────────────
        self._rebuild_preview()

    # ═════════════════════════════════════════════════════
    #  FORM HEADER (left panel top)
    # ═════════════════════════════════════════════════════
    def _build_form_header(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=(12, 4))

        tk.Label(container, text="Smart LATEX Resumes with AI",
                 bg=BG_FORM, fg=FG_BLACK, font=("Arial", 20, "bold"),
                 anchor="center").pack(fill="x", pady=(0, 6))

        tk.Label(container, text="Enter your details and a preview of your resume will be\n"
                                  "generated live on your right side.\nUsing a laptop is recommended.",
                 bg=BG_FORM, fg=FG_BLACK, font=("Arial", 10),
                 anchor="w", justify="left").pack(fill="x")

        # Steps
        tk.Label(container, text="\nSteps to Generate Your Resume:",
                 bg=BG_FORM, fg=FG_BLACK, font=("Arial", 13, "bold"),
                 anchor="w").pack(fill="x")

        steps_text = (
            "• Step 1: Fill in your personal information.\n"
            "• Step 2: Copy the LaTeX code.\n"
            "• Step 3: Paste it in a LaTeX editor like Overleaf and Compile.\n"
            "• Step 4: You can use the integrated AI assistant to enhance your resume!"
        )
        tk.Label(container, text=steps_text, bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10), anchor="w", justify="left").pack(fill="x", pady=(2, 8))

    # ─── Helper: labelled form field ──────────────────
    def _add_form_field(self, parent, label_text, placeholder=""):
        tk.Label(parent, text=label_text, bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(6, 2))
        entry = tk.Entry(parent, bg=BG_WHITE, fg=FG_BLACK, font=("Arial", 10),
                          insertbackground=FG_BLACK, bd=1, relief="solid",
                          highlightthickness=1, highlightcolor="#999999",
                          highlightbackground="#bbbbbb")
        entry.pack(fill="x", ipady=5, pady=(0, 2))
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg="#999999")
            entry.bind("<FocusIn>", lambda e, ent=entry, ph=placeholder: self._ph_clear(ent, ph))
            entry.bind("<FocusOut>", lambda e, ent=entry, ph=placeholder: self._ph_set(ent, ph))
        return entry

    def _ph_clear(self, entry, ph):
        if entry.get() == ph:
            entry.delete(0, "end")
            entry.config(fg=FG_BLACK)

    def _ph_set(self, entry, ph):
        if not entry.get():
            entry.insert(0, ph)
            entry.config(fg="#999999")

    def _val(self, entry, placeholder=""):
        """Get entry value, ignoring placeholder text."""
        v = entry.get().strip()
        return "" if v == placeholder else v

    def _set_entry(self, entry, value):
        entry.delete(0, "end")
        entry.config(fg=FG_BLACK)
        if value:
            entry.insert(0, value)

    def _section_header(self, parent, text):
        tk.Label(parent, text=text, bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(14, 4))

    # ═════════════════════════════════════════════════════
    #  PERSONAL DETAILS
    # ═════════════════════════════════════════════════════
    def _build_personal_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        self._section_header(container, "Personal Details")

        self.ent_name    = self._add_form_field(container, "Name", "Enter your name")
        self.ent_year    = self._add_form_field(container, "Current Year", "Eg.: Second Year Undergraduate")
        self.ent_program = self._add_form_field(container, "Program", "Enter your discipline. Eg: Computer Science Engineering")
        self.ent_email   = self._add_form_field(container, "Email Id", "email id")
        self.ent_contact = self._add_form_field(container, "Contact number", "Enter your number")
        self.ent_github  = self._add_form_field(container, "Github", "Paste your GitHub account link")
        self.ent_linkedin = self._add_form_field(container, "LinkedIn", "Paste your LinkedIn account link")
        self.ent_website = self._add_form_field(container, "Website", "Paste your website link")

    # ═════════════════════════════════════════════════════
    #  ACADEMIC DETAILS
    # ═════════════════════════════════════════════════════
    def _build_academic_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        self._section_header(container, "Academic Details")

        # PhD Toggle
        self.phd_var = tk.BooleanVar(value=False)
        phd_row = tk.Frame(container, bg=BG_FORM)
        phd_row.pack(fill="x", pady=(6, 0))
        tk.Label(phd_row, text="PhD", bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(side="left")
        tk.Checkbutton(phd_row, variable=self.phd_var, bg=BG_FORM,
                       activebackground=BG_FORM, command=self._toggle_phd).pack(side="left", padx=8)

        self.phd_frame = tk.Frame(container, bg=BG_FORM)
        self.ent_phd_inst  = self._add_form_field(self.phd_frame, "Institute", "Institute name")
        self.ent_phd_spec  = self._add_form_field(self.phd_frame, "Specialization", "Specialization")
        self.ent_phd_marks = self._add_form_field(self.phd_frame, "CPI / %", "CPI or %")
        self.ent_phd_year  = self._add_form_field(self.phd_frame, "Year", "e.g. 2022-2026")

        # MTech Toggle
        self.mtech_var = tk.BooleanVar(value=False)
        mtech_row = tk.Frame(container, bg=BG_FORM)
        mtech_row.pack(fill="x", pady=(6, 0))
        tk.Label(mtech_row, text="M.Tech", bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(side="left")
        tk.Checkbutton(mtech_row, variable=self.mtech_var, bg=BG_FORM,
                       activebackground=BG_FORM, command=self._toggle_mtech).pack(side="left", padx=8)

        self.mtech_frame = tk.Frame(container, bg=BG_FORM)
        self.ent_mtech_inst  = self._add_form_field(self.mtech_frame, "Institute", "Institute name")
        self.ent_mtech_spec  = self._add_form_field(self.mtech_frame, "Specialization", "Specialization")
        self.ent_mtech_marks = self._add_form_field(self.mtech_frame, "CPI / %", "CPI or %")
        self.ent_mtech_year  = self._add_form_field(self.mtech_frame, "Year", "e.g. 2022-2024")

        # BTech
        tk.Label(container, text="B.Tech", bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.ent_btech_inst  = self._add_form_field(container, "Institute", "Institute name")
        self.ent_btech_spec  = self._add_form_field(container, "Specialization", "Specialization")
        self.ent_btech_marks = self._add_form_field(container, "CPI / %", "CPI or %")
        self.ent_btech_year  = self._add_form_field(container, "Year", "e.g. 2020-2024")

        # Class 12
        tk.Label(container, text="Class XII", bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.ent_12_inst  = self._add_form_field(container, "School / Board", "School name / Board")
        self.ent_12_spec  = self._add_form_field(container, "Stream", "e.g. PCM")
        self.ent_12_marks = self._add_form_field(container, "% / CGPA", "Percentage or CGPA")
        self.ent_12_year  = self._add_form_field(container, "Year", "e.g. 2020")

        # Class 10
        tk.Label(container, text="Class X", bg=BG_FORM, fg=FG_BLACK,
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.ent_10_inst  = self._add_form_field(container, "School / Board", "School name / Board")
        self.ent_10_spec  = self._add_form_field(container, "Stream", "")
        self.ent_10_marks = self._add_form_field(container, "% / CGPA", "Percentage or CGPA")
        self.ent_10_year  = self._add_form_field(container, "Year", "e.g. 2018")

    def _toggle_phd(self):
        if self.phd_var.get():
            # Insert phd_frame right after the PhD checkbox row
            children = self.phd_frame.master.winfo_children()
            # Find the phd checkbox row index
            for i, child in enumerate(children):
                if child == self.phd_frame.master.winfo_children()[1]:  # phd_row
                    break
            self.phd_frame.pack(fill="x", after=children[1])
        else:
            self.phd_frame.pack_forget()
        self._rebuild_preview()

    def _toggle_mtech(self):
        if self.mtech_var.get():
            children = self.mtech_frame.master.winfo_children()
            for i, child in enumerate(children):
                if child == children[3]:  # mtech_row
                    break
            self.mtech_frame.pack(fill="x", after=children[3])
        else:
            self.mtech_frame.pack_forget()
        self._rebuild_preview()

    # ═════════════════════════════════════════════════════
    #  INTERNSHIPS
    # ═════════════════════════════════════════════════════
    def _build_internship_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        # Checkbox to toggle section
        self.intern_var = tk.BooleanVar(value=False)
        row = tk.Frame(container, bg=BG_FORM)
        row.pack(fill="x", pady=(10, 0))
        self._section_header(row, "Internships")
        tk.Checkbutton(row, text="Include", variable=self.intern_var, bg=BG_FORM,
                       activebackground=BG_FORM, font=("Arial", 9),
                       command=self._toggle_internship).pack(side="right", pady=(14, 4))

        self.intern_container = tk.Frame(container, bg=BG_FORM)
        # Form fields
        self.intern_form = tk.Frame(self.intern_container, bg=BG_FORM)
        self.intern_form.pack(fill="x")
        self.ent_intern_title = self._add_form_field(self.intern_form, "Internship Title", "Internship title")
        self.ent_intern_info  = self._add_form_field(self.intern_form, "Company / Guide / Info", "Company or guide")
        self.ent_intern_link  = self._add_form_field(self.intern_form, "Link (optional)", "https://...")
        self.ent_intern_desc1 = self._add_form_field(self.intern_form, "Description Line 1", "Key responsibility / achievement")
        self.ent_intern_desc2 = self._add_form_field(self.intern_form, "Description Line 2 (optional)", "Another line")
        self.ent_intern_year  = self._add_form_field(self.intern_form, "Duration / Year", "e.g. May 2024 - July 2024")

        btn_frame = tk.Frame(self.intern_container, bg=BG_FORM)
        btn_frame.pack(fill="x", pady=6)
        self.intern_add_btn = tk.Button(btn_frame, text="Add Internship", bg=BTN_DARK, fg="white",
                                         font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                         cursor="hand2", activebackground=BTN_HOVER,
                                         command=self._add_internship)
        self.intern_add_btn.pack(side="left", padx=(0, 6))
        self.intern_update_btn = tk.Button(btn_frame, text="Update", bg="#28a745", fg="white",
                                            font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                            cursor="hand2", command=self._update_internship)
        tk.Button(btn_frame, text="✨ AI Enhance", bg="#ffc107", fg=FG_BLACK,
                  font=("Arial", 9, "bold"), bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._ai_enhance("intern")).pack(side="right")

        self.intern_list = tk.Frame(self.intern_container, bg=BG_FORM)
        self.intern_list.pack(fill="x", pady=4)

    def _toggle_internship(self):
        if self.intern_var.get():
            self.intern_container.pack(fill="x")
        else:
            self.intern_container.pack_forget()
            self.internships.clear()
            self._refresh_intern_list()
        self._rebuild_preview()

    def _add_internship(self):
        title = self._val(self.ent_intern_title, "Internship title")
        if not title:
            messagebox.showwarning("Missing", "Please enter an internship title.")
            return
        self.internships.append({
            "id": str(uuid.uuid4()), "title": title,
            "info": self._val(self.ent_intern_info, "Company or guide"),
            "link": self._val(self.ent_intern_link, "https://..."),
            "desc1": self._val(self.ent_intern_desc1, "Key responsibility / achievement"),
            "desc2": self._val(self.ent_intern_desc2, "Another line"),
            "year": self._val(self.ent_intern_year, "e.g. May 2024 - July 2024"),
        })
        self._clear_fields([self.ent_intern_title, self.ent_intern_info, self.ent_intern_link,
                            self.ent_intern_desc1, self.ent_intern_desc2, self.ent_intern_year])
        self._refresh_intern_list()
        self._rebuild_preview()

    def _update_internship(self):
        if self._editing_intern_idx is not None and self._editing_intern_idx < len(self.internships):
            self.internships[self._editing_intern_idx].update({
                "title": self._val(self.ent_intern_title, "Internship title"),
                "info": self._val(self.ent_intern_info, "Company or guide"),
                "link": self._val(self.ent_intern_link, "https://..."),
                "desc1": self._val(self.ent_intern_desc1, "Key responsibility / achievement"),
                "desc2": self._val(self.ent_intern_desc2, "Another line"),
                "year": self._val(self.ent_intern_year, "e.g. May 2024 - July 2024"),
            })
        self._editing_intern_idx = None
        self.intern_update_btn.pack_forget()
        self.intern_add_btn.config(state="normal")
        self._clear_fields([self.ent_intern_title, self.ent_intern_info, self.ent_intern_link,
                            self.ent_intern_desc1, self.ent_intern_desc2, self.ent_intern_year])
        self._refresh_intern_list()
        self._rebuild_preview()

    def _edit_internship(self, idx):
        if idx >= len(self.internships):
            return
        self._editing_intern_idx = idx
        item = self.internships[idx]
        for ent, key in [(self.ent_intern_title, "title"), (self.ent_intern_info, "info"),
                         (self.ent_intern_link, "link"), (self.ent_intern_desc1, "desc1"),
                         (self.ent_intern_desc2, "desc2"), (self.ent_intern_year, "year")]:
            self._set_entry(ent, item[key])
        self.intern_add_btn.config(state="disabled")
        self.intern_update_btn.pack(side="left", padx=(0, 6))

    def _delete_internship(self, idx):
        if idx < len(self.internships):
            title = self.internships[idx]["title"]
            if messagebox.askyesno("Delete", f"Are you sure, you want to delete {title} internship"):
                self.internships.pop(idx)
                self._refresh_intern_list()
                self._rebuild_preview()

    def _refresh_intern_list(self):
        for w in self.intern_list.winfo_children():
            w.destroy()
        for i, item in enumerate(self.internships):
            self._make_card(self.intern_list, i,
                            f"Internship Title-Year: {item['title']} {item['year']}",
                            lambda idx=i: self._edit_internship(idx),
                            lambda idx=i: self._delete_internship(idx))

    # ═════════════════════════════════════════════════════
    #  PROJECTS
    # ═════════════════════════════════════════════════════
    def _build_project_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        self._section_header(container, "Projects")

        self.ent_proj_title = self._add_form_field(container, "Project Title", "Project title")
        self.ent_proj_info  = self._add_form_field(container, "Advisor / Guide", "Advisor or guide name")
        self.ent_proj_link  = self._add_form_field(container, "Link (optional)", "https://...")
        self.ent_proj_desc1 = self._add_form_field(container, "Description Line 1", "Main description")
        self.ent_proj_desc2 = self._add_form_field(container, "Description Line 2 (optional)", "Second line")
        self.ent_proj_year  = self._add_form_field(container, "Duration / Year", "e.g. Jan 2024 - Apr 2024")

        btn_frame = tk.Frame(container, bg=BG_FORM)
        btn_frame.pack(fill="x", pady=6)
        self.proj_add_btn = tk.Button(btn_frame, text="Add Project", bg=BTN_DARK, fg="white",
                                       font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                       cursor="hand2", activebackground=BTN_HOVER,
                                       command=self._add_project)
        self.proj_add_btn.pack(side="left", padx=(0, 6))
        self.proj_update_btn = tk.Button(btn_frame, text="Update", bg="#28a745", fg="white",
                                          font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                          cursor="hand2", command=self._update_project)
        tk.Button(btn_frame, text="✨ AI Enhance", bg="#ffc107", fg=FG_BLACK,
                  font=("Arial", 9, "bold"), bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._ai_enhance("project")).pack(side="right")

        self.proj_list = tk.Frame(container, bg=BG_FORM)
        self.proj_list.pack(fill="x", pady=4)

    def _add_project(self):
        title = self._val(self.ent_proj_title, "Project title")
        if not title:
            messagebox.showwarning("Missing", "Please enter a project title.")
            return
        self.projects.append({
            "id": str(uuid.uuid4()), "title": title,
            "info": self._val(self.ent_proj_info, "Advisor or guide name"),
            "link": self._val(self.ent_proj_link, "https://..."),
            "desc1": self._val(self.ent_proj_desc1, "Main description"),
            "desc2": self._val(self.ent_proj_desc2, "Second line"),
            "year": self._val(self.ent_proj_year, "e.g. Jan 2024 - Apr 2024"),
        })
        self._clear_fields([self.ent_proj_title, self.ent_proj_info, self.ent_proj_link,
                            self.ent_proj_desc1, self.ent_proj_desc2, self.ent_proj_year])
        self._refresh_proj_list()
        self._rebuild_preview()

    def _update_project(self):
        if self._editing_project_idx is not None and self._editing_project_idx < len(self.projects):
            self.projects[self._editing_project_idx].update({
                "title": self._val(self.ent_proj_title, "Project title"),
                "info": self._val(self.ent_proj_info, "Advisor or guide name"),
                "link": self._val(self.ent_proj_link, "https://..."),
                "desc1": self._val(self.ent_proj_desc1, "Main description"),
                "desc2": self._val(self.ent_proj_desc2, "Second line"),
                "year": self._val(self.ent_proj_year, "e.g. Jan 2024 - Apr 2024"),
            })
        self._editing_project_idx = None
        self.proj_update_btn.pack_forget()
        self.proj_add_btn.config(state="normal")
        self._clear_fields([self.ent_proj_title, self.ent_proj_info, self.ent_proj_link,
                            self.ent_proj_desc1, self.ent_proj_desc2, self.ent_proj_year])
        self._refresh_proj_list()
        self._rebuild_preview()

    def _edit_project(self, idx):
        if idx >= len(self.projects):
            return
        self._editing_project_idx = idx
        item = self.projects[idx]
        for ent, key in [(self.ent_proj_title, "title"), (self.ent_proj_info, "info"),
                         (self.ent_proj_link, "link"), (self.ent_proj_desc1, "desc1"),
                         (self.ent_proj_desc2, "desc2"), (self.ent_proj_year, "year")]:
            self._set_entry(ent, item[key])
        self.proj_add_btn.config(state="disabled")
        self.proj_update_btn.pack(side="left", padx=(0, 6))

    def _delete_project(self, idx):
        if idx < len(self.projects):
            if messagebox.askyesno("Delete", f"Delete project \"{self.projects[idx]['title']}\"?"):
                self.projects.pop(idx)
                self._refresh_proj_list()
                self._rebuild_preview()

    def _refresh_proj_list(self):
        for w in self.proj_list.winfo_children():
            w.destroy()
        for i, item in enumerate(self.projects):
            self._make_card(self.proj_list, i,
                            f"Project Title-Year: {item['title']} {item['year']}",
                            lambda idx=i: self._edit_project(idx),
                            lambda idx=i: self._delete_project(idx))

    # ═════════════════════════════════════════════════════
    #  TECHNICAL SKILLS
    # ═════════════════════════════════════════════════════
    def _build_skills_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        self._section_header(container, "Technical Skills")

        self.ent_skill_type = self._add_form_field(container, "Skill Type", "e.g. Programming Languages")
        self.ent_skill_desc = self._add_form_field(container, "Skills", "e.g. Python, C++, Java")

        btn_frame = tk.Frame(container, bg=BG_FORM)
        btn_frame.pack(fill="x", pady=6)
        self.skill_add_btn = tk.Button(btn_frame, text="Add Skill", bg=BTN_DARK, fg="white",
                                        font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                        cursor="hand2", activebackground=BTN_HOVER,
                                        command=self._add_skill)
        self.skill_add_btn.pack(side="left", padx=(0, 6))
        self.skill_update_btn = tk.Button(btn_frame, text="Update", bg="#28a745", fg="white",
                                           font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                           cursor="hand2", command=self._update_skill)
        tk.Button(btn_frame, text="✨ AI Enhance", bg="#ffc107", fg=FG_BLACK,
                  font=("Arial", 9, "bold"), bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._ai_enhance("skill")).pack(side="right")

        self.skill_list = tk.Frame(container, bg=BG_FORM)
        self.skill_list.pack(fill="x", pady=4)

    def _add_skill(self):
        stype = self._val(self.ent_skill_type, "e.g. Programming Languages")
        if not stype:
            messagebox.showwarning("Missing", "Please enter a skill type.")
            return
        self.skills.append({
            "id": str(uuid.uuid4()),
            "type": stype,
            "desc": self._val(self.ent_skill_desc, "e.g. Python, C++, Java"),
        })
        self._clear_fields([self.ent_skill_type, self.ent_skill_desc])
        self._refresh_skill_list()
        self._rebuild_preview()

    def _update_skill(self):
        if self._editing_skill_idx is not None and self._editing_skill_idx < len(self.skills):
            self.skills[self._editing_skill_idx].update({
                "type": self._val(self.ent_skill_type, "e.g. Programming Languages"),
                "desc": self._val(self.ent_skill_desc, "e.g. Python, C++, Java"),
            })
        self._editing_skill_idx = None
        self.skill_update_btn.pack_forget()
        self.skill_add_btn.config(state="normal")
        self._clear_fields([self.ent_skill_type, self.ent_skill_desc])
        self._refresh_skill_list()
        self._rebuild_preview()

    def _edit_skill(self, idx):
        if idx >= len(self.skills):
            return
        self._editing_skill_idx = idx
        self._set_entry(self.ent_skill_type, self.skills[idx]["type"])
        self._set_entry(self.ent_skill_desc, self.skills[idx]["desc"])
        self.skill_add_btn.config(state="disabled")
        self.skill_update_btn.pack(side="left", padx=(0, 6))

    def _delete_skill(self, idx):
        if idx < len(self.skills):
            if messagebox.askyesno("Delete", f"Delete skill \"{self.skills[idx]['type']}\"?"):
                self.skills.pop(idx)
                self._refresh_skill_list()
                self._rebuild_preview()

    def _refresh_skill_list(self):
        for w in self.skill_list.winfo_children():
            w.destroy()
        for i, item in enumerate(self.skills):
            self._make_card(self.skill_list, i, f"{item['type']}: {item['desc']}",
                            lambda idx=i: self._edit_skill(idx),
                            lambda idx=i: self._delete_skill(idx))

    # ═════════════════════════════════════════════════════
    #  POSITIONS OF RESPONSIBILITY
    # ═════════════════════════════════════════════════════
    def _build_por_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=2)

        self._section_header(container, "Positions of Responsibility")

        self.ent_por_name  = self._add_form_field(container, "Position Title", "e.g. Team Lead")
        self.ent_por_desc1 = self._add_form_field(container, "Description Line 1", "Responsibility description")
        self.ent_por_desc2 = self._add_form_field(container, "Description Line 2 (optional)", "Second line")
        self.ent_por_year  = self._add_form_field(container, "Duration", "e.g. Aug 2023 - Present")

        btn_frame = tk.Frame(container, bg=BG_FORM)
        btn_frame.pack(fill="x", pady=6)
        self.por_add_btn = tk.Button(btn_frame, text="Add POR", bg=BTN_DARK, fg="white",
                                      font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                      cursor="hand2", activebackground=BTN_HOVER,
                                      command=self._add_por)
        self.por_add_btn.pack(side="left", padx=(0, 6))
        self.por_update_btn = tk.Button(btn_frame, text="Update", bg="#28a745", fg="white",
                                         font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                         cursor="hand2", command=self._update_por)
        tk.Button(btn_frame, text="✨ AI Enhance", bg="#ffc107", fg=FG_BLACK,
                  font=("Arial", 9, "bold"), bd=0, padx=10, pady=4,
                  cursor="hand2", command=lambda: self._ai_enhance("por")).pack(side="right")

        self.por_list = tk.Frame(container, bg=BG_FORM)
        self.por_list.pack(fill="x", pady=4)

    def _add_por(self):
        name = self._val(self.ent_por_name, "e.g. Team Lead")
        if not name:
            messagebox.showwarning("Missing", "Please enter a position title.")
            return
        self.pors.append({
            "id": str(uuid.uuid4()), "name": name,
            "desc1": self._val(self.ent_por_desc1, "Responsibility description"),
            "desc2": self._val(self.ent_por_desc2, "Second line"),
            "year": self._val(self.ent_por_year, "e.g. Aug 2023 - Present"),
        })
        self._clear_fields([self.ent_por_name, self.ent_por_desc1, self.ent_por_desc2, self.ent_por_year])
        self._refresh_por_list()
        self._rebuild_preview()

    def _update_por(self):
        if self._editing_por_idx is not None and self._editing_por_idx < len(self.pors):
            self.pors[self._editing_por_idx].update({
                "name": self._val(self.ent_por_name, "e.g. Team Lead"),
                "desc1": self._val(self.ent_por_desc1, "Responsibility description"),
                "desc2": self._val(self.ent_por_desc2, "Second line"),
                "year": self._val(self.ent_por_year, "e.g. Aug 2023 - Present"),
            })
        self._editing_por_idx = None
        self.por_update_btn.pack_forget()
        self.por_add_btn.config(state="normal")
        self._clear_fields([self.ent_por_name, self.ent_por_desc1, self.ent_por_desc2, self.ent_por_year])
        self._refresh_por_list()
        self._rebuild_preview()

    def _edit_por(self, idx):
        if idx >= len(self.pors):
            return
        self._editing_por_idx = idx
        item = self.pors[idx]
        for ent, key in [(self.ent_por_name, "name"), (self.ent_por_desc1, "desc1"),
                         (self.ent_por_desc2, "desc2"), (self.ent_por_year, "year")]:
            self._set_entry(ent, item[key])
        self.por_add_btn.config(state="disabled")
        self.por_update_btn.pack(side="left", padx=(0, 6))

    def _delete_por(self, idx):
        if idx < len(self.pors):
            if messagebox.askyesno("Delete", f"Delete POR \"{self.pors[idx]['name']}\"?"):
                self.pors.pop(idx)
                self._refresh_por_list()
                self._rebuild_preview()

    def _refresh_por_list(self):
        for w in self.por_list.winfo_children():
            w.destroy()
        for i, item in enumerate(self.pors):
            self._make_card(self.por_list, i, f"{item['name']} — {item['year']}",
                            lambda idx=i: self._edit_por(idx),
                            lambda idx=i: self._delete_por(idx))

    # ═════════════════════════════════════════════════════
    #  ACHIEVEMENTS
    # ═════════════════════════════════════════════════════
    def _build_achievements_section(self):
        container = tk.Frame(self.form, bg=BG_FORM)
        container.pack(fill="x", padx=12, pady=(2, 20))

        self._section_header(container, "Achievements & Extra-Curriculars")

        self.ent_ach_name = self._add_form_field(container, "Achievement", "Describe your achievement")

        btn_frame = tk.Frame(container, bg=BG_FORM)
        btn_frame.pack(fill="x", pady=6)
        self.ach_add_btn = tk.Button(btn_frame, text="Add Achievement", bg=BTN_DARK, fg="white",
                                      font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                      cursor="hand2", activebackground=BTN_HOVER,
                                      command=self._add_ach)
        self.ach_add_btn.pack(side="left", padx=(0, 6))
        self.ach_update_btn = tk.Button(btn_frame, text="Update", bg="#28a745", fg="white",
                                         font=("Arial", 10, "bold"), bd=0, padx=14, pady=5,
                                         cursor="hand2", command=self._update_ach)

        self.ach_list = tk.Frame(container, bg=BG_FORM)
        self.ach_list.pack(fill="x", pady=4)

    def _add_ach(self):
        name = self._val(self.ent_ach_name, "Describe your achievement")
        if not name:
            messagebox.showwarning("Missing", "Please enter an achievement.")
            return
        self.achievements.append({"id": str(uuid.uuid4()), "name": name})
        self.ent_ach_name.delete(0, "end")
        self._refresh_ach_list()
        self._rebuild_preview()

    def _update_ach(self):
        if self._editing_ach_idx is not None and self._editing_ach_idx < len(self.achievements):
            self.achievements[self._editing_ach_idx]["name"] = self._val(self.ent_ach_name, "Describe your achievement")
        self._editing_ach_idx = None
        self.ach_update_btn.pack_forget()
        self.ach_add_btn.config(state="normal")
        self.ent_ach_name.delete(0, "end")
        self._refresh_ach_list()
        self._rebuild_preview()

    def _edit_ach(self, idx):
        if idx >= len(self.achievements):
            return
        self._editing_ach_idx = idx
        self._set_entry(self.ent_ach_name, self.achievements[idx]["name"])
        self.ach_add_btn.config(state="disabled")
        self.ach_update_btn.pack(side="left", padx=(0, 6))

    def _delete_ach(self, idx):
        if idx < len(self.achievements):
            if messagebox.askyesno("Delete", "Delete this achievement?"):
                self.achievements.pop(idx)
                self._refresh_ach_list()
                self._rebuild_preview()

    def _refresh_ach_list(self):
        for w in self.ach_list.winfo_children():
            w.destroy()
        for i, item in enumerate(self.achievements):
            self._make_card(self.ach_list, i, item["name"],
                            lambda idx=i: self._edit_ach(idx),
                            lambda idx=i: self._delete_ach(idx))

    # ═════════════════════════════════════════════════════
    #  Generic list-item card (edit / delete)
    # ═════════════════════════════════════════════════════
    def _make_card(self, parent, index, text, edit_cmd, delete_cmd):
        card = tk.Frame(parent, bg=BG_WHITE, bd=1, relief="solid",
                        highlightthickness=0)
        card.pack(fill="x", pady=3, ipady=3)

        tk.Label(card, text=text, bg=BG_WHITE, fg=FG_BLACK,
                 font=("Arial", 10, "bold"), anchor="w",
                 wraplength=340).pack(side="left", fill="x", expand=True, padx=8, pady=2)

        btn_box = tk.Frame(card, bg=BG_WHITE)
        btn_box.pack(side="right", padx=6)
        tk.Button(btn_box, text="Edit", bg=BTN_DARK, fg="white", font=("Arial", 9),
                  bd=0, padx=8, pady=2, cursor="hand2", command=edit_cmd).pack(side="left", padx=2)
        tk.Button(btn_box, text="Delete", bg=BTN_DARK, fg="white", font=("Arial", 9),
                  bd=0, padx=8, pady=2, cursor="hand2", command=delete_cmd).pack(side="left", padx=2)

    def _clear_fields(self, entries):
        for e in entries:
            e.delete(0, "end")

    # ═════════════════════════════════════════════════════
    #  RIGHT PANEL — Resume Preview (visual)
    # ═════════════════════════════════════════════════════
    def _rebuild_preview(self):
        """Rebuild the visual resume preview on the right side."""
        for w in self.preview_frame.winfo_children():
            w.destroy()

        pf = self.preview_frame  # shorthand
        pad_x = 16

        # ── Title ──
        tk.Label(pf, text="Resume Preview", bg=BG_WHITE, fg=FG_BLACK,
                 font=("Arial", 22, "bold")).pack(pady=(16, 2))
        tk.Label(pf, text="A rough preview. Differs from the LaTeX output.\n"
                          "Check the LaTeX code for a clean and professional resume.",
                 bg=BG_WHITE, fg=FG_DIM, font=("Arial", 9), justify="center").pack(pady=(0, 12))

        # ── Personal header ──
        name    = self._val(self.ent_name, "Enter your name")
        year    = self._val(self.ent_year, "Eg.: Second Year Undergraduate")
        program = self._val(self.ent_program, "Enter your discipline. Eg: Computer Science Engineering")
        email   = self._val(self.ent_email, "email id")
        contact = self._val(self.ent_contact, "Enter your number")

        header = tk.Frame(pf, bg=BG_WHITE)
        header.pack(fill="x", padx=pad_x, pady=(0, 4))

        if name:
            tk.Label(header, text=name, bg=BG_WHITE, fg=FG_BLACK,
                     font=("Arial", 14, "bold")).pack(anchor="w")

        # Row: year/program left, email right
        row1 = tk.Frame(header, bg=BG_WHITE)
        row1.pack(fill="x")
        left_txt = ""
        if year:
            left_txt = year
        tk.Label(row1, text=left_txt, bg=BG_WHITE, fg=FG_BLACK,
                 font=("Arial", 10)).pack(side="left")
        if email:
            tk.Label(row1, text=email, bg=BG_WHITE, fg=LINK_BLUE,
                     font=("Arial", 10)).pack(side="right")

        row2 = tk.Frame(header, bg=BG_WHITE)
        row2.pack(fill="x")
        if program:
            tk.Label(row2, text=f"Discipline of {program}", bg=BG_WHITE, fg=FG_BLACK,
                     font=("Arial", 10, "italic")).pack(side="left")
        if contact:
            tk.Label(row2, text=contact, bg=BG_WHITE, fg=FG_BLACK,
                     font=("Arial", 10)).pack(side="right")

        # Links row
        link_row = tk.Frame(header, bg=BG_WHITE)
        link_row.pack(fill="x")
        tk.Label(link_row, text="Indian Institute of Technology, Gandhinagar",
                 bg=BG_WHITE, fg=FG_BLACK, font=("Arial", 10)).pack(side="left")

        links_frame = tk.Frame(link_row, bg=BG_WHITE)
        links_frame.pack(side="right")
        for label in ["LinkedIn", "Github", "Website"]:
            lbl = tk.Label(links_frame, text=label, bg=BG_WHITE, fg=LINK_BLUE,
                           font=("Arial", 10, "underline"), cursor="hand2")
            lbl.pack(side="left", padx=4)
            sep = tk.Label(links_frame, text="|", bg=BG_WHITE, fg=FG_DIM, font=("Arial", 10))
            sep.pack(side="left")
        # Remove last separator
        if links_frame.winfo_children():
            links_frame.winfo_children()[-1].destroy()

        # ── Section: Academic Details ──
        self._preview_section_header(pf, "ACADEMIC DETAILS")
        self._preview_academic_table(pf)

        # ── Section: Internships ──
        if self.intern_var.get():
            self._preview_section_header(pf, "INTERNSHIPS")
            if self.internships:
                for item in self.internships:
                    self._preview_item_block(pf, item)
            else:
                self._preview_placeholder(pf)

        # ── Section: Projects ──
        self._preview_section_header(pf, "PROJECTS")
        if self.projects:
            for item in self.projects:
                self._preview_item_block(pf, item)
        else:
            self._preview_placeholder(pf)

        # ── Section: Skills ──
        self._preview_section_header(pf, "SKILLS")
        if self.skills:
            for s in self.skills:
                sk_frame = tk.Frame(pf, bg=BG_WHITE)
                sk_frame.pack(fill="x", padx=pad_x + 12, pady=1)
                tk.Label(sk_frame, text=f"• {s['type']}: ", bg=BG_WHITE, fg=FG_BLACK,
                         font=("Arial", 10, "bold")).pack(side="left")
                tk.Label(sk_frame, text=s['desc'], bg=BG_WHITE, fg=FG_BLACK,
                         font=("Arial", 10)).pack(side="left")
        else:
            self._preview_placeholder(pf)

        # ── Section: Positions of Responsibility ──
        self._preview_section_header(pf, "POSITIONS OF RESPONSIBILITY")
        if self.pors:
            for por in self.pors:
                block = tk.Frame(pf, bg=BG_WHITE)
                block.pack(fill="x", padx=pad_x + 12, pady=2)
                row = tk.Frame(block, bg=BG_WHITE)
                row.pack(fill="x")
                tk.Label(row, text=f"• {por['name']}", bg=BG_WHITE, fg=FG_BLACK,
                         font=("Arial", 10, "bold")).pack(side="left")
                if por['year']:
                    tk.Label(row, text=por['year'], bg=BG_WHITE, fg=FG_DIM,
                             font=("Arial", 10, "italic")).pack(side="right")
                for desc_key in ['desc1', 'desc2']:
                    if por.get(desc_key):
                        tk.Label(block, text=f"    ◦ {por[desc_key]}", bg=BG_WHITE, fg=FG_BLACK,
                                 font=("Arial", 9), anchor="w", wraplength=500).pack(anchor="w", padx=16)
        else:
            self._preview_placeholder(pf)

        # ── Section: Achievements ──
        self._preview_section_header(pf, "ACHIEVEMENTS")
        if self.achievements:
            for ach in self.achievements:
                tk.Label(pf, text=f"  • {ach['name']}", bg=BG_WHITE, fg=FG_BLACK,
                         font=("Arial", 10), anchor="w", wraplength=500).pack(fill="x", padx=pad_x + 12, pady=1)
        else:
            self._preview_placeholder(pf)

        # ── Copy Button ──
        tk.Frame(pf, bg=BG_WHITE, height=16).pack(fill="x")
        copy_btn = tk.Button(pf, text="Copy LaTeX Code to Clipboard",
                              bg=BTN_DARK, fg="white", font=("Arial", 13, "bold"),
                              bd=0, padx=30, pady=10, cursor="hand2",
                              activebackground=BTN_HOVER, command=self._copy_latex)
        copy_btn.pack(pady=(8, 20))
        tk.Frame(pf, bg=BG_WHITE, height=20).pack(fill="x")

    def _preview_section_header(self, parent, text):
        hdr = tk.Frame(parent, bg=BG_GREY)
        hdr.pack(fill="x", padx=16, pady=(8, 2))
        tk.Label(hdr, text=f"  {text}", bg=BG_GREY, fg=FG_BLACK,
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x", ipady=3)

    def _preview_academic_table(self, parent):
        table = tk.Frame(parent, bg=BG_WHITE)
        table.pack(fill="x", padx=16, pady=(4, 4))

        # Header row
        headers = ["Degree", "Institute", "CPI/%", "Year"]
        hdr_row = tk.Frame(table, bg=BG_WHITE)
        hdr_row.pack(fill="x")
        for i, h in enumerate(headers):
            w = [120, 260, 80, 80][i]
            tk.Label(hdr_row, text=h, bg=BG_WHITE, fg=FG_BLACK,
                     font=("Arial", 10, "bold"), width=w // 8, anchor="w").pack(side="left")

        # Separator
        tk.Frame(table, bg="#cccccc", height=1).pack(fill="x", pady=2)

        # PhD row
        if self.phd_var.get():
            self._preview_table_row(table, "PhD",
                                     self._val(self.ent_phd_inst, "Institute name"),
                                     self._val(self.ent_phd_marks, "CPI or %"),
                                     self._val(self.ent_phd_year, "e.g. 2022-2026"))

        # MTech row
        if self.mtech_var.get():
            self._preview_table_row(table, "M.Tech",
                                     self._val(self.ent_mtech_inst, "Institute name"),
                                     self._val(self.ent_mtech_marks, "CPI or %"),
                                     self._val(self.ent_mtech_year, "e.g. 2022-2024"))

        # BTech row
        self._preview_table_row(table, "B.Tech",
                                 self._val(self.ent_btech_inst, "Institute name"),
                                 self._val(self.ent_btech_marks, "CPI or %"),
                                 self._val(self.ent_btech_year, "e.g. 2020-2024"))

        # Class XII
        self._preview_table_row(table, "Class XII",
                                 self._val(self.ent_12_inst, "School name / Board"),
                                 self._val(self.ent_12_marks, "Percentage or CGPA"),
                                 self._val(self.ent_12_year, "e.g. 2020"))

        # Class X
        self._preview_table_row(table, "Class X",
                                 self._val(self.ent_10_inst, "School name / Board"),
                                 self._val(self.ent_10_marks, "Percentage or CGPA"),
                                 self._val(self.ent_10_year, "e.g. 2018"))

    def _preview_table_row(self, parent, degree, institute, marks, year):
        row = tk.Frame(parent, bg=BG_WHITE)
        row.pack(fill="x")
        for val, w in [(degree, 120), (institute, 260), (marks, 80), (year, 80)]:
            tk.Label(row, text=val if val else "", bg=BG_WHITE, fg=FG_BLACK,
                     font=("Arial", 10), width=w // 8, anchor="w").pack(side="left")

    def _preview_item_block(self, parent, item):
        """Render an internship/project block in the preview."""
        block = tk.Frame(parent, bg=BG_WHITE)
        block.pack(fill="x", padx=28, pady=2)
        row = tk.Frame(block, bg=BG_WHITE)
        row.pack(fill="x")
        title_text = f"• {item.get('title', '')}"
        if item.get('info'):
            title_text += f" — {item['info']}"
        tk.Label(row, text=title_text, bg=BG_WHITE, fg=FG_BLACK,
                 font=("Arial", 10, "bold"), anchor="w").pack(side="left")
        if item.get('year'):
            tk.Label(row, text=item['year'], bg=BG_WHITE, fg=FG_DIM,
                     font=("Arial", 10, "italic")).pack(side="right")
        for desc_key in ['desc1', 'desc2']:
            if item.get(desc_key):
                tk.Label(block, text=f"    ◦ {item[desc_key]}", bg=BG_WHITE, fg=FG_BLACK,
                         font=("Arial", 9), anchor="w", wraplength=500).pack(anchor="w", padx=16)

    def _preview_placeholder(self, parent):
        """Empty placeholder for a section with no items yet."""
        pass  # Just leave blank — matches original behavior

    # ═════════════════════════════════════════════════════
    #  LaTeX GENERATION (exact original template)
    # ═════════════════════════════════════════════════════
    def _generate_latex(self) -> str:
        name    = latex_escape(self._val(self.ent_name, "Enter your name"))
        year    = latex_escape(self._val(self.ent_year, "Eg.: Second Year Undergraduate"))
        program = latex_escape(self._val(self.ent_program, "Enter your discipline. Eg: Computer Science Engineering"))
        email   = self._val(self.ent_email, "email id")
        contact = latex_escape(self._val(self.ent_contact, "Enter your number"))
        github  = self._val(self.ent_github, "Paste your GitHub account link")
        linkedin = self._val(self.ent_linkedin, "Paste your LinkedIn account link")
        website = self._val(self.ent_website, "Paste your website link")

        L = []
        # ── Preamble ──
        L.append(r"\documentclass[a4paper,10pt]{article}")
        L.append(r"%-----------------------------------------------------------")
        L.append(r"\usepackage[top=0.1cm, bottom=0.3cm, left=0.3cm, right=1.1cm, nohead, nofoot]{geometry}")
        L.append(r"\usepackage{graphicx}")
        L.append(r"\usepackage{url}")
        L.append(r"\usepackage{palatino}")
        L.append(r"\usepackage{booktabs}")
        L.append(r"\usepackage{hyperref}")
        L.append(r"\fontfamily{SansSerif}")
        L.append(r"\selectfont")
        L.append("")
        L.append(r"\usepackage[T1]{fontenc}")
        L.append(r"\usepackage[utf8]{inputenc}")
        L.append("")
        L.append(r"\usepackage{color}")
        L.append(r"\definecolor{mygrey}{gray}{0.75}")
        L.append(r"\textheight = 29.1 cm")
        L.append(r"\raggedbottom")
        L.append("")
        L.append(r"\setlength{\tabcolsep}{0in}")
        L.append(r"\newcommand{\isep}{-2 pt}")
        L.append(r"\newcommand{\lsep}{-0.6cm}")
        L.append(r"\newcommand{\psep}{-0.6cm}")
        L.append(r"\renewcommand{\labelitemii}{$\circ$}")
        L.append("")
        L.append(r"\pagestyle{empty}")
        L.append(r"%-----------------------------------------------------------")
        L.append(r"%Custom commands")
        L.append(r"\newcommand{\resitem}[1]{\item #1 \vspace{-2pt}}")
        L.append(r"\newcommand{\resheading}[1]{{\small \colorbox{mygrey}{\begin{minipage}{0.965\textwidth}{\textbf{#1 \vphantom{p\^{E}}}}\end{minipage}}}}")
        L.append(r"\newcommand{\ressubheading}[3]{")
        L.append(r"\begin{tabular*}{6.62in}{l @{\extracolsep{\fill}} r}")
        L.append(r"    \textsc{{\textbf{#1}}} & \textsc{\textit{[#2]}} \\")
        L.append(r"\end{tabular*}\vspace{-9pt}}")
        L.append(r"%-----------------------------------------------------------")
        L.append("")
        L.append(r"\begin{document}")
        L.append(r"\hspace{0.75cm}\\[-0.54cm]")
        L.append("")

        # ── Header ──
        L.append(rf"\textbf{{{name}}} \\")
        L.append(rf"\indent {year} \hfill ")
        L.append(rf"\href{{mailto:{email}}}{{{latex_escape(email)}}}\\  ")
        L.append(rf"\indent Discipline of {program} \hfill {contact}  \\")
        L.append(rf"\indent Indian Institute of Technology, Gandhinagar  \hfill")
        L.append(rf"\underline{{\href{{{linkedin}}}{{LinkedIn}}}} |")
        L.append(rf"\underline{{\href{{{github}}}{{Github}}}} | \underline{{\href{{{website}}}{{Website}}}}")
        L.append(r"\\")

        # ── ACADEMIC DETAILS ──
        L.append(r"\indent \resheading{\textbf{ACADEMIC DETAILS} }\\[\lsep]")
        L.append(r"\\ \\")
        L.append(r"%\begin{table}[ht!]")
        L.append(r"%\begin{center}")
        L.append(r"\indent \begin{tabular}{ p{1.7cm} @{\hskip 0.08in} p{5.254cm} @{\hskip 0.08in} p{7.054cm} @{\hskip 0.09in} p{2.554cm} @{\hskip 0.08in} p{1.72cm} }")
        L.append(r"\toprule")
        L.append(r"\textbf{Degree} & \textbf{Specialization} & \textbf{Institute} & \textbf{Year} & \textbf{CPI/\%} \\")
        L.append(r"\midrule")
        L.append("")

        # PhD row
        if self.phd_var.get():
            pi = latex_escape(self._val(self.ent_phd_inst, "Institute name"))
            ps = latex_escape(self._val(self.ent_phd_spec, "Specialization"))
            pm = latex_escape(self._val(self.ent_phd_marks, "CPI or %"))
            py = latex_escape(self._val(self.ent_phd_year, "e.g. 2022-2026"))
            L.append(rf"PhD & \textit{{{ps}}} & {pi} & {py} & {pm} \\")

        # MTech row
        if self.mtech_var.get():
            mi = latex_escape(self._val(self.ent_mtech_inst, "Institute name"))
            ms = latex_escape(self._val(self.ent_mtech_spec, "Specialization"))
            mm = latex_escape(self._val(self.ent_mtech_marks, "CPI or %"))
            my_ = latex_escape(self._val(self.ent_mtech_year, "e.g. 2022-2024"))
            L.append(rf"M.Tech. & \textit{{{ms}}} & {mi} & {my_} & {mm} \\")

        # BTech row
        bi = latex_escape(self._val(self.ent_btech_inst, "Institute name"))
        bs = latex_escape(self._val(self.ent_btech_spec, "Specialization"))
        bm = latex_escape(self._val(self.ent_btech_marks, "CPI or %"))
        by = latex_escape(self._val(self.ent_btech_year, "e.g. 2020-2024"))
        L.append(rf"B.Tech. & \textit{{{bs}}} & {bi} & {by} & {bm} \\")

        # Class XII
        c12i = latex_escape(self._val(self.ent_12_inst, "School name / Board"))
        c12s = latex_escape(self._val(self.ent_12_spec, "e.g. PCM"))
        c12m = latex_escape(self._val(self.ent_12_marks, "Percentage or CGPA"))
        c12y = latex_escape(self._val(self.ent_12_year, "e.g. 2020"))
        if not c12s:
            c12s = "Physics, Chemistry, Maths"
        L.append(rf"Class XII  & \textit{{{c12s}}} & {c12i} & {c12y} & {c12m} \\")

        # Class X
        c10i = latex_escape(self._val(self.ent_10_inst, "School name / Board"))
        c10s = latex_escape(self._val(self.ent_10_spec, ""))
        c10m = latex_escape(self._val(self.ent_10_marks, "Percentage or CGPA"))
        c10y = latex_escape(self._val(self.ent_10_year, "e.g. 2018"))
        L.append(rf"Class X  & {c10s} & {c10i} & {c10y} & {c10m} \\")

        L.append(r"\bottomrule")
        L.append(r"\end{tabular}")
        L.append("")

        # ── INTERNSHIPS ──
        if self.intern_var.get():
            L.append("")
            L.append(r"\resheading{\textbf{ INTERNSHIPS} }")
            L.append(r"\vspace{-0.4cm}")
            L.append(r"\begin{itemize}\itemsep\isep")
            if self.internships:
                for it in self.internships:
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
                    if d1:
                        L.append(rf"\item {d1}")
                    if d2:
                        L.append(rf"\item {d2}")
                    L.append(r"\end{itemize}")
            L.append(r"\end{itemize}")

        # ── PROJECTS ──
        L.append("")
        L.append(r"\resheading{\textbf{ PROJECTS} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize}\itemsep\isep")
        if self.projects:
            for p in self.projects:
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
                if d1:
                    L.append(rf"\item {d1}")
                if d2:
                    L.append(rf"\item {d2}")
                L.append(r"\end{itemize}")
        L.append(r"\end{itemize}")

        # ── TECHNICAL SKILLS ──
        L.append("")
        L.append(r"\resheading{\textbf{TECHNICAL SKILLS} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize} \itemsep \isep")
        if self.skills:
            for s in self.skills:
                st = latex_escape(s["type"])
                sd = latex_escape(s["desc"])
                L.append(rf"\item \textbf{{{st}:}} {sd}")
        L.append(r"\end{itemize}")

        # ── POSITIONS OF RESPONSIBILITY ──
        L.append("")
        L.append(r"\resheading{\textbf{POSITIONS OF RESPONSIBILITY} }")
        L.append(r"\vspace{-0.4cm}")
        L.append(r"\begin{itemize} \itemsep \isep")
        if self.pors:
            for por in self.pors:
                n = latex_escape(por["name"])
                yr = latex_escape(por["year"])
                d1 = latex_escape(por["desc1"])
                d2 = latex_escape(por["desc2"])
                L.append(rf"\item \textbf{{{n}}} \hfill \textit{{{yr}}}")
                L.append(r"\begin{itemize}\itemsep\isep")
                if d1:
                    L.append(rf"\item {d1}")
                if d2:
                    L.append(rf"\item {d2}")
                L.append(r"\end{itemize}")
        L.append(r"\end{itemize}")

        # ── ACHIEVEMENTS ──
        L.append("")
        L.append(r"\resheading{\textbf{ACHIEVEMENTS} }")
        L.append(r"\begin{itemize}\itemsep\isep")
        if self.achievements:
            for ach in self.achievements:
                n = latex_escape(ach["name"])
                L.append(rf"\item {n}")
        L.append(r"\end{itemize}")

        L.append(r"\end{document}")

        return "\n".join(L)

    def _copy_latex(self):
        latex = self._generate_latex()
        self.root.clipboard_clear()
        self.root.clipboard_append(latex)
        messagebox.showinfo("Copied!",
                            "LaTeX code copied to clipboard!\n\n"
                            "Paste it into Overleaf or any LaTeX editor and compile.")

    # ═════════════════════════════════════════════════════
    #  AI ENHANCEMENT (Groq API)
    # ═════════════════════════════════════════════════════
    def _ai_enhance(self, section: str):
        if not HAS_REQUESTS:
            messagebox.showwarning("Missing Library",
                                   "The 'requests' library is not installed.\n\n"
                                   "Install with:  pip install requests")
            return
        if not self.groq_key or self.groq_key == "your-groq-api-key-here":
            messagebox.showwarning("Missing API Key",
                                   "No Groq API key found.\n\n"
                                   "Edit secrets.json next to main.py:\n"
                                   '{ "GROQ_KEY": "gsk_..." }')
            return

        # Gather text to enhance
        if section == "intern":
            items = self.internships
            if not items:
                messagebox.showinfo("Nothing to enhance", "Add at least one internship first.")
                return
            text_parts = []
            for e in items:
                text_parts.append(f"Title: {e['title']}")
                if e['desc1']: text_parts.append(f"Description 1: {e['desc1']}")
                if e['desc2']: text_parts.append(f"Description 2: {e['desc2']}")
            ctx = "internship descriptions for a professional resume"
        elif section == "project":
            items = self.projects
            if not items:
                messagebox.showinfo("Nothing to enhance", "Add at least one project first.")
                return
            text_parts = []
            for e in items:
                text_parts.append(f"Title: {e['title']}")
                if e['desc1']: text_parts.append(f"Description 1: {e['desc1']}")
                if e['desc2']: text_parts.append(f"Description 2: {e['desc2']}")
            ctx = "project descriptions for a professional resume"
        elif section == "skill":
            items = self.skills
            if not items:
                messagebox.showinfo("Nothing to enhance", "Add at least one skill first.")
                return
            text_parts = [f"{e['type']}: {e['desc']}" for e in items]
            ctx = "technical skills section for a professional resume"
        elif section == "por":
            items = self.pors
            if not items:
                messagebox.showinfo("Nothing to enhance", "Add at least one POR first.")
                return
            text_parts = []
            for e in items:
                text_parts.append(f"Position: {e['name']}")
                if e['desc1']: text_parts.append(f"Description 1: {e['desc1']}")
                if e['desc2']: text_parts.append(f"Description 2: {e['desc2']}")
            ctx = "positions of responsibility descriptions for a professional resume"
        else:
            return

        user_text = "\n".join(text_parts)
        system_prompt = (
            "You are a professional resume writing assistant. "
            f"Improve the following {ctx}. "
            "Make them more impactful, use strong action verbs, quantify results where possible, "
            "and keep each description concise (1-2 lines max). "
            "Return ONLY the improved text in the same format with no extra commentary. "
            "Keep the same number of entries."
        )

        try:
            resp = req_lib.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            enhanced = result["choices"][0]["message"]["content"].strip()
            self._show_ai_result(section, enhanced, items)
        except Exception as e:
            messagebox.showerror("AI Enhancement Failed", f"Error: {str(e)}")

    def _show_ai_result(self, section, enhanced_text, entries):
        popup = tk.Toplevel(self.root)
        popup.title("AI Enhanced Text")
        popup.geometry("620x480")
        popup.configure(bg=BG_WHITE)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="AI Enhanced Descriptions", bg=BG_WHITE, fg=FG_BLACK,
                 font=("Arial", 14, "bold")).pack(pady=(14, 4))
        tk.Label(popup, text="Review the enhanced text. Click Apply to use it.",
                 bg=BG_WHITE, fg=FG_DIM, font=("Arial", 10)).pack(pady=(0, 8))

        text_widget = tk.Text(popup, bg="#f8f8f8", fg=FG_BLACK,
                               font=("Consolas", 10), wrap="word", bd=1, relief="solid",
                               padx=10, pady=8)
        text_widget.pack(fill="both", expand=True, padx=14, pady=4)
        text_widget.insert("1.0", enhanced_text)

        btn_frame = tk.Frame(popup, bg=BG_WHITE)
        btn_frame.pack(fill="x", padx=14, pady=10)

        def apply():
            new_text = text_widget.get("1.0", "end").strip()
            self._apply_ai(section, new_text, entries)
            popup.destroy()

        tk.Button(btn_frame, text="Apply Changes", bg="#28a745", fg="white",
                  font=("Arial", 10, "bold"), bd=0, padx=16, pady=6,
                  cursor="hand2", command=apply).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Discard", bg="#dc3545", fg="white",
                  font=("Arial", 10, "bold"), bd=0, padx=16, pady=6,
                  cursor="hand2", command=popup.destroy).pack(side="left")

    def _apply_ai(self, section, text, entries):
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if section in ("intern", "project"):
            idx = 0
            for line in lines:
                if line.startswith("Description 1:") and idx < len(entries):
                    entries[idx]["desc1"] = line.replace("Description 1:", "").strip()
                elif line.startswith("Description 2:") and idx < len(entries):
                    entries[idx]["desc2"] = line.replace("Description 2:", "").strip()
                    idx += 1
            if section == "intern":
                self._refresh_intern_list()
            else:
                self._refresh_proj_list()
        elif section == "skill":
            for i, line in enumerate(lines):
                if i < len(entries) and ":" in line:
                    parts = line.split(":", 1)
                    entries[i]["type"] = parts[0].strip()
                    entries[i]["desc"] = parts[1].strip() if len(parts) > 1 else entries[i]["desc"]
            self._refresh_skill_list()
        elif section == "por":
            idx = 0
            for line in lines:
                if line.startswith("Description 1:") and idx < len(entries):
                    entries[idx]["desc1"] = line.replace("Description 1:", "").strip()
                elif line.startswith("Description 2:") and idx < len(entries):
                    entries[idx]["desc2"] = line.replace("Description 2:", "").strip()
                    idx += 1
            self._refresh_por_list()
        self._rebuild_preview()


# ═══════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeGeneratorApp(root)
    root.mainloop()
