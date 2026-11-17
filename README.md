# Contact Manager

A desktop contact management application built with **Python, Tkinter, SQLite and regular expressions**.

## Group members

- Kunjana Panthy, B24CS036 
- B J Mahalakshmi, B24CS019
- Rhythm Bhetwal, B24CS038
- Sonam Kumari, B24CS047

## Requirements

- Python 3.8 or newer
- Tkinter (ships with Python on Windows and macOS)
- No third-party packages are needed. `sqlite3`, `re`, `os` and `tkinter` are all in the standard library.

Check your Python version:

```
python --version
```

## How to run

1. Download and unzip the folder, then open a terminal inside it.
2. Run:

   ```
   python main.py
   ```

   On macOS/Linux use `python3 main.py` if `python` is not found.
3. The window opens. On first launch the app creates `address_book.db` in the same folder automatically.

**Linux only:** if you see `No module named tkinter`, install it with:

```
sudo apt install python3-tk
```

## Files

| File | Purpose | Presenter Focus |
|------|---------|-----------------|
| `validation.py` | Data validation, RegEx patterns, input sanitization, and custom exceptions | **Person 1**: RegEx & Defensive Validation |
| `database.py` | SQLite database connection, table initialization, parameterized queries, search indexing, transaction management | **Person 2**: Database Architecture & Persistence |
| `gui_view.py` | UI design system, color palettes, fonts, TTK styles, responsive layout, form card, table card, status bar | **Person 3**: UI Design, Styling & Widget Layout |
| `main.py` | Main application controller, reactive event binding, state management, CRUD action workflows, Tkinter event loop | **Person 4**: Application Controller & Event Architecture |
| `address_book.db` | Created automatically on first run (the SQLite contact database) | - |
| `README.md` | Project documentation and presentation breakdown | - |

## Features

1. **Add a contact** with name, phone number and email address.
2. **Validation** with regular expressions: live feedback under each field while typing (green tick / red cross), and a final check before anything is saved.
3. **Search** by name or phone number. Results filter live as you type; "Show All" resets the search.
4. **Edit or delete** a contact: click a row in the table, change the fields and press **Update**, or press **Delete** (asks for confirmation).
5. **Duplicate detection**: a phone number that already belongs to another contact is rejected, and the message names the existing contact.
6. **Display all contacts** in a striped table. Click a column heading to sort by it (click again to reverse). A badge in the header shows the total number of contacts.
7. **Keyboard shortcuts:** Enter adds or updates, Esc clears the form, Delete removes the selected contact.

## Validation rules

| Field | Rule | Example |
|-------|------|---------|
| Name | Starts with a letter, 2-50 characters; letters, spaces, `.` `'` `-` allowed | `Asha Rao` |
| Phone | Optional country code (`+` and 1-3 digits) followed by exactly 10 digits. Spaces, dashes and brackets are ignored | `9876543210`, `+91 98765-43210` |
| Email | `local@domain.tld`, where the TLD has at least 2 letters | `asha@mail.com` |

## How to use

- **Add:** fill in all three fields and press **Add**.
- **Search:** type a name or part of a phone number in the search box.
- **Edit:** click a contact in the table, change the details, press **Update**.
- **Delete:** click a contact, press **Delete**, confirm.
- **Clear form:** empties the form, removes the table selection and switches back to "new contact" mode. While a contact is selected, the form is in "edit" mode: Add is disabled and Update/Delete are enabled.

## Design overview & Architecture (4-Tier Split)

The project follows the **Model-View-Controller (MVC)** architectural pattern, divided into 4 modular files of equal difficulty:

1. **`validation.py` (Validation Layer - Person 1)**:
   - Compiled regular expressions (`NAME_RE`, `PHONE_RE`, `EMAIL_RE`).
   - Normalization and sanitization helpers (`normalize_phone`, `clean_name`).
   - Custom exception hierarchy (`ValidationError`, `DuplicateError`).
   - Atomic pre-save validation pipeline (`validate_contact`).

2. **`database.py` (Persistence Layer - Person 2)**:
   - `AddressBookDB` class encapsulating all SQLite operations.
   - Parameterized SQL queries (`?`) preventing SQL injection.
   - Database-level duplicate protection via `UNIQUE` constraints and `sqlite3.IntegrityError` translation.
   - Wildcard character escaping (`%`, `_`, `\`) for case-insensitive partial searches.
   - Transactional safety using Python context managers (`with self.conn:`).

3. **`gui_view.py` (View Layer - Person 3)**:
   - Complete design system: color palette tokens, fallback font detection, and TTK "clam" theme configuration.
   - Responsive multi-column layout using `ttk.Frame`, `grid()`, and weight management.
   - Left Form Card: dynamic labels, Entry fields with Return bindings, and action buttons.
   - Right List Card: Search bar, Show All button, Treeview table with alternate row striping, and vertical scrollbar.
   - Bottom Status Bar layout.

4. **`main.py` (Controller Layer - Person 4)**:
   - Inherits from `AddressBookView` and `tk.Tk`, orchestrating View, DB, and Validation layers.
   - Reactive programming: Variable tracing (`trace_add`) for real-time keystroke validation (green ticks / red crosses) and live search.
   - Application state management: switching between "New Contact" and "Edit Contact" modes.
   - Action workflows: Add, Update, Delete (with confirmation dialog), Sorting, and auto-resetting status bar timers.
   - Lifecycle management: safe cleanup and shutdown on window close.
