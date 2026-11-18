"""
gui_view.py
-----------
Module 3: UI Design System, Widget Styling & Responsive Layout

Responsible for:
1. Visual design system (modern color palette and dynamic OS font fallbacks)
2. TTK theme customization ('clam' theme with interactive button & input states)
3. Responsive geometry management (grid weighting, card containers, dynamic resizing)
4. Form input widgets with validation feedback hint labels
5. Treeview table construction with alternating row striping and scrollbar integration
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from validation import is_valid_name, is_valid_phone, is_valid_email


# COLOR PALETTE & DESIGN SYSTEM TOKENS

PRIMARY, PRIMARY_DARK = "#4F46E5", "#4338CA"
SUCCESS, SUCCESS_DARK = "#16A34A", "#15803D"
DANGER, DANGER_DARK = "#DC2626", "#B91C1C"
GREY, GREY_DARK = "#E5E7EB", "#D1D5DB"
BG, CARD = "#F3F4F6", "#FFFFFF"
TEXT, MUTED, BORDER = "#111827", "#6B7280", "#D1D5DB"
HEAD_BG, ROW_ALT = "#EEF2FF", "#F9FAFB"
DISABLED_BG, DISABLED_FG = "#E5E7EB", "#9CA3AF"

DEFAULT_TIP = "Tip: click a contact in the table to edit or delete it."


class AddressBookView:
    """
    View Layer: handles window geometry, styling, and responsive widget hierarchy.
    Designed to be mixed into the main Application Controller.
    """

    def _center_window(self, width, height):
        """Centers the application window on the user's primary monitor."""
        x = (self.winfo_screenwidth() - width) // 2
        y = max((self.winfo_screenheight() - height) // 3, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_fonts(self):
        """Detects available high-quality system fonts with automatic fallback."""
        available = set(tkfont.families(self))
        family = next(
            (f for f in ("Segoe UI", "Helvetica Neue", "Calibri", "Helvetica", "Arial")
             if f in available),
            tkfont.nametofont("TkDefaultFont").actual("family")
        )
        self.f_base = (family, 11)
        self.f_bold = (family, 11, "bold")
        self.f_small = (family, 10)
        self.f_title = (family, 22, "bold")
        self.f_card = (family, 15, "bold")

    def _button_style(self, name, bg, hover, fg="white"):
        """Configures interactive TTK button styles (normal, hover, pressed, disabled)."""
        s = self.style
        s.configure(
            name, background=bg, foreground=fg, borderwidth=0, relief="flat",
            padding=(12, 9), font=self.f_bold, focusthickness=0
        )
        s.map(
            name,
            background=[("disabled", DISABLED_BG), ("pressed", hover), ("active", hover)],
            foreground=[("disabled", DISABLED_FG)]
        )

    def _setup_styles(self):
        """Configures custom TTK styles using the cross-platform 'clam' theme engine."""
        self.style = s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=CARD)
        s.configure("Header.TFrame", background=PRIMARY)

        s.configure("Header.TLabel", background=PRIMARY, foreground="white", font=self.f_title)
        s.configure("HeaderSub.TLabel", background=PRIMARY, foreground="#C7D2FE", font=self.f_base)
        s.configure("Badge.TLabel", background="#6366F1", foreground="white",
                    font=self.f_bold, padding=(14, 6))
        s.configure("CardTitle.TLabel", background=CARD, foreground=TEXT, font=self.f_card)
        s.configure("CardSub.TLabel", background=CARD, foreground=MUTED, font=self.f_small)
        s.configure("Field.TLabel", background=CARD, foreground=TEXT, font=self.f_bold)
        s.configure("Hint.TLabel", background=CARD, foreground=MUTED, font=self.f_small)
        s.configure("Result.TLabel", background=CARD, foreground=MUTED, font=self.f_small)
        s.configure("Status.TLabel", background=BG, foreground=MUTED, font=self.f_small)

        s.configure(
            "Field.TEntry", padding=8, fieldbackground="white", foreground=TEXT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER
        )
        s.map(
            "Field.TEntry",
            bordercolor=[("invalid", DANGER), ("focus", PRIMARY)],
            lightcolor=[("invalid", DANGER), ("focus", PRIMARY)],
            darkcolor=[("invalid", DANGER), ("focus", PRIMARY)]
        )

        self._button_style("Primary.TButton", PRIMARY, PRIMARY_DARK)
        self._button_style("Success.TButton", SUCCESS, SUCCESS_DARK)
        self._button_style("Danger.TButton", DANGER, DANGER_DARK)
        self._button_style("Neutral.TButton", GREY, GREY_DARK, fg=TEXT)

        # Treeview styling with custom row height and selection colors
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        s.configure(
            "Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
            rowheight=34, borderwidth=0, font=self.f_base
        )
        s.map("Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "white")])
        s.configure(
            "Treeview.Heading", background=HEAD_BG, foreground=TEXT, relief="flat",
            font=self.f_bold, padding=(10, 9)
        )
        s.map("Treeview.Heading", background=[("active", "#E0E7FF")])

    def _build_header(self):
        """Constructs the responsive top header bar with branding and contact count badge."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Header.TFrame", padding=(26, 18))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Address Book", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header, text="Store, search and manage your contacts", style="HeaderSub.TLabel"
        ).grid(row=1, column=0, sticky="w")
        ttk.Label(header, textvariable=self.count_var, style="Badge.TLabel").grid(
            row=0, column=1, rowspan=2, sticky="e"
        )

    def _build_body(self):
        """Constructs the two-column responsive body container."""
        body = ttk.Frame(self, padding=(20, 20, 20, 8))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)   # Right table expands to take remaining width
        body.rowconfigure(0, weight=1)      # Expands vertically on resize
        self._build_form_card(body)
        self._build_list_card(body)

    def _build_form_card(self, parent):
        """Constructs the left card containing input fields, validation hints, and buttons."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=22)
        card.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar()
        self.mode_sub_var = tk.StringVar()
        ttk.Label(card, textvariable=self.mode_var, style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            card, textvariable=self.mode_sub_var, style="CardSub.TLabel", wraplength=290
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

        # Field specifications: (key, label, StringVar, validation_fn, hint_text)
        specs = [
            ("name", "Full name", self.name_var, is_valid_name,
             "2-50 letters; spaces . ' - allowed"),
            ("phone", "Phone number", self.phone_var, is_valid_phone,
             "10 digits, optional +country code"),
            ("email", "Email address", self.email_var, is_valid_email,
             "Format: name@domain.com"),
        ]
        self.fields = {}
        row = 2
        for key, label, var, check, tip in specs:
            ttk.Label(card, text=label, style="Field.TLabel").grid(
                row=row, column=0, columnspan=2, sticky="w"
            )
            entry = ttk.Entry(
                card, textvariable=var, style="Field.TEntry", width=30, font=self.f_base
            )
            entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
            entry.bind("<Return>", self.submit)

            hint = ttk.Label(card, text=tip, style="Hint.TLabel")
            hint.grid(row=row + 2, column=0, columnspan=2, sticky="w", pady=(3, 12))
            self.fields[key] = (var, entry, hint, check, tip)
            row += 3

        self.name_entry = self.fields["name"][1]

        # Action Buttons
        self.add_btn = ttk.Button(
            card, text="Add Contact", style="Primary.TButton",
            command=self.add_contact, cursor="hand2"
        )
        self.add_btn.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 8))

        self.update_btn = ttk.Button(
            card, text="Update", style="Success.TButton",
            command=self.update_contact, cursor="hand2"
        )
        self.update_btn.grid(row=row + 1, column=0, sticky="ew", padx=(0, 4), pady=(0, 8))

        self.delete_btn = ttk.Button(
            card, text="Delete", style="Danger.TButton",
            command=self.delete_contact, cursor="hand2"
        )
        self.delete_btn.grid(row=row + 1, column=1, sticky="ew", padx=(4, 0), pady=(0, 8))

        ttk.Button(
            card, text="Clear form", style="Neutral.TButton",
            command=self.clear_form, cursor="hand2"
        ).grid(row=row + 2, column=0, columnspan=2, sticky="ew")

    def _build_list_card(self, parent):
        """Constructs the right card containing search bar, Treeview table, and scrollbars."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=22)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(3, weight=1)   # Table row expands to take all spare height

        ttk.Label(card, text="All contacts", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        # Search Controls
        search = ttk.Frame(card, style="Card.TFrame")
        search.grid(row=1, column=0, sticky="ew", pady=(12, 4))
        search.columnconfigure(0, weight=1)

        self.search_entry = ttk.Entry(
            search, textvariable=self.search_var, style="Field.TEntry", font=self.f_base
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Button(
            search, text="Show All", style="Neutral.TButton",
            command=self.show_all, cursor="hand2"
        ).grid(row=0, column=1)

        ttk.Label(card, textvariable=self.result_var, style="Result.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 8)
        )

        # Treeview Table with Vertical Scrollbar
        table = ttk.Frame(card, style="Card.TFrame")
        table.grid(row=3, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)

        self.columns = {"name": ("Name", 210), "phone": ("Phone", 150), "email": ("Email", 260)}
        self.tree = ttk.Treeview(
            table, columns=tuple(self.columns), show="headings", selectmode="browse"
        )
        for col, (text, width) in self.columns.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width, anchor="w", stretch=True)

        self.tree.tag_configure("odd", background=CARD)
        self.tree.tag_configure("even", background=ROW_ALT)

        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Treeview event bindings
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Delete>", lambda _e: self.delete_contact())
        self.tree.bind("<BackSpace>", lambda _e: self.delete_contact())

    def _build_status_bar(self):
        """Constructs the bottom status bar for user feedback notifications."""
        ttk.Label(
            self, textvariable=self.status_var, style="Status.TLabel",
            anchor="w", padding=(24, 4, 24, 12)
        ).grid(row=2, column=0, sticky="ew")



# 6. DEMO / PREVIEW

if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: UI Layout & Design System Preview (Person 3)")
    print("=" * 60)

    class ViewPreviewApp(AddressBookView, tk.Tk):
        """Standalone preview allowing Person 3 to demonstrate the UI layout."""
        def __init__(self):
            tk.Tk.__init__(self)
            self.title("UI Design & Layout Preview - Person 3")
            self.configure(bg=BG)
            self.minsize(920, 580)
            self._center_window(1000, 650)

            self.count_var = tk.StringVar(value="Preview Mode (0 contacts)")
            self.result_var = tk.StringVar(value="Type in the search box to test layout")
            self.status_var = tk.StringVar(value=DEFAULT_TIP)
            self.search_var = tk.StringVar()
            self.name_var = tk.StringVar()
            self.phone_var = tk.StringVar()
            self.email_var = tk.StringVar()

            # Stub actions for preview
            self.submit = lambda e=None: None
            self.add_contact = lambda: None
            self.update_contact = lambda: None
            self.delete_contact = lambda: None
            self.clear_form = lambda: None
            self.show_all = lambda: None
            self.sort_by = lambda c: None
            self.on_select = lambda e=None: None

            self._setup_fonts()
            self._setup_styles()
            self._build_header()
            self._build_body()
            self._build_status_bar()

            self.mode_var.set("New contact (UI Preview)")
            self.mode_sub_var.set("Responsive grid and widgets rendered successfully.")

    print("Opening standalone UI preview window...")
    preview = ViewPreviewApp()
    preview.mainloop()
