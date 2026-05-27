import tkinter as tk
from tkinter import ttk, font
import sys
import os

# ── View imports ─────────────────────────────────────────────────────────────
from views.patient_form     import PatientFormView
from views.appointment_form import AppointmentFormView
from views.summary_view import SummaryView


# ── Colour palette ──────────────────────────────────────────────────────────
BG_DARK      = "#0F1117"   # near-black canvas
BG_CARD      = "#181C27"   # card surface
BG_CARD_HVR  = "#1E2335"   # card hover
ACCENT       = "#4F8EF7"   # electric-blue accent
ACCENT_SOFT  = "#1E3A6E"   # muted accent fill
TEXT_PRIMARY = "#EEF0F6"
TEXT_SECONDARY = "#7A8099"
TEXT_DESC    = "#4E5568"
BORDER       = "#252A3A"
BORDER_HVR   = "#4F8EF7"
SUCCESS      = "#3EC98E"

# ── Frame labels (must match keys used in show_frame) ───────────────────────
FRAMES = ["patient_form", "appointment_form", "summary_view"]
mult = 1.5

class App(tk.Tk):
    """Main application window with animated side-menu navigation."""

    def __init__(self):
        super().__init__()
        self.title("MedDesk — Patient Management")
        self.geometry("1080x680")
        self.minsize(860, 760)
        self.configure(bg=BG_DARK)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1080) // 2
        y = (self.winfo_screenheight() - 680)  // 2
        self.geometry(f"+{x}+{y}")

        self._frames: dict[str, tk.Frame] = {}
        self._active_key = tk.StringVar(value="patient_form")

        self._build_layout()

        # ── Register real views (Option 2 — wired directly in app.py) ────────
        self.register_frame("patient_form",
                            PatientFormView(self._content, self))
        self.register_frame("appointment_form",
                            AppointmentFormView(self._content, self))
        self.register_frame("summary_view", SummaryView(self._content, self))

        self.show_frame("patient_form")
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Root uses a two-column grid: sidebar | content
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=BG_CARD, width=260)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        # ── Logo / App name ──
        logo_frame = tk.Frame(sidebar, bg=BG_CARD)
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(32, 8), padx=24)

        dot = tk.Canvas(logo_frame, width=10, height=10,
                        bg=BG_CARD, highlightthickness=0)
        dot.pack(side="left", padx=(0, 8), pady=2)
        dot.create_oval(0, 0, 10, 10, fill=ACCENT, outline="")

        tk.Label(logo_frame, text="MedDesk", bg=BG_CARD,
                 fg=TEXT_PRIMARY, font=("Georgia", int(18*mult), "bold")).pack(side="left")

        tk.Label(sidebar, text="v1.0  ·  Patient System",
                 bg=BG_CARD, fg=TEXT_DESC, font=("Courier", int(9*mult))).grid(
                 row=1, column=0, sticky="w", padx=28, pady=(0, 28))

        # Divider
        tk.Frame(sidebar, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", padx=20, pady=(0, 24))

        # ── Nav label ──
        tk.Label(sidebar, text="NAVIGATION", bg=BG_CARD,
                 fg=TEXT_DESC, font=("Courier", int(8*mult), "bold")).grid(
                 row=3, column=0, sticky="w", padx=28, pady=(0, 8))

        # ── Nav items ──
        nav_items = [
            {
                "key":   "patient_form",
                "icon":  "⊕",
                "label": "Register Patient",
                "desc":  "Add a new patient record to the system",
            },
            {
                "key":   "appointment_form",
                "icon":  "◷",
                "label": "Book Appointment",
                "desc":  "Schedule a visit for an existing patient",
            },
            {
                "key":   "summary_view",
                "icon":  "≡",
                "label": "View Summary",
                "desc":  "Browse all patients and appointments",
            },
        ]

        self._nav_buttons = {}
        for row_idx, item in enumerate(nav_items, start=4):
            btn = self._make_nav_button(sidebar, item)
            btn.grid(row=row_idx, column=0, sticky="ew",
                     padx=12, pady=4)
            self._nav_buttons[item["key"]] = btn

        # Spacer pushes footer down
        sidebar.rowconfigure(10, weight=1)

        # ── Footer ──
        footer = tk.Frame(sidebar, bg=BG_CARD)
        footer.grid(row=11, column=0, sticky="ew", padx=20, pady=24)

        status_dot = tk.Canvas(footer, width=8, height=8,
                               bg=BG_CARD, highlightthickness=0)
        status_dot.pack(side="left", padx=(0, 6))
        status_dot.create_oval(0, 0, 8, 8, fill=SUCCESS, outline="")

        tk.Label(footer, text="System online",
                 bg=BG_CARD, fg=TEXT_DESC, font=("Courier", int(9*mult))).pack(side="left")

    def _make_nav_button(self, parent, item: dict) -> tk.Frame:
        """Build a styled navigation card button."""
        frame = tk.Frame(parent, bg=BG_CARD, cursor="hand2",
                         padx=14, pady=12)
        frame.columnconfigure(1, weight=1)

        # Left accent bar (hidden by default, shown when active)
        bar = tk.Frame(frame, bg=ACCENT, width=3)
        bar.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 10))
        bar.grid_remove()

        # Icon
        icon_lbl = tk.Label(frame, text=item["icon"],
                            bg=BG_CARD, fg=TEXT_SECONDARY,
                            font=("Courier", int(16*mult)))
        icon_lbl.grid(row=0, column=1, sticky="w")

        # Label
        name_lbl = tk.Label(frame, text=item["label"],
                            bg=BG_CARD, fg=TEXT_PRIMARY,
                            font=("Georgia", int(11*mult), "bold"),
                            anchor="w")
        name_lbl.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # Description
        desc_lbl = tk.Label(frame, text=item["desc"],
                            bg=BG_CARD, fg=TEXT_DESC,
                            font=("Courier", int(8*mult)),
                            wraplength=150, justify="left",
                            anchor="w")
        desc_lbl.grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(2, 0))

        # Store refs for dynamic styling
        frame._bar       = bar
        frame._icon      = icon_lbl
        frame._name      = name_lbl
        frame._desc      = desc_lbl
        frame._key       = item["key"]
        frame._all_widgets = [frame, icon_lbl, name_lbl, desc_lbl]

        # Bind click + hover to every child
        for widget in frame._all_widgets:
            widget.bind("<Button-1>",   lambda e, k=item["key"]: self.show_frame(k))
            widget.bind("<Enter>",      lambda e, f=frame: self._nav_hover(f, True))
            widget.bind("<Leave>",      lambda e, f=frame: self._nav_hover(f, False))

        return frame

    def _nav_hover(self, frame: tk.Frame, entering: bool):
        """Highlight card on hover (skip if already active)."""
        if frame._key == self._active_key.get():
            return
        bg = BG_CARD_HVR if entering else BG_CARD
        for w in frame._all_widgets:
            w.configure(bg=bg)

    def _set_active_nav(self, key: str):
        """Update active state styling on nav buttons."""
        prev = self._active_key.get()
        self._active_key.set(key)

        for k, frame in self._nav_buttons.items():
            if k == key:
                # Active state
                for w in frame._all_widgets:
                    w.configure(bg=ACCENT_SOFT)
                frame._bar.grid()
                frame._icon.configure(fg=ACCENT)
                frame._name.configure(fg=TEXT_PRIMARY)
            else:
                # Inactive state
                for w in frame._all_widgets:
                    w.configure(bg=BG_CARD)
                frame._bar.grid_remove()
                frame._icon.configure(fg=TEXT_SECONDARY)
                frame._name.configure(fg=TEXT_PRIMARY)

    # ── Content area ─────────────────────────────────────────────────────────

    def _build_content_area(self):
        self._content = tk.Frame(self, bg=BG_DARK)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

        # Placeholder frames (replaced by real views once views/ is imported)
        for key in FRAMES:
            frame = self._make_placeholder_frame(key)
            frame.grid(row=0, column=0, sticky="nsew")
            self._frames[key] = frame

    def _make_placeholder_frame(self, key: str) -> tk.Frame:
        """Fallback content frame shown until real views are loaded."""
        labels = {
            "patient_form":      ("Register Patient",    "Fill in the form below to add a new patient."),
            "appointment_form":  ("Book Appointment",    "Select a patient and choose a date and time."),
            "summary_view":      ("Summary",             "A full table of all records will appear here."),
        }
        title, subtitle = labels.get(key, (key, ""))

        frame = tk.Frame(self._content, bg=BG_DARK)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        inner = tk.Frame(frame, bg=BG_DARK)
        inner.grid(padx=48, pady=48, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Header bar
        header = tk.Frame(inner, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 32))

        tk.Label(header, text=title, bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Georgia", int(26*mult), "bold")).pack(side="left")

        tk.Label(inner, text=subtitle, bg=BG_DARK, fg=TEXT_SECONDARY,
                 font=("Courier", int(11*mult))).pack(anchor="w", pady=(0, 24))

        # Divider
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(0, 32))

        # Placeholder content card
        card = tk.Frame(inner, bg=BG_CARD,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True)

        tk.Label(card, text=f"[ {title} form loads here ]",
                 bg=BG_CARD, fg=TEXT_DESC,
                 font=("Courier", int(12*mult))).pack(expand=True)

        return frame

    # ── Public API ────────────────────────────────────────────────────────────

    def show_frame(self, key: str):
        """Raise a content frame and update the active nav item."""
        self._set_active_nav(key)
        frame = self._frames.get(key)
        if frame:
            frame.tkraise()
        if key == "summary_view" and hasattr(frame, "on_show"):
            frame.on_show()

    def register_frame(self, key: str, frame: tk.Frame):
        """
        Allow view modules to register their own frame.
        Call from patient_form.py / appointment_form.py / summary_view.py.

        Example:
            app.register_frame("patient_form", PatientFormView(app, app))
        """
        frame.grid(row=0, column=0, sticky="nsew", in_=self._content)
        self._frames[key] = frame
        if self._active_key.get() == key:
            frame.tkraise()
            

    def _on_close(self):
        """Cleanly close the DB connection before destroying the window."""
        from database import get_connection
        try:
            conn = get_connection()
            conn.close()
        except Exception:
            pass
        self.destroy()


# ── Entry-point (used when running app.py directly for testing) ───────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()