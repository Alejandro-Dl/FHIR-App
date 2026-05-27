"""
views/patient_form.py
─────────────────────
Patient registration screen.
Registers itself into App via  app.register_frame("patient_form", PatientFormView(app, app))
"""

import tkinter as tk
from tkinter import messagebox
import re
import os
import sys

# ── shared palette (mirrors app.py) ─────────────────────────────────────────

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
# Reusable styled widgets
# ════════════════════════════════════════════════════════════════════════════

class StyledEntry(tk.Frame):
    """Label + single-line Entry with focus-border animation."""

    def __init__(self, parent, label: str, placeholder: str = "",
                 required: bool = False, width: int = 28, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._required    = required
        self._placeholder = placeholder
        self._has_focus   = False

        # Label row
        lbl_row = tk.Frame(self, bg=BG_DARK)
        lbl_row.pack(fill="x")
        tk.Label(lbl_row, text=label.upper(), bg=BG_DARK,
                 fg=TEXT_SECONDARY, font=FONT_LABEL).pack(side="left")
        if required:
            tk.Label(lbl_row, text=" *", bg=BG_DARK,
                     fg=ACCENT, font=FONT_LABEL).pack(side="left")

        # Border canvas wrapping the Entry
        self._border = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        self._border.pack(fill="x", pady=(4, 0))

        self._entry = tk.Entry(self._border, bg=BG_INPUT, fg=TEXT_DESC,
                               insertbackground=ACCENT,
                               relief="flat", font=FONT_INPUT,
                               width=width, bd=0)
        self._entry.pack(fill="x", padx=10, pady=8)

        # Placeholder
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

        border = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        border.pack(fill="x", pady=(4, 0))

        self._text = tk.Text(border, bg=BG_INPUT, fg=TEXT_DESC,
                             insertbackground=ACCENT, relief="flat",
                             font=FONT_INPUT, height=height, bd=0,
                             wrap="word")
        self._text.pack(fill="x", padx=10, pady=8)

        if placeholder:
            self._text.insert("1.0", placeholder)

        self._text.bind("<FocusIn>",  lambda _: self._on_focus_in(border))
        self._text.bind("<FocusOut>", lambda _: border.configure(bg=BORDER))

    def _on_focus_in(self, border):
        border.configure(bg=BORDER_FOCUS)
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


# ════════════════════════════════════════════════════════════════════════════
# Main view
# ════════════════════════════════════════════════════════════════════════════

class PatientFormView(tk.Frame):
    """
    Register Patient screen.

    Usage (inside main.py):
        from views.patient_form import PatientFormView
        pf = PatientFormView(app, controller=app)
        app.register_frame("patient_form", pf)
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_DARK)
        self.controller  = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer scroll container
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

    def _build_content(self, parent):
        pad = dict(padx=48, pady=0)

        # ── Page header ──────────────────────────────────────────────────────
        header = tk.Frame(parent, bg=BG_DARK)
        header.pack(fill="x", padx=48, pady=(36, 0))

        left_bar = tk.Frame(header, bg=ACCENT, width=4)
        left_bar.pack(side="left", fill="y", padx=(0, 16))

        htext = tk.Frame(header, bg=BG_DARK)
        htext.pack(side="left")
        tk.Label(htext, text="Register Patient", bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_TITLE).pack(anchor="w")
        tk.Label(htext, text="Complete all required fields ( * ) to create a new patient record.",
                 bg=BG_DARK, fg=TEXT_SECONDARY,
                 font=FONT_DESC).pack(anchor="w", pady=(4, 0))

        # Divider
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=48, pady=(20, 28))

        # ── SECTION 1 — Personal Information ─────────────────────────────────
        self._section_header(parent, "01", "Personal Information",
                             "Basic identification details")

        card1 = self._card(parent)

        row1 = self._form_row(card1)
        self.f_first_name = StyledEntry(row1, "First Name",
                                        placeholder="e.g. Marie",
                                        required=True, width=22)
        self.f_first_name.pack(side="left", fill="x", expand=True,
                               padx=(0, 16))

        self.f_last_name = StyledEntry(row1, "Last Name",
                                       placeholder="e.g. Dupont",
                                       required=True, width=22)
        self.f_last_name.pack(side="left", fill="x", expand=True)

        row2 = self._form_row(card1)
        self.f_dob = StyledEntry(row2, "Date of Birth",
                                 placeholder="DD/MM/YYYY",
                                 required=True, width=16)
        self.f_dob.pack(side="left", padx=(0, 16))

        self.f_gender = StyledDropdown(row2, "Gender",
                                       ["— Select —", "Female", "Male",
                                        "Non-binary", "Prefer not to say"],
                                       required=True)
        self.f_gender.pack(side="left", padx=(0, 16))

        self.f_blood = StyledDropdown(row2, "Blood Type",
                                      ["Unknown", "A+", "A−", "B+", "B−",
                                       "AB+", "AB−", "O+", "O−"])
        self.f_blood.pack(side="left")

        # ── SECTION 2 — Contact Details ───────────────────────────────────────
        self._section_header(parent, "02", "Contact Details",
                             "How to reach the patient")

        card2 = self._card(parent)

        row3 = self._form_row(card2)
        self.f_phone = StyledEntry(row3, "Phone Number",
                                   placeholder="+32 478 000 000",
                                   required=True, width=22)
        self.f_phone.pack(side="left", padx=(0, 16))

        self.f_email = StyledEntry(row3, "Email Address",
                                   placeholder="patient@example.com",
                                   width=30)
        self.f_email.pack(side="left", fill="x", expand=True)

        row4 = self._form_row(card2)
        self.f_address = StyledEntry(row4, "Street Address",
                                     placeholder="Rue de la Loi 16",
                                     width=34)
        self.f_address.pack(side="left", padx=(0, 16), fill="x", expand=True)

        self.f_city = StyledEntry(row4, "City",
                                  placeholder="Brussels",
                                  width=18)
        self.f_city.pack(side="left", padx=(0, 16))

        self.f_postcode = StyledEntry(row4, "Postcode",
                                      placeholder="1000",
                                      width=8)
        self.f_postcode.pack(side="left")

        # ── SECTION 3 — Medical Information ──────────────────────────────────
        self._section_header(parent, "03", "Medical Information",
                             "Clinical background and history")

        card3 = self._card(parent)

        row5 = self._form_row(card3)
        self.f_doctor = StyledEntry(row5, "Assigned Doctor",
                                    placeholder="Dr. Bernard",
                                    width=24)
        self.f_doctor.pack(side="left", padx=(0, 16))

        self.f_insurance = StyledEntry(row5, "Insurance Number",
                                       placeholder="MUT-XXXX-XXXX",
                                       width=22)
        self.f_insurance.pack(side="left")

        row6 = self._form_row(card3)
        self.f_allergies = StyledTextArea(row6, "Known Allergies",
                                          placeholder="Penicillin, latex…",
                                          height=3)
        self.f_allergies.pack(fill="x", expand=True, padx=(0, 16))

        self.f_notes = StyledTextArea(row6, "Clinical Notes",
                                      placeholder="Current conditions, chronic illnesses, medications…",
                                      height=3)
        self.f_notes.pack(fill="x", expand=True)

        # ── SECTION 4 — Emergency Contact ─────────────────────────────────────
        self._section_header(parent, "04", "Emergency Contact",
                             "Person to notify in case of emergency")

        card4 = self._card(parent)

        row7 = self._form_row(card4)
        self.f_em_name = StyledEntry(row7, "Full Name",
                                     placeholder="Jean Dupont",
                                     width=26)
        self.f_em_name.pack(side="left", padx=(0, 16))

        self.f_em_relation = StyledDropdown(row7, "Relationship",
                                            ["— Select —", "Spouse / Partner",
                                             "Parent", "Child", "Sibling",
                                             "Friend", "Guardian", "Other"])
        self.f_em_relation.pack(side="left", padx=(0, 16))

        self.f_em_phone = StyledEntry(row7, "Phone Number",
                                      placeholder="+32 478 000 000",
                                      width=20)
        self.f_em_phone.pack(side="left")

        # ── Action bar ────────────────────────────────────────────────────────
        self._build_action_bar(parent)

        # ── Status banner (hidden by default) ─────────────────────────────────
        self._status_frame = tk.Frame(parent, bg=BG_DARK)
        self._status_frame.pack(fill="x", padx=48, pady=(0, 8))
        self._status_lbl = tk.Label(self._status_frame, text="",
                                    bg=BG_DARK, fg=SUCCESS,
                                    font=FONT_SMALL)
        self._status_lbl.pack(anchor="w")

        # bottom padding
        tk.Frame(parent, bg=BG_DARK, height=40).pack()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _section_header(self, parent, number: str,
                        title: str, subtitle: str):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="x", padx=48, pady=(24, 8))

        tk.Label(frame, text=number, bg=BG_DARK,
                 fg=ACCENT_SOFT, font=("Courier", 9, "bold")).pack(side="left",
                                                                     padx=(0, 10))
        tk.Label(frame, text=title, bg=BG_DARK,
                 fg=TEXT_PRIMARY, font=FONT_SECTION).pack(side="left")
        tk.Label(frame, text=f"  ·  {subtitle}", bg=BG_DARK,
                 fg=TEXT_DESC, font=FONT_DESC).pack(side="left",
                                                      padx=(0, 0), pady=2)

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

        # Save button
        save_btn = tk.Frame(bar, bg=ACCENT, cursor="hand2")
        save_btn.pack(side="right")

        save_inner = tk.Label(save_btn, text="  Register Patient  →  ",
                              bg=ACCENT, fg="#FFFFFF",
                              font=FONT_BTN, pady=10, padx=4)
        save_inner.pack()

        for w in (save_btn, save_inner):
            w.bind("<Button-1>",  lambda _: self._submit())
            w.bind("<Enter>",     lambda _: save_btn.configure(bg=ACCENT_DARK))
            w.bind("<Leave>",     lambda _: save_btn.configure(bg=ACCENT))

        # Divider above
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=48, pady=(0, 28))

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _collect(self) -> dict:
        return {
            "first_name":  self.f_first_name.get().strip(),
            "last_name":   self.f_last_name.get().strip(),
            "dob":         self.f_dob.get().strip(),
            "gender":      self.f_gender.get(),
            "blood_type":  self.f_blood.get(),
            "phone":       self.f_phone.get().strip(),
            "email":       self.f_email.get().strip(),
            "address":     self.f_address.get().strip(),
            "city":        self.f_city.get().strip(),
            "postcode":    self.f_postcode.get().strip(),
            "doctor":      self.f_doctor.get().strip(),
            "insurance":   self.f_insurance.get().strip(),
            "allergies":   self.f_allergies.get().strip(),
            "notes":       self.f_notes.get().strip(),
            "em_name":     self.f_em_name.get().strip(),
            "em_relation": self.f_em_relation.get(),
            "em_phone":    self.f_em_phone.get().strip(),
        }

    def _validate(self, data: dict) -> list[str]:
        errors = []

        if not data["first_name"]:
            errors.append("First name is required.")
            self.f_first_name.mark_error(True)
        else:
            self.f_first_name.mark_error(False)

        if not data["last_name"]:
            errors.append("Last name is required.")
            self.f_last_name.mark_error(True)
        else:
            self.f_last_name.mark_error(False)

        # Date format DD/MM/YYYY
        dob = data["dob"]
        if not dob:
            errors.append("Date of birth is required.")
            self.f_dob.mark_error(True)
        elif not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dob):
            errors.append("Date of birth must be DD/MM/YYYY.")
            self.f_dob.mark_error(True)
        else:
            self.f_dob.mark_error(False)

        if data["gender"] == "— Select —":
            errors.append("Please select a gender.")

        if not data["phone"]:
            errors.append("Phone number is required.")
            self.f_phone.mark_error(True)
        else:
            self.f_phone.mark_error(False)

        # Optional e-mail format check
        email = data["email"]
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            errors.append("E-mail address format is invalid.")
            self.f_email.mark_error(True)
        else:
            self.f_email.mark_error(False)

        return errors

    def _submit(self):
        data   = self._collect()
        errors = self._validate(data)

        if errors:
            self._show_status("\n".join(f"⚠  {e}" for e in errors),
                              color=ERROR)
            return

        # ── Hand off to storage layer ────────────────────────────────────────
        try:
            # Lazy import so the form works even if storage.py isn't ready yet
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from storage import save_patient          # type: ignore
            save_patient(data)
        except ImportError:
            # storage.py not yet implemented — just print for now
            print("[patient_form] Data collected:", data)

        self._show_status(
            f"✓  Patient  {data['first_name']} {data['last_name']}  registered successfully.",
            color=SUCCESS)
        self._clear_form()

    def _clear_form(self):
        for widget in (
            self.f_first_name, self.f_last_name, self.f_dob,
            self.f_phone, self.f_email, self.f_address,
            self.f_city, self.f_postcode, self.f_doctor,
            self.f_insurance, self.f_em_name, self.f_em_phone,
        ):
            widget.clear()

        for widget in (self.f_allergies, self.f_notes):
            widget.clear()

        self.f_gender.set("— Select —")
        self.f_blood.set("Unknown")
        self.f_em_relation.set("— Select —")
        self._show_status("")

    def _show_status(self, message: str, color: str = SUCCESS):
        self._status_lbl.configure(text=message, fg=color)
        self._status_frame.update_idletasks()


# ── Quick standalone test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Patient Form — Test")
    root.geometry("1000x700")
    root.configure(bg=BG_DARK)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    class _FakeController:
        pass

    view = PatientFormView(root, _FakeController())
    view.grid(row=0, column=0, sticky="nsew")
    root.mainloop()