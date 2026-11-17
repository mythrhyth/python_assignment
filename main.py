"""
main.py
-------
Module 4: Application Controller, Reactive State & Event Loop
Presenter: Person 4

Responsible for:
1. Orchestrating the Model (validation.py), View (gui_view.py), and Storage (database.py)
2. Reactive event bindings: Keystroke validation traces and live as-you-type search
3. Application state machine (switching between 'New Contact' and 'Edit Contact' modes)
4. CRUD controller workflows (Add, Update, Delete with confirmation dialogs)
5. Non-blocking asynchronous timers (status bar auto-reset) and window lifecycle

Run the complete application with:
    python main.py
"""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from validation import (
    validate_contact,
    ValidationError,
    DuplicateError,
)
from database import AddressBookDB
from gui_view import (
    AddressBookView,
    BG,
    DEFAULT_TIP,
    MUTED,
    SUCCESS,
    DANGER,
)


class AddressBookApp(AddressBookView, tk.Tk):
    """
    Main Controller: integrates the AddressBookView with AddressBookDB
    and input validation logic.
    """

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Digital Address Book")
        self.configure(bg=BG)
        self.minsize(920, 580)
        self._center_window(1000, 650)

        # 1. Database layer initialization with error recovery
        try:
            self.db = AddressBookDB()
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not open the database:\n{exc}")
            self.destroy()
            raise SystemExit(1)

        # 2. State machine variables
        self.selected_id = None      # ID of contact currently loaded in the form
        self.sort_col = "name"       # Table sorted by this column
        self.sort_desc = False       # Sort direction flag
        self._status_job = None      # Timer handle for auto-resetting status bar

        # 3. Tkinter dynamic StringVars
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value=DEFAULT_TIP)
        self.count_var = tk.StringVar()
        self.result_var = tk.StringVar()

        # 4. Construct visual layout and styles (inherited from AddressBookView)
        self._setup_fonts()
        self._setup_styles()
        self._build_header()
        self._build_body()
        self._build_status_bar()

        # 5. Event bindings & Reactive Tracing
        # Live feedback: re-check the fields on every keystroke
        for var in (self.name_var, self.phone_var, self.email_var):
            var.trace_add("write", lambda *_: self.update_feedback())

        # Live search: re-query database as the user types
        self.search_var.trace_add("write", lambda *_: self.refresh())

        # Keyboard shortcuts and window close intercept
        self.bind("<Escape>", lambda _e: self.clear_form())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 6. Set initial application state
        self.set_mode(editing=False)
        self.update_feedback()
        self.refresh()

    # ---- UI State & Feedback Helpers --------------------------------------
    def set_status(self, message, kind="info"):
        """Show a coloured message in the status bar; it fades back to the tip after 5 s."""
        colour = {"info": MUTED, "success": SUCCESS, "error": DANGER}[kind]
        self.style.configure("Status.TLabel", foreground=colour)
        self.status_var.set(message)
        if self._status_job:
            self.after_cancel(self._status_job)
        self._status_job = self.after(5000, self._reset_status)

    def _reset_status(self):
        """Callback to reset status text back to the default tip."""
        self._status_job = None
        self.style.configure("Status.TLabel", foreground=MUTED)
        self.status_var.set(DEFAULT_TIP)

    def set_mode(self, editing):
        """Switch the form between 'New Contact' and 'Edit Contact' mode."""
        if editing:
            self.mode_var.set("Edit contact")
            self.mode_sub_var.set(
                "Change the details, then press Update. "
                "Press Clear form to add a new contact instead."
            )
        else:
            self.mode_var.set("New contact")
            self.mode_sub_var.set("Fill in the details below and press Add Contact.")
        self.add_btn.state(["disabled"] if editing else ["!disabled"])
        for btn in (self.update_btn, self.delete_btn):
            btn.state(["!disabled"] if editing else ["disabled"])

    def update_feedback(self):
        """Live regex feedback under each field (neutral / valid / invalid)."""
        for var, entry, hint, check, tip in self.fields.values():
            text = var.get()
            if not text.strip():
                entry.state(["!invalid"])
                hint.configure(text=tip, foreground=MUTED)
            elif check(text):
                entry.state(["!invalid"])
                hint.configure(text="\u2713 Looks good", foreground=SUCCESS)
            else:
                entry.state(["invalid"])
                hint.configure(text="\u2715 " + tip, foreground=DANGER)

    def sort_by(self, col):
        """Clicking a column heading sorts by it; clicking again reverses the order."""
        if self.sort_col == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col, self.sort_desc = col, False
        self.refresh()

    # ---- Data Synchronization -> Table -----------------------------------
    def refresh(self):
        """Reload the table using the current search text (empty text = all contacts)."""
        try:
            rows = self.db.search(self.search_var.get())
            total = len(self.db.get_all())
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not load contacts:\n{exc}")
            return

        rows = sorted(rows, key=lambda r: str(r[self.sort_col]).lower(), reverse=self.sort_desc)

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            # iid = database id, so we always know which contact a selected row represents
            self.tree.insert(
                "", "end", iid=str(r["id"]),
                values=(r["name"], r["phone"], r["email"]),
                tags=("even" if i % 2 else "odd",)
            )

        arrow = " \u25BC" if self.sort_desc else " \u25B2"
        for col, (text, _w) in self.columns.items():
            self.tree.heading(col, text=text + (arrow if col == self.sort_col else ""))

        self.count_var.set(f"{total} contact" + ("" if total == 1 else "s"))
        if self.search_var.get().strip():
            self.result_var.set(f"{len(rows)} of {total} match your search")
        else:
            self.result_var.set(
                "Type in the box to search by name or phone number"
                if total else "No contacts yet. Add your first one on the left."
            )

    def show_all(self):
        """Reset the search box and reload all contacts."""
        self.search_var.set("")   # triggers refresh via the trace
        self.clear_form()

    def clear_form(self):
        """Reset form fields, clear table selection, and reset to 'new' mode."""
        self.selected_id = None
        self.name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.set_mode(editing=False)
        self.name_entry.focus_set()

    def on_select(self, _event=None):
        """Load selected table contact into the input form for editing."""
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        name, phone, email = self.tree.item(sel[0], "values")
        self.name_var.set(name)
        self.phone_var.set(phone)
        self.email_var.set(email)
        self.set_mode(editing=True)

    def _read_form(self):
        """Validate form input; show an error box and return None if invalid."""
        try:
            return validate_contact(
                self.name_var.get(), self.phone_var.get(), self.email_var.get()
            )
        except ValidationError as exc:
            messagebox.showerror("Invalid input", str(exc))
            self.set_status("Please fix the highlighted fields.", "error")
            return None

    # ---- Actions & Controller Logic --------------------------------------
    def submit(self, _event=None):
        """Enter key handler: add in 'new' mode, update in 'edit' mode."""
        if self.selected_id is None:
            self.add_contact()
        else:
            self.update_contact()

    def add_contact(self):
        """Validate and insert a new contact into the database."""
        data = self._read_form()
        if not data:
            return
        try:
            self.db.add(*data)
        except DuplicateError as exc:
            messagebox.showwarning("Duplicate phone number", str(exc))
            self.set_status("Duplicate phone number - contact not saved.", "error")
            return
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not save contact:\n{exc}")
            return
        self.clear_form()
        self.refresh()
        self.set_status(f"Added '{data[0]}'.", "success")

    def update_contact(self):
        """Validate and update the currently selected contact in the database."""
        if self.selected_id is None:
            messagebox.showinfo("Update", "Select a contact from the table first.")
            return
        data = self._read_form()
        if not data:
            return
        try:
            self.db.update(self.selected_id, *data)
        except DuplicateError as exc:
            messagebox.showwarning("Duplicate phone number", str(exc))
            self.set_status("Duplicate phone number - contact not updated.", "error")
            return
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not update contact:\n{exc}")
            return
        self.clear_form()
        self.refresh()
        self.set_status(f"Updated '{data[0]}'.", "success")

    def delete_contact(self):
        """Prompt confirmation and delete the selected contact from the database."""
        if self.selected_id is None:
            messagebox.showinfo("Delete", "Select a contact from the table first.")
            return
        name = self.name_var.get()
        if not messagebox.askyesno("Confirm delete", f"Delete '{name}' permanently?"):
            return
        try:
            self.db.delete(self.selected_id)
        except sqlite3.Error as exc:
            messagebox.showerror("Database error", f"Could not delete contact:\n{exc}")
            return
        self.clear_form()
        self.refresh()
        self.set_status(f"Deleted '{name}'.", "success")

    def _on_close(self):
        """Gracefully close the database connection and destroy the application window."""
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    AddressBookApp().mainloop()
