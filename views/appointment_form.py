"""
views/appointment_form.py
─────────────────────────
Appointment booking screen.
Same structure as patient_form.py — 4 sections, scrollable canvas, card layout.
"""

import tkinter as tk
import re
import os
import sys

# ── Shared palette (mirrors app.py & patient_form.py) ───────────────────────


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
SUCCESS_DARK   = "#2AA870"
ERROR          = "#F76F6F"
WARNING        = "#F7B94F"

FONT_TITLE     = ("Georgia",  int(22*Mult), "bold")
FONT_SECTION   = ("Georgia",  int(11*Mult), "bold")
FONT_LABEL     = ("Courier",   int(9*Mult), "bold")
FONT_INPUT     = ("Courier",  int(11*Mult))
FONT_DESC      = ("Courier",   int(8*Mult))
FONT_BTN       = ("Georgia",  int(11*Mult), "bold")
FONT_SMALL     = ("Courier",  int( 8*Mult))


# ════════════════════════════════════════════════════════════════════════════
# Reusable styled widgets  — identical API to patient_form.py
# ════════════════════════════════════════════════════════════════════════════

class StyledEntry(tk.Frame):
    """Label + single-line Entry with focus-border animation."""

    def __init__(self, parent, label: str, placeholder: str = "",
                 required: bool = False, width: int = 28, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._required    = required
        self._placeholder = placeholder

        # Label row
        lbl_row = tk.Frame(self, bg=BG_DARK)
        lbl_row.pack(fill="x")
        tk.Label(lbl_row, text=label.upper(), bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left")
        if required:
            tk.Label(lbl_row, text=" *", bg=BG_DARK,
                     fg=ACCENT, font=FONT_LABEL).pack(side="left")

        # Border frame — NO padx/pady on constructor (causes tkinter TypeError)
        self._border = tk.Frame(self, bg=BORDER)
        self._border.pack(fill="x", pady=(4, 0))

        # 1-px inner padding via nested frame
        _inner = tk.Frame(self._border, bg=BG_INPUT)
        _inner.pack(fill="x", padx=1, pady=1)

        self._entry = tk.Entry(_inner, bg=BG_INPUT, fg=TEXT_DESC,
                               insertbackground=ACCENT,
                               relief="flat", font=FONT_INPUT,
                               width=width, bd=0)
        self._entry.pack(fill="x", padx=10, pady=8)

        if placeholder:
            self._entry.insert(0, placeholder)
        self._entry.bind("<FocusIn>",  self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _):
        self._border.configure(bg=BORDER_FOCUS)
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, "end")
            self._entry.configure(fg=TEXT_PRIMARY)

    def _on_focus_out(self, _):
        self._border.configure(bg=BORDER)
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.configure(fg=TEXT_DESC)

    def get(self) -> str:
        v = self._entry.get()
        return "" if v == self._placeholder else v

    def set(self, value: str):
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._entry.configure(fg=TEXT_PRIMARY)

    def clear(self):
        self._entry.delete(0, "end")
        self._entry.insert(0, self._placeholder)
        self._entry.configure(fg=TEXT_DESC)
        self._border.configure(bg=BORDER)

    def mark_error(self, on: bool = True):
        self._border.configure(bg=ERROR if on else BORDER)


class StyledDropdown(tk.Frame):
    """Label + OptionMenu styled to match the dark theme."""

    def __init__(self, parent, label: str, options: list,
                 required: bool = False, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._required = required
        self._var = tk.StringVar(value=options[0])

        lbl_row = tk.Frame(self, bg=BG_DARK)
        lbl_row.pack(fill="x")
        tk.Label(lbl_row, text=label.upper(), bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left")
        if required:
            tk.Label(lbl_row, text=" *", bg=BG_DARK,
                     fg=ACCENT, font=FONT_LABEL).pack(side="left")

        border = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        border.pack(fill="x", pady=(4, 0))

        menu = tk.OptionMenu(border, self._var, *options)
        menu.configure(bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_INPUT,
                       activebackground=ACCENT_SOFT,
                       activeforeground=TEXT_PRIMARY,
                       relief="flat", bd=0, highlightthickness=0,
                       indicatoron=True, anchor="w")
        menu["menu"].configure(bg=BG_CARD, fg=TEXT_PRIMARY,
                               activebackground=ACCENT,
                               activeforeground=TEXT_PRIMARY,
                               font=FONT_INPUT, bd=0)
        menu.pack(fill="x", padx=6, pady=4)

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        self._var.set(value)

    def clear(self, default: str = ""):
        if default:
            self._var.set(default)


class StyledTextArea(tk.Frame):
    """Label + scrollable Text widget."""

    def __init__(self, parent, label: str, placeholder: str = "",
                 height: int = 4, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._placeholder = placeholder

        tk.Label(self, text=label.upper(), bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w")

        # Border frame — NO padx/pady on constructor
        self._border = tk.Frame(self, bg=BORDER)
        self._border.pack(fill="x", pady=(4, 0))

        _inner = tk.Frame(self._border, bg=BG_INPUT)
        _inner.pack(fill="x", padx=1, pady=1)

        self._text = tk.Text(_inner, bg=BG_INPUT, fg=TEXT_DESC,
                             insertbackground=ACCENT, relief="flat",
                             font=FONT_INPUT, height=height, bd=0,
                             wrap="word")
        self._text.pack(fill="x", padx=10, pady=8)

        if placeholder:
            self._text.insert("1.0", placeholder)

        self._text.bind("<FocusIn>",  lambda _: self._on_focus_in())
        self._text.bind("<FocusOut>", lambda _: self._border.configure(bg=BORDER))

    def _on_focus_in(self):
        self._border.configure(bg=BORDER_FOCUS)
        if self._text.get("1.0", "end-1c") == self._placeholder:
            self._text.delete("1.0", "end")
            self._text.configure(fg=TEXT_PRIMARY)

    def get(self) -> str:
        v = self._text.get("1.0", "end-1c")
        return "" if v == self._placeholder else v

    def clear(self):
        self._text.delete("1.0", "end")
        self._text.insert("1.0", self._placeholder)
        self._text.configure(fg=TEXT_DESC)
        self._border.configure(bg=BORDER)


# ════════════════════════════════════════════════════════════════════════════
# Patient ID searchable picker
# ════════════════════════════════════════════════════════════════════════════

class PatientPicker(tk.Frame):
    """
    Label + search Entry + dropdown listbox.
    Shows all registered patients from the DB.
    Filters live as the user types (by ID or name).
    Selecting a row fills the field and closes the dropdown.
    """

    def __init__(self, parent, label: str, required: bool = False,
                 on_select=None, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._required    = required
        self._all_patients: list[dict] = []   # [{id, label, doctor}, ...]
        self._selected_id = tk.StringVar()
        self._dropdown_open = False
        self._on_select = on_select   # callback(patient_dict) when a row is picked

        # ── Label row ──
        lbl_row = tk.Frame(self, bg=BG_DARK)
        lbl_row.pack(fill="x")
        tk.Label(lbl_row, text=label.upper(), bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left")
        if required:
            tk.Label(lbl_row, text=" *", bg=BG_DARK,
                     fg=ACCENT, font=FONT_LABEL).pack(side="left")

        # ── Search border + entry ──
        self._border = tk.Frame(self, bg=BORDER)
        self._border.pack(fill="x", pady=(4, 0))
        _inner = tk.Frame(self._border, bg=BG_INPUT)
        _inner.pack(fill="x", padx=1, pady=1)

        entry_row = tk.Frame(_inner, bg=BG_INPUT)
        entry_row.pack(fill="x")

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_type())

        self._entry = tk.Entry(entry_row, textvariable=self._search_var,
                               bg=BG_INPUT, fg=TEXT_PRIMARY,
                               insertbackground=ACCENT,
                               relief="flat", font=FONT_INPUT, bd=0)
        self._entry.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        # Reload button
        reload_lbl = tk.Label(entry_row, text="↻", bg=BG_INPUT,
                              fg=TEXT_SECONDARY,
                              font=("Courier", int(11*Mult)),
                              cursor="hand2")
        reload_lbl.pack(side="right", padx=(0, 8))
        reload_lbl.bind("<Button-1>", lambda _: self._load_patients())
        reload_lbl.bind("<Enter>",    lambda _: reload_lbl.configure(fg=ACCENT))
        reload_lbl.bind("<Leave>",    lambda _: reload_lbl.configure(fg=TEXT_SECONDARY))

        self._entry.bind("<FocusIn>",  self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Down>",     lambda _: self._focus_list())
        self._entry.bind("<Return>",   lambda _: self._focus_list())

        # ── Dropdown frame (hidden by default) ──
        self._drop_frame = tk.Frame(self, bg=BORDER)
        # Not packed yet — shown on demand

        _drop_inner = tk.Frame(self._drop_frame, bg=BG_CARD)
        _drop_inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._listbox = tk.Listbox(
            _drop_inner,
            bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=ACCENT_SOFT,
            selectforeground=TEXT_PRIMARY,
            font=FONT_INPUT,
            relief="flat", bd=0,
            height=6,
            activestyle="none",
        )
        self._listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self._listbox.bind("<Double-Button-1>", lambda _: self._pick())
        self._listbox.bind("<Return>",          lambda _: self._pick())
        self._listbox.bind("<Escape>",          lambda _: self._close_dropdown())

        # ── Selected ID badge (shown after selection) ──
        self._badge_frame = tk.Frame(self, bg=BG_DARK)
        self._badge_lbl   = tk.Label(self._badge_frame,
                                     text="", bg=ACCENT_SOFT,
                                     fg=ACCENT, font=FONT_SMALL,
                                     padx=8, pady=2)
        self._badge_lbl.pack(side="left", pady=(4, 0))

        # Load on creation
        self._load_patients()

    # ── DB load ──────────────────────────────────────────────────────────────

    def _load_patients(self):
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from database import get_connection   # type: ignore
            conn = get_connection()
            rows = conn.execute(
                "SELECT Patient_id, First_Name, Last_Name, Doctor FROM Patient ORDER BY Last_Name"
            ).fetchall()
            conn.close()
            self._all_patients = [
                {
                    "id":     str(row["Patient_id"]),
                    "label":  f"{row['Patient_id']}  —  {row['First_Name']} {row['Last_Name']}",
                    "doctor": row["Doctor"] or "",
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[PatientPicker] Could not load patients: {e}")
            self._all_patients = []

        self._refresh_list(self._all_patients)

    # ── Filtering ────────────────────────────────────────────────────────────

    def _on_type(self):
        query = self._search_var.get().strip().lower()
        if not query:
            filtered = self._all_patients
        else:
            filtered = [
                p for p in self._all_patients
                if query in p["label"].lower()
            ]
        self._refresh_list(filtered)
        self._open_dropdown()

    def _refresh_list(self, patients: list):
        self._listbox.delete(0, "end")
        for p in patients:
            self._listbox.insert("end", p["label"])
        self._listbox._patients = patients   # store for lookup

    # ── Dropdown open/close ───────────────────────────────────────────────────

    def _on_focus_in(self, _):
        self._border.configure(bg=BORDER_FOCUS)
        if not self._all_patients:
            self._load_patients()
        self._open_dropdown()

    def _on_focus_out(self, _):
        self._border.configure(bg=BORDER)
        # Small delay so click on listbox registers before we close
        self.after(200, self._close_dropdown)

    def _open_dropdown(self):
        if not self._dropdown_open:
            self._drop_frame.pack(fill="x", pady=(2, 0))
            self._dropdown_open = True

    def _close_dropdown(self):
        if self._dropdown_open:
            self._drop_frame.pack_forget()
            self._dropdown_open = False

    def _focus_list(self):
        if self._listbox.size() > 0:
            self._listbox.focus_set()
            self._listbox.selection_set(0)

    # ── Selection ────────────────────────────────────────────────────────────

    def _pick(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx     = sel[0]
        patient = self._listbox._patients[idx]
        self._selected_id.set(patient["id"])
        self._search_var.set(patient["label"])
        self._entry.configure(fg=TEXT_PRIMARY)
        self._badge_lbl.configure(text=f"✓  ID: {patient['id']}")
        self._badge_frame.pack(fill="x")
        self._close_dropdown()
        # Fire callback so the form can auto-fill doctor etc.
        if self._on_select:
            self._on_select(patient)

    # ── Public API (same as StyledEntry) ─────────────────────────────────────

    def get(self) -> str:
        return self._selected_id.get()

    def set(self, value: str):
        self._selected_id.set(value)
        self._search_var.set(value)

    def clear(self):
        self._selected_id.set("")
        self._search_var.set("")
        self._badge_lbl.configure(text="")
        self._badge_frame.pack_forget()
        self._border.configure(bg=BORDER)
        self._close_dropdown()

    def mark_error(self, on: bool = True):
        self._border.configure(bg=ERROR if on else BORDER)


# ════════════════════════════════════════════════════════════════════════════
# Main view
# ════════════════════════════════════════════════════════════════════════════

class AppointmentFormView(tk.Frame):
    """
    Book Appointment screen.
    Identical structure to PatientFormView — 4 sections inside scrollable canvas.

    Usage (inside app.py __init__, after _build_layout()):
        from views.appointment_form import AppointmentFormView
        self.register_frame("appointment_form",
                            AppointmentFormView(self._content, self))
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_ui()

    # ── Scrollable shell (identical to patient_form) ─────────────────────────

    def _build_ui(self):
        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._inner = tk.Frame(canvas, bg=BG_DARK)
        self._inner_id = canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._inner_id, width=e.width))

        # Mouse-wheel scrolling
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        canvas.bind_all("<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>",
            lambda e: canvas.yview_scroll(1, "units"))

        self._build_content(self._inner)

    # ── Content ──────────────────────────────────────────────────────────────

    def _build_content(self, parent):

        # ── Page header ──────────────────────────────────────────────────────
        header = tk.Frame(parent, bg=BG_DARK)
        header.pack(fill="x", padx=48, pady=(36, 0))

        left_bar = tk.Frame(header, bg=ACCENT, width=4)
        left_bar.pack(side="left", fill="y", padx=(0, 16))

        htext = tk.Frame(header, bg=BG_DARK)
        htext.pack(side="left")
        tk.Label(htext, text="Book Appointment", bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(htext,
                 text="Complete all required fields ( * ) to schedule a new appointment.",
                 bg=BG_DARK, fg=TEXT_SECONDARY,
                 font=FONT_DESC).pack(anchor="w", pady=(4, 0))

        # Divider
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=48, pady=(20, 28))

        # ── SECTION 1 — Identification ────────────────────────────────────────
        self._section_header(parent, "01", "Identification",
                             "Select a registered patient")

        card1 = self._card(parent)

        row1 = self._form_row(card1)
        self.f_patient_id = PatientPicker(row1, "Patient ID", required=True,
                                          on_select=self._on_patient_selected)
        self.f_patient_id.pack(side="left", fill="x", expand=True,
                               padx=(0, 16))

        row2 = self._form_row(card1)
        self.f_status = StyledDropdown(row2, "Status",
                                       ["booked", "pending", "arrived",
                                        "fulfilled", "cancelled", "noshow"],
                                       required=True)
        
        self.f_status.pack(side="left", padx=(0, 16))

        self.f_priority = StyledDropdown(row2, "Priority",
                                         ["routine", "urgent", "asap", "stat"])
        self.f_priority.pack(side="left")

        # ── SECTION 2 — Clinical Assignment ──────────────────────────────────
        self._section_header(parent, "02", "Clinical Assignment",
                             "Doctor and department for this visit")

        card2 = self._card(parent)

        row3 = self._form_row(card2)
        self.f_doctor = StyledEntry(row3, "Doctor Name",
                                    placeholder="Dr. Bernard",
                                    required=True, width=26)
        self.f_doctor.pack(side="left", padx=(0, 16))

        self.f_department = StyledDropdown(row3, "Department",
                                           ["— Select Department —",
                                            "General Practice",
                                            "Cardiology", "Neurology",
                                            "Orthopaedics", "Paediatrics",
                                            "Dermatology", "Gynaecology",
                                            "Oncology", "Radiology",
                                            "Emergency", "Psychiatry",
                                            "Ophthalmology", "ENT",
                                            "Urology", "Other"],
                                           required=True)
        self.f_department.pack(side="left", fill="x", expand=True)

        row4 = self._form_row(card2)
        self.f_appt_type = StyledDropdown(row4, "Appointment Type",
                                          ["— Select Type —",
                                           "Consultation", "Follow-up",
                                           "Emergency", "Procedure",
                                           "Lab Test", "Imaging / Scan",
                                           "Vaccination", "Therapy Session",
                                           "Other"])
        self.f_appt_type.pack(side="left", padx=(0, 16))

        self.f_duration = StyledDropdown(row4, "Est. Duration",
                                         ["15 min", "30 min", "45 min",
                                          "60 min", "90 min", "120 min"])
        self.f_duration.pack(side="left")
        # Auto-recalculate end time whenever duration changes
        self.f_duration._var.trace_add("write", lambda *_: self._calc_end_time())

        # ── SECTION 3 — Date & Time ───────────────────────────────────────────
        self._section_header(parent, "03", "Date & Time",
                             "When the appointment will take place")

        card3 = self._card(parent)

        row5 = self._form_row(card3)
        self.f_date = StyledEntry(row5, "Appointment Date",
                                  placeholder="DD/MM/YYYY",
                                  required=True, width=18)
        self.f_date.pack(side="left", padx=(0, 16))
        # Recalculate end time when date changes (not strictly needed but keeps sync)
        self.f_date._entry.bind("<FocusOut>", lambda _: self._calc_end_time())

        self.f_time = StyledEntry(row5, "Start Time",
                                  placeholder="HH:MM  (e.g. 09:30)",
                                  required=True, width=22)
        self.f_time.pack(side="left", padx=(0, 16))
        self.f_time._entry.bind("<FocusOut>", lambda _: self._calc_end_time())

        # End time — read-only, auto-calculated
        end_frame = tk.Frame(row5, bg=BG_DARK)
        end_frame.pack(side="left")
        tk.Label(end_frame, text="END TIME (AUTO)", bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(anchor="w")
        end_border = tk.Frame(end_frame, bg=BORDER)
        end_border.pack(fill="x", pady=(4, 0))
        end_inner = tk.Frame(end_border, bg=BG_INPUT)
        end_inner.pack(fill="x", padx=1, pady=1)
        self._end_time_var = tk.StringVar(value="—")
        tk.Label(end_inner, textvariable=self._end_time_var,
                 bg=BG_INPUT, fg=ACCENT,
                 font=FONT_INPUT, width=16, anchor="w").pack(
                 padx=10, pady=8, anchor="w")

        # ── SECTION 4 — Visit Details ─────────────────────────────────────────
        self._section_header(parent, "04", "Visit Details",
                             "Reason for visit and additional notes")

        card4 = self._card(parent)

        row6 = self._form_row(card4)
        self.f_reason = StyledTextArea(row6, "Reason for Visit *",
                                       placeholder="Describe the main reason for this appointment…",
                                       height=3)
        self.f_reason.pack(fill="x", expand=True, padx=(0, 16))

        self.f_notes = StyledTextArea(row6, "Additional Notes",
                                      placeholder="Pre-appointment instructions, special requirements…",
                                      height=3)
        self.f_notes.pack(fill="x", expand=True)

        # ── Action bar ────────────────────────────────────────────────────────
        self._build_action_bar(parent)

        # ── Status banner (hidden by default) ─────────────────────────────────
        self._status_frame = tk.Frame(parent, bg=BG_DARK)
        self._status_frame.pack(fill="x", padx=48, pady=(0, 8))
        self._status_lbl = tk.Label(self._status_frame, text="",
                                    bg=BG_DARK, fg=SUCCESS,
                                    font=FONT_SMALL)
        self._status_lbl.pack(anchor="w")

        # Bottom padding
        tk.Frame(parent, bg=BG_DARK, height=40).pack()

    # ── Helpers (identical pattern to patient_form) ──────────────────────────

    def _section_header(self, parent, number: str, title: str, subtitle: str):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="x", padx=48, pady=(24, 8))

        tk.Label(frame, text=number, bg=BG_DARK,
                 fg=ACCENT_SOFT, font=("Courier", 9, "bold")).pack(
                 side="left", padx=(0, 10))
        tk.Label(frame, text=title, bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_SECTION).pack(side="left")
        tk.Label(frame, text=f"  ·  {subtitle}", bg=BG_DARK,
                 fg=TEXT_DESC, font=FONT_DESC).pack(side="left", pady=2)

    def _card(self, parent) -> tk.Frame:
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", padx=48, pady=(0, 4))
        return card

    def _form_row(self, card) -> tk.Frame:
        row = tk.Frame(card, bg=BG_CARD)
        row.pack(fill="x", padx=24, pady=14)
        return row

    def _build_action_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_DARK)
        bar.pack(fill="x", padx=48, pady=(28, 8))

        # Clear button
        clear_btn = tk.Label(bar, text="Clear Form", bg=BG_DARK,
                             fg=TEXT_SECONDARY, font=FONT_BTN,
                             cursor="hand2", padx=0, pady=8)
        clear_btn.pack(side="left")
        clear_btn.bind("<Button-1>", lambda _: self._clear_form())
        clear_btn.bind("<Enter>",
                       lambda _: clear_btn.configure(fg=TEXT_PRIMARY))
        clear_btn.bind("<Leave>",
                       lambda _: clear_btn.configure(fg=TEXT_SECONDARY))

        # Book button
        book_btn = tk.Frame(bar, bg=ACCENT, cursor="hand2")
        book_btn.pack(side="right")

        book_inner = tk.Label(book_btn, text="  Book Appointment  →  ",
                              bg=ACCENT, fg="#FFFFFF",
                              font=FONT_BTN, pady=10, padx=4)
        book_inner.pack()

        for w in (book_btn, book_inner):
            w.bind("<Button-1>",  lambda _: self._submit())
            w.bind("<Enter>",     lambda _: book_btn.configure(bg=ACCENT_DARK))
            w.bind("<Leave>",     lambda _: book_btn.configure(bg=ACCENT))

        # Divider above
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=48, pady=(0, 28))

    # ── Auto-fill helpers ─────────────────────────────────────────────────────

    def _on_patient_selected(self, patient: dict):
        """Called by PatientPicker when a patient is chosen — pre-fills doctor."""
        doctor = patient.get("doctor", "")
        if doctor:
            self.f_doctor.set(doctor)

    def _calc_end_time(self):
        """Auto-calculate end time from start time + duration."""
        start = self.f_time.get().strip()
        dur   = self.f_duration.get()   # e.g. "30 min"
        if not start or not dur:
            return
        try:
            h, m   = map(int, start.split(":"))
            mins   = int(dur.split()[0])
            total  = h * 60 + m + mins
            end_h  = (total // 60) % 24
            end_m  = total % 60
            self._end_time_var.set(f"{end_h:02d}:{end_m:02d}")
        except Exception:
            self._end_time_var.set("—")

    # ── Logic ────────────────────────────────────────────────────────────────

    def _collect(self) -> dict:
        return {
            "patient_id": self.f_patient_id.get(),
            "status":     self.f_status.get(),
            "priority":   self.f_priority.get(),
            "doctor":     self.f_doctor.get().strip(),
            "department": self.f_department.get(),
            "appt_type":  self.f_appt_type.get(),
            "duration":   self.f_duration.get(),
            "date":       self.f_date.get().strip(),
            "time":       self.f_time.get().strip(),
            "time_end":   self._end_time_var.get() if self._end_time_var.get() != "—" else "",
            "reason":     self.f_reason.get().strip(),
            "notes":      self.f_notes.get().strip(),
        }

    def _validate(self, data: dict) -> list[str]:
        errors = []

        if not data["patient_id"]:
            errors.append("Please select a patient.")
            self.f_patient_id.mark_error(True)
        else:
            self.f_patient_id.mark_error(False)

        if not data["doctor"]:
            errors.append("Doctor name is required.")
            self.f_doctor.mark_error(True)
        else:
            self.f_doctor.mark_error(False)

        if data["department"] == "— Select Department —":
            errors.append("Please select a department.")

        date = data["date"]
        if not date:
            errors.append("Appointment date is required.")
            self.f_date.mark_error(True)
        elif not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date):
            errors.append("Date must be in DD/MM/YYYY format.")
            self.f_date.mark_error(True)
        else:
            self.f_date.mark_error(False)

        time = data["time"]
        if not time:
            errors.append("Start time is required.")
            self.f_time.mark_error(True)
        elif not re.fullmatch(r"\d{2}:\d{2}", time):
            errors.append("Start time must be in HH:MM format.")
            self.f_time.mark_error(True)
        else:
            self.f_time.mark_error(False)

        if not data["reason"]:
            errors.append("Reason for visit is required.")

        return errors

    def _submit(self):
        data   = self._collect()
        errors = self._validate(data)

        if errors:
            self._show_status("\n".join(f"⚠  {e}" for e in errors),
                              color=ERROR)
            return

        # ── Hand off to storage layer ─────────────────────────────────────────
        appt_id = None
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from storage import save_appointment          # type: ignore
            appt_id = save_appointment(data)
        except ImportError:
            print("[appointment_form] Data collected:", data)

        if appt_id:
            self._show_status(
                f"✓  Appointment booked successfully!\n"
                f"   Appointment ID : {appt_id}\n"
                f"   Patient        : {data['patient_id']}\n"
                f"   Date & Time    : {data['date']}  {data['time']} → {data['time_end']}",
                color=SUCCESS)
        else:
            self._show_status(
                f"✓  Appointment booked for patient {data['patient_id']} "
                f"on {data['date']} at {data['time']}.",
                color=SUCCESS)
        self._clear_form()

    def _clear_form(self):
        self.f_patient_id.clear()

        for widget in (self.f_doctor, self.f_date, self.f_time):
            widget.clear()

        for widget in (self.f_reason, self.f_notes):
            widget.clear()

        self._end_time_var.set("—")
        self.f_status.clear("booked")
        self.f_priority.clear("routine")
        self.f_department.clear("— Select Department —")
        self.f_appt_type.clear("— Select Type —")
        self.f_duration.clear("30 min")
        # Keep the success status visible after clearing — don't wipe it here

    def _show_status(self, message: str, color: str = SUCCESS):
        self._status_lbl.configure(text=message, fg=color,
                                   justify="left", anchor="w")
        self._status_frame.update_idletasks()



# ── Quick standalone test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Appointment Form — Test")
    root.geometry("1000x700")
    root.configure(bg=BG_DARK)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    class _FakeController:
        pass

    view = AppointmentFormView(root, _FakeController())
    view.grid(row=0, column=0, sticky="nsew")
    root.mainloop()