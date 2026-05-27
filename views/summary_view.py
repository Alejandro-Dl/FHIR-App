"""
views/summary_view.py
─────────────────────
Summary & lookup screen.

Features:
  • Search by Patient ID, Patient Name, or Appointment ID
  • Scrollable appointments sidebar listing all booked appointments
  • Detail panel showing full Patient + Appointment info on selection
  • Export selected record as a PDF report (via reportlab)

Registration (in app.py __init__, after _build_layout()):
    from views.summary_view import SummaryView
    self.register_frame("summary_view", SummaryView(self._content, self))
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
import datetime

# ── Shared palette (mirrors app.py) ─────────────────────────────────────────
Mult = 1.5

BG_DARK        = "#0F1117"
BG_CARD        = "#181C27"
BG_CARD_HVR    = "#1E2335"
BG_INPUT       = "#12151F"
ACCENT         = "#4F8EF7"
ACCENT_SOFT    = "#1E3A6E"
ACCENT_DARK    = "#3A6DD8"
TEXT_PRIMARY   = "#EEF0F6"
TEXT_SECONDARY = "#7A8099"
TEXT_DESC      = "#4E5568"
BORDER         = "#252A3A"
BORDER_FOCUS   = "#4F8EF7"
SUCCESS        = "#3EC98E"
ERROR          = "#F76F6F"
WARNING        = "#F7B94F"

FONT_TITLE   = ("Georgia",  int(18 * Mult), "bold")
FONT_SECTION = ("Georgia",  int(10 * Mult), "bold")
FONT_LABEL   = ("Courier",  int( 8 * Mult), "bold")
FONT_INPUT   = ("Courier",  int(10 * Mult))
FONT_DESC    = ("Courier",  int( 8 * Mult))
FONT_BTN     = ("Georgia",  int(10 * Mult), "bold")
FONT_SMALL   = ("Courier",  int( 7 * Mult))
FONT_MONO    = ("Courier",  int( 9 * Mult))

# ── Reverse lookup maps (integer → label) ────────────────────────────────────
GENDER_LABEL = {0: "Prefer not to say", 1: "Male", 2: "Female", 3: "Other"}
STATUS_LABEL = {1: "Booked", 2: "Pending", 3: "Cancelled", 4: "Completed"}
PRIORITY_LABEL = {1: "Routine", 2: "Urgent", 3: "Emergency"}
DEPT_LABEL = {
    1: "Cardiology", 2: "Neurology", 3: "Orthopedics",
    4: "Pediatrics", 5: "General Practice", 6: "Dermatology",
    7: "Oncology",   8: "Radiology",
}
APPT_TYPE_LABEL = {
    1: "Consultation", 2: "Follow-up", 3: "Emergency", 4: "Routine Check",
}


# ════════════════════════════════════════════════════════════════════════════
# Database helpers
# ════════════════════════════════════════════════════════════════════════════

def _db():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from database import get_connection
    return get_connection()


def fetch_all_appointments():
    """Return list of dicts: appointment + joined patient name."""
    conn = _db()
    rows = conn.execute("""
        SELECT
            a.Appointment_id, a.Patient_id, a.Status, a.Priority,
            a.Doctor, a.Department, a.Appointment_type, a.Duration,
            a.Date, a.Time, a.Time_end, a.Reason, a.Notes,
            p.First_Name, p.Last_Name
        FROM Appointment a
        LEFT JOIN Patient p ON a.Patient_id = p.Patient_id
        ORDER BY a.Date DESC, a.Time DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_records(query: str):
    """
    Search by Patient ID (exact), Appointment ID (exact), or
    patient name (partial, case-insensitive).
    Returns (patients list, appointments list).
    """
    conn  = _db()
    q     = query.strip()
    like  = f"%{q}%"

    patients = conn.execute("""
        SELECT * FROM Patient
        WHERE CAST(Patient_id AS TEXT) = ?
           OR LOWER(First_Name || ' ' || Last_Name) LIKE LOWER(?)
        ORDER BY Last_Name, First_Name
    """, (q, like)).fetchall()

    appointments = conn.execute("""
        SELECT
            a.*, p.First_Name, p.Last_Name
        FROM Appointment a
        LEFT JOIN Patient p ON a.Patient_id = p.Patient_id
        WHERE CAST(a.Appointment_id AS TEXT) = ?
           OR CAST(a.Patient_id     AS TEXT) = ?
           OR LOWER(p.First_Name || ' ' || p.Last_Name) LIKE LOWER(?)
        ORDER BY a.Date DESC
    """, (q, q, like)).fetchall()

    conn.close()
    return [dict(r) for r in patients], [dict(r) for r in appointments]


def fetch_patient(patient_id) -> dict | None:
    conn = _db()
    row  = conn.execute(
        "SELECT * FROM Patient WHERE Patient_id = ?", (patient_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def fetch_appointment(appt_id) -> dict | None:
    conn = _db()
    row  = conn.execute("""
        SELECT a.*, p.First_Name, p.Last_Name
        FROM Appointment a
        LEFT JOIN Patient p ON a.Patient_id = p.Patient_id
        WHERE a.Appointment_id = ?
    """, (appt_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ════════════════════════════════════════════════════════════════════════════
# PDF export
# ════════════════════════════════════════════════════════════════════════════

def export_pdf(patient: dict, appointment: dict | None, out_path: str):
    """Generate a summary PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table,
            TableStyle, HRFlowable,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        messagebox.showerror(
            "Missing library",
            "reportlab is not installed.\n\nRun:  pip install reportlab",
        )
        return

    doc    = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "MedTitle", parent=styles["Title"],
        fontSize=22, textColor=colors.HexColor("#1a2a4a"),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "MedSub", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#7A8099"),
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "MedSection", parent=styles["Heading2"],
        fontSize=12, textColor=colors.HexColor("#4F8EF7"),
        spaceBefore=16, spaceAfter=6,
        borderPad=4,
    )
    normal = ParagraphStyle(
        "MedNormal", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#1a1a2e"),
    )

    def make_table(data_rows):
        col_w = [5*cm, 10*cm]
        tbl   = Table(data_rows, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
            ("TEXTCOLOR",  (0, 0), (0, -1), colors.HexColor("#1E3A6E")),
            ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1),
             [colors.HexColor("#FFFFFF"), colors.HexColor("#F7F9FF")]),
            ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D8EE")),
            ("LEFTPADDING",  (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]))
        return tbl

    story = []

    # ── Header ──
    story.append(Paragraph("MedDesk", title_style))
    story.append(Paragraph(
        f"Patient Summary Report  ·  Generated {datetime.date.today().strftime('%d %B %Y')}",
        sub_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#4F8EF7")))
    story.append(Spacer(1, 12))

    # ── Patient section ──
    story.append(Paragraph("Patient Information", section_style))
    pt_rows = [
        ["Patient ID",    str(patient.get("Patient_id", ""))],
        ["Full Name",     f"{patient.get('First_Name','')} {patient.get('Last_Name','')}"],
        ["Date of Birth", patient.get("Date_Of_Birth", "")],
        ["Gender",        GENDER_LABEL.get(patient.get("Gender"), "—")],
        ["Blood Type",    patient.get("Blood_Type", "—")],
        ["Phone",         patient.get("Phone", "—")],
        ["Email",         patient.get("Email", "—")],
        ["Address",       f"{patient.get('Address','')} {patient.get('City','')} {patient.get('Postcode','')}".strip()],
        ["GP / Doctor",   patient.get("Doctor", "—")],
        ["Insurance",     patient.get("Insurance", "—")],
        ["Allergies",     patient.get("Allergies", "—") or "None"],
        ["Notes",         patient.get("Notes", "—") or "—"],
    ]
    story.append(make_table(pt_rows))

    # ── Emergency contact ──
    if patient.get("Em_name"):
        story.append(Spacer(1, 8))
        story.append(Paragraph("Emergency Contact", section_style))
        em_rows = [
            ["Name",         patient.get("Em_name", "—")],
            ["Relationship", patient.get("Em_relation", "—")],
            ["Phone",        patient.get("Em_phone", "—")],
        ]
        story.append(make_table(em_rows))

    # ── Appointment section ──
    if appointment:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Appointment Details", section_style))
        ap_rows = [
            ["Appointment ID", str(appointment.get("Appointment_id", ""))],
            ["Status",         STATUS_LABEL.get(appointment.get("Status"), "—")],
            ["Priority",       PRIORITY_LABEL.get(appointment.get("Priority"), "—")],
            ["Doctor",         appointment.get("Doctor", "—")],
            ["Department",     DEPT_LABEL.get(appointment.get("Department"), "—")],
            ["Type",           APPT_TYPE_LABEL.get(appointment.get("Appointment_type"), "—")],
            ["Date",           appointment.get("Date", "—")],
            ["Start Time",     appointment.get("Time", "—")],
            ["End Time",       appointment.get("Time_end", "—")],
            ["Duration",       f"{appointment.get('Duration', '—')} min" if appointment.get("Duration") else "—"],
            ["Reason",         appointment.get("Reason", "—")],
            ["Notes",          appointment.get("Notes", "—") or "—"],
        ]
        story.append(make_table(ap_rows))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#D0D8EE")))
    story.append(Paragraph(
        "This document is confidential and intended solely for the named patient.",
        ParagraphStyle("footer", parent=normal,
                       fontSize=7, textColor=colors.HexColor("#AAAAAA"),
                       spaceBefore=6),
    ))

    doc.build(story)
    messagebox.showinfo("PDF Exported", f"Saved to:\n{out_path}")


# ════════════════════════════════════════════════════════════════════════════
# Main view
# ════════════════════════════════════════════════════════════════════════════

class SummaryView(tk.Frame):
    """
    Summary & lookup screen.

    Layout (horizontal split):
      LEFT  — search bar + scrollable appointments sidebar
      RIGHT — detail panel for the selected record
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller = controller
        self.columnconfigure(0, weight=0)   # sidebar fixed
        self.columnconfigure(1, weight=1)   # detail expands
        self.rowconfigure(0, weight=1)

        self._selected_patient     = None   # dict
        self._selected_appointment = None   # dict

        self._build_sidebar()
        self._build_detail_panel()
        self._load_appointments()

    # ── Left sidebar ──────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=BG_CARD,
                           highlightbackground=BORDER,
                           highlightthickness=1,
                           width=int(320 * Mult))
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(2, weight=1)

        # ── Title ──
        hdr = tk.Frame(sidebar, bg=BG_CARD)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        tk.Label(hdr, text="Records", bg=BG_CARD,
                 fg=TEXT_PRIMARY, font=FONT_SECTION).pack(side="left")

        # Refresh button
        ref_btn = tk.Label(hdr, text="↻", bg=BG_CARD,
                           fg=TEXT_SECONDARY, font=("Courier", int(14*Mult)),
                           cursor="hand2")
        ref_btn.pack(side="right")
        ref_btn.bind("<Button-1>", lambda _: self._load_appointments())
        ref_btn.bind("<Enter>", lambda _: ref_btn.configure(fg=ACCENT))
        ref_btn.bind("<Leave>", lambda _: ref_btn.configure(fg=TEXT_SECONDARY))

        # ── Search bar ──
        search_frame = tk.Frame(sidebar, bg=BORDER)
        search_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        inner = tk.Frame(search_frame, bg=BG_INPUT)
        inner.pack(fill="x", padx=1, pady=1)

        tk.Label(inner, text="⌕", bg=BG_INPUT,
                 fg=TEXT_SECONDARY, font=("Courier", int(12*Mult))).pack(
                 side="left", padx=(10, 4))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())

        self._search_entry = tk.Entry(
            inner, textvariable=self._search_var,
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            insertbackground=ACCENT,
            relief="flat", font=FONT_INPUT, bd=0,
        )
        self._search_entry.pack(fill="x", padx=(0, 10), pady=8, side="left",
                                expand=True)
        self._search_entry.insert(0, "Search by name, patient ID or appt ID…")
        self._search_entry.configure(fg=TEXT_DESC)
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        # ── Scrollable appointments list ──
        list_frame = tk.Frame(sidebar, bg=BG_CARD)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(list_frame, bg=BG_CARD,
                           highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._list_inner = tk.Frame(canvas, bg=BG_CARD)
        self._list_window = canvas.create_window(
            (0, 0), window=self._list_inner, anchor="nw"
        )

        self._list_inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._list_window, width=e.width
        ))

        # Mouse wheel
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._canvas = canvas

    # ── Right detail panel ───────────────────────────────────────────────────

    def _build_detail_panel(self):
        self._detail = tk.Frame(self, bg=BG_DARK)
        self._detail.grid(row=0, column=1, sticky="nsew")
        self._detail.columnconfigure(0, weight=1)
        self._detail.rowconfigure(1, weight=1)

        self._show_empty_state()

    def _show_empty_state(self):
        self._clear_detail()
        placeholder = tk.Frame(self._detail, bg=BG_DARK)
        placeholder.grid(row=0, column=0, sticky="nsew")
        self._detail.rowconfigure(0, weight=1)

        tk.Label(placeholder,
                 text="Select an appointment\nfrom the sidebar",
                 bg=BG_DARK, fg=TEXT_DESC,
                 font=("Georgia", int(13*Mult), "italic"),
                 justify="center").place(relx=0.5, rely=0.5, anchor="center")

        self._placeholder = placeholder

    def _clear_detail(self):
        for w in self._detail.winfo_children():
            w.destroy()

    # ── Load & render appointments list ──────────────────────────────────────

    def _load_appointments(self, appointments=None):
        """Populate the sidebar list. Fetches all if appointments is None."""
        for w in self._list_inner.winfo_children():
            w.destroy()

        if appointments is None:
            try:
                appointments = fetch_all_appointments()
            except Exception as e:
                tk.Label(self._list_inner,
                         text=f"DB error:\n{e}",
                         bg=BG_CARD, fg=ERROR,
                         font=FONT_SMALL, wraplength=280,
                         justify="left").pack(padx=16, pady=16, anchor="w")
                return

        if not appointments:
            tk.Label(self._list_inner,
                     text="No records found.",
                     bg=BG_CARD, fg=TEXT_DESC,
                     font=FONT_SMALL).pack(padx=16, pady=24)
            return

        tk.Label(self._list_inner,
                 text=f"APPOINTMENTS  ({len(appointments)})",
                 bg=BG_CARD, fg=TEXT_DESC,
                 font=("Courier", int(7*Mult), "bold")).pack(
                 anchor="w", padx=16, pady=(12, 4))

        for appt in appointments:
            self._make_appt_card(appt)

    def _make_appt_card(self, appt: dict):
        status_colors = {
            1: SUCCESS, 2: WARNING, 3: ERROR, 4: TEXT_SECONDARY
        }
        status_color = status_colors.get(appt.get("Status"), TEXT_DESC)
        status_text  = STATUS_LABEL.get(appt.get("Status"), "—")

        card = tk.Frame(self._list_inner, bg=BG_CARD,
                        cursor="hand2")
        card.pack(fill="x", padx=8, pady=2)

        # Left accent stripe
        stripe = tk.Frame(card, bg=status_color, width=3)
        stripe.pack(side="left", fill="y")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(side="left", fill="x", expand=True, padx=12, pady=10)

        # Row 1 — name + status badge
        row1 = tk.Frame(body, bg=BG_CARD)
        row1.pack(fill="x")

        name = f"{appt.get('First_Name','')} {appt.get('Last_Name','')}".strip() or "Unknown"
        tk.Label(row1, text=name, bg=BG_CARD,
                 fg=TEXT_PRIMARY, font=("Georgia", int(9*Mult), "bold"),
                 anchor="w").pack(side="left")

        tk.Label(row1, text=status_text, bg=BG_CARD,
                 fg=status_color, font=FONT_SMALL,
                 anchor="e").pack(side="right")

        # Row 2 — date + doctor
        row2 = tk.Frame(body, bg=BG_CARD)
        row2.pack(fill="x", pady=(2, 0))

        date_str = appt.get("Date", "—") or "—"
        time_str = appt.get("Time", "") or ""
        tk.Label(row2, text=f"{date_str}  {time_str}".strip(),
                 bg=BG_CARD, fg=TEXT_SECONDARY,
                 font=FONT_SMALL, anchor="w").pack(side="left")

        doctor = appt.get("Doctor", "—") or "—"
        tk.Label(row2, text=f"Dr. {doctor}" if doctor != "—" else "—",
                 bg=BG_CARD, fg=TEXT_DESC,
                 font=FONT_SMALL, anchor="e").pack(side="right")

        # Row 3 — IDs
        row3 = tk.Frame(body, bg=BG_CARD)
        row3.pack(fill="x", pady=(2, 0))
        tk.Label(row3,
                 text=f"Appt #{appt.get('Appointment_id','—')}  ·  "
                      f"Patient #{appt.get('Patient_id','—')}",
                 bg=BG_CARD, fg=TEXT_DESC,
                 font=("Courier", int(6*Mult))).pack(anchor="w")

        # Divider
        tk.Frame(self._list_inner, bg=BORDER, height=1).pack(
            fill="x", padx=8)

        # Hover + click
        all_w = [card, body, stripe, row1, row2, row3] + \
                list(body.winfo_children()) + \
                list(row1.winfo_children()) + \
                list(row2.winfo_children()) + \
                list(row3.winfo_children())

        def on_enter(_):
            for w in [card, body, row1, row2, row3]:
                w.configure(bg=BG_CARD_HVR)

        def on_leave(_):
            for w in [card, body, row1, row2, row3]:
                w.configure(bg=BG_CARD)

        def on_click(_):
            self._select_appointment(appt)

        for w in [card, body, row1, row2, row3]:
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)
            w.bind("<Button-1>", on_click)

    # ── Search ───────────────────────────────────────────────────────────────

    _PLACEHOLDER = "Search by name, patient ID or appt ID…"

    def _search_focus_in(self, _):
        if self._search_entry.get() == self._PLACEHOLDER:
            self._search_entry.delete(0, "end")
            self._search_entry.configure(fg=TEXT_PRIMARY)

    def _search_focus_out(self, _):
        if not self._search_entry.get():
            self._search_entry.insert(0, self._PLACEHOLDER)
            self._search_entry.configure(fg=TEXT_DESC)

    def _on_search(self):
        query = self._search_var.get().strip()
        if not query or query == self._PLACEHOLDER:
            self._load_appointments()
            return
        try:
            _, appointments = search_records(query)
            self._load_appointments(appointments)
        except Exception as e:
            print(f"[summary_view] Search error: {e}")

    # ── Detail panel ─────────────────────────────────────────────────────────

    def _select_appointment(self, appt: dict):
        """Load full patient + appointment data and render the detail panel."""
        try:
            patient     = fetch_patient(appt.get("Patient_id"))
            appointment = fetch_appointment(appt.get("Appointment_id"))
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        self._selected_patient     = patient
        self._selected_appointment = appointment
        self._render_detail(patient, appointment)

    def _render_detail(self, patient: dict | None, appt: dict | None):
        self._clear_detail()
        self._detail.rowconfigure(0, weight=0)
        self._detail.rowconfigure(1, weight=1)
        self._detail.rowconfigure(2, weight=0)

        # ── Action bar ──
        action_bar = tk.Frame(self._detail, bg=BG_DARK)
        action_bar.grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 0))

        name = ""
        if patient:
            name = f"{patient.get('First_Name','')} {patient.get('Last_Name','')}".strip()

        tk.Label(action_bar, text=name or "Patient Record",
                 bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=FONT_TITLE).pack(side="left")

        # PDF export button
        pdf_btn = tk.Frame(action_bar, bg=ACCENT, cursor="hand2")
        pdf_btn.pack(side="right")
        pdf_inner = tk.Label(pdf_btn, text="  ↓ Export PDF  ",
                             bg=ACCENT, fg="#FFFFFF",
                             font=FONT_BTN, pady=8, padx=4)
        pdf_inner.pack()
        for w in (pdf_btn, pdf_inner):
            w.bind("<Button-1>",  lambda _: self._export_pdf())
            w.bind("<Enter>",     lambda _: pdf_btn.configure(bg=ACCENT_DARK))
            w.bind("<Leave>",     lambda _: pdf_btn.configure(bg=ACCENT))

        # ── Scrollable content ──
        scroll_frame = tk.Frame(self._detail, bg=BG_DARK)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_frame, bg=BG_DARK,
                           highlightthickness=0, bd=0)
        vsb    = tk.Scrollbar(scroll_frame, orient="vertical",
                              command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        scroll_frame.columnconfigure(0, weight=1)

        content = tk.Frame(canvas, bg=BG_DARK)
        win_id  = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        pad = {"padx": 32, "pady": (0, 4)}

        # ── Patient info section ──
        if patient:
            self._section_title(content, "01", "Patient Information")
            fields_pt = [
                ("Patient ID",    str(patient.get("Patient_id", "—"))),
                ("Date of Birth", patient.get("Date_Of_Birth", "—")),
                ("Gender",        GENDER_LABEL.get(patient.get("Gender"), "—")),
                ("Blood Type",    patient.get("Blood_Type", "—")),
                ("Phone",         patient.get("Phone", "—")),
                ("Email",         patient.get("Email", "—")),
                ("Address",       f"{patient.get('Address','')} "
                                  f"{patient.get('City','')} "
                                  f"{patient.get('Postcode','')}".strip() or "—"),
                ("GP / Doctor",   patient.get("Doctor", "—")),
                ("Insurance",     patient.get("Insurance", "—")),
                ("Allergies",     patient.get("Allergies", "") or "None"),
                ("Notes",         patient.get("Notes", "") or "—"),
            ]
            self._info_card(content, fields_pt)

            if patient.get("Em_name"):
                self._section_title(content, "02", "Emergency Contact")
                fields_em = [
                    ("Name",         patient.get("Em_name", "—")),
                    ("Relationship", patient.get("Em_relation", "—")),
                    ("Phone",        patient.get("Em_phone", "—")),
                ]
                self._info_card(content, fields_em)

        # ── Appointment info section ──
        if appt:
            self._section_title(content, "03", "Appointment Details")
            status_str   = STATUS_LABEL.get(appt.get("Status"), "—")
            priority_str = PRIORITY_LABEL.get(appt.get("Priority"), "—")
            dept_str     = DEPT_LABEL.get(appt.get("Department"), "—")
            type_str     = APPT_TYPE_LABEL.get(appt.get("Appointment_type"), "—")
            dur_str      = (f"{appt.get('Duration')} min"
                            if appt.get("Duration") else "—")

            fields_ap = [
                ("Appointment ID", str(appt.get("Appointment_id", "—"))),
                ("Status",         status_str),
                ("Priority",       priority_str),
                ("Doctor",         appt.get("Doctor", "—")),
                ("Department",     dept_str),
                ("Type",           type_str),
                ("Date",           appt.get("Date", "—")),
                ("Start Time",     appt.get("Time", "—")),
                ("End Time",       appt.get("Time_end", "—")),
                ("Duration",       dur_str),
                ("Reason",         appt.get("Reason", "—")),
                ("Notes",          appt.get("Notes", "") or "—"),
            ]
            self._info_card(content, fields_ap)

        # Bottom padding
        tk.Frame(content, bg=BG_DARK, height=40).pack()

    # ── Reusable detail widgets ───────────────────────────────────────────────

    def _section_title(self, parent, number: str, title: str):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="x", padx=32, pady=(20, 6))
        tk.Label(frame, text=number, bg=BG_DARK,
                 fg=ACCENT_SOFT,
                 font=("Courier", int(7*Mult), "bold")).pack(side="left",
                                                              padx=(0, 8))
        tk.Label(frame, text=title, bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_SECTION).pack(side="left")
        tk.Frame(frame, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=(16, 0))

    def _info_card(self, parent, fields: list[tuple]):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", padx=32, pady=(0, 4))
        card.columnconfigure(1, weight=1)

        for i, (label, value) in enumerate(fields):
            bg = BG_CARD if i % 2 == 0 else BG_CARD_HVR

            row = tk.Frame(card, bg=bg)
            row.pack(fill="x")
            row.columnconfigure(1, weight=1)

            tk.Label(row, text=label.upper(),
                     bg=bg, fg=TEXT_SECONDARY,
                     font=FONT_LABEL,
                     width=18, anchor="w").pack(
                     side="left", padx=(16, 8), pady=8)

            tk.Label(row, text=str(value) if value else "—",
                     bg=bg, fg=TEXT_PRIMARY,
                     font=FONT_MONO, anchor="w",
                     wraplength=500, justify="left").pack(
                     side="left", padx=(0, 16), pady=8, fill="x", expand=True)

    # ── PDF export ────────────────────────────────────────────────────────────

    def _export_pdf(self):
        if not self._selected_patient:
            messagebox.showwarning("No record selected",
                                   "Please select an appointment first.")
            return

        pt   = self._selected_patient
        name = f"{pt.get('First_Name','')}_{pt.get('Last_Name','')}".strip("_")
        appt = self._selected_appointment
        appt_id = appt.get("Appointment_id", "0") if appt else "0"

        out_dir  = os.path.join(os.path.dirname(__file__), "..", "data", "reports")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"summary_{name}_{appt_id}.pdf"
        out_path = os.path.abspath(os.path.join(out_dir, filename))

        export_pdf(pt, appt, out_path)

    # ── Public: called by app.py when this tab becomes visible ───────────────

    def on_show(self):
        """Refresh the list every time the view is navigated to."""
        self._load_appointments()


# ── Quick standalone test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Summary View — Test")
    root.geometry("1200x750")
    root.configure(bg=BG_DARK)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    class _FakeController:
        pass

    view = SummaryView(root, _FakeController())
    view.grid(row=0, column=0, sticky="nsew")
    root.mainloop()