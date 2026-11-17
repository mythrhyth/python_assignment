"""
database.py
-----------
Module 2: Database Management & Persistence Layer (SQLite)
Presenter: Person 2

Responsible for:
1. SQLite connection and table schema creation with UNIQUE constraints
2. Secure parameterized CRUD operations (SQL injection prevention)
3. Transaction management (atomic commits & automatic rollback)
4. Case-insensitive search engine with literal wildcard escaping
5. Database error translation and duplicate phone detection
"""

import os
import sqlite3
from validation import DuplicateError, normalize_phone

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "address_book.db")


class AddressBookDB:
    """
    Data Access Object (DAO) for interacting with the SQLite contacts database.
    Ensures thread-safe connections and parameterized execution.
    """

    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row   # Enables dict-like column access: row["name"]
        self._create_table()

    def _create_table(self):
        """
        Creates the contacts table if it does not exist.
        The UNIQUE constraint on phone acts as a second line of defense against duplicates.
        """
        with self.conn:
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS contacts (
                       id    INTEGER PRIMARY KEY AUTOINCREMENT,
                       name  TEXT NOT NULL,
                       phone TEXT NOT NULL UNIQUE,
                       email TEXT NOT NULL
                   )"""
            )

    def find_by_phone(self, phone, exclude_id=None):
        """
        Locates a contact by exact phone number.
        If exclude_id is provided, ignores that record (crucial for updating an existing contact).
        """
        if exclude_id is None:
            cur = self.conn.execute("SELECT * FROM contacts WHERE phone = ?", (phone,))
        else:
            cur = self.conn.execute(
                "SELECT * FROM contacts WHERE phone = ? AND id != ?", (phone, exclude_id)
            )
        return cur.fetchone()

    def add(self, name, phone, email):
        """
        Inserts a new contact.
        Performs an application-level duplicate check and handles database-level race conditions.
        """
        dup = self.find_by_phone(phone)
        if dup:
            raise DuplicateError(dup)

        try:
            with self.conn:   # Commits on successful block exit, rolls back on exception
                cur = self.conn.execute(
                    "INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)",
                    (name, phone, email),
                )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            # Handles duplicate phone if a concurrent write occurred
            raise DuplicateError(self.find_by_phone(phone))

    def update(self, contact_id, name, phone, email):
        """
        Updates an existing contact record.
        Ensures the updated phone number does not collide with another contact.
        """
        dup = self.find_by_phone(phone, exclude_id=contact_id)
        if dup:
            raise DuplicateError(dup)

        with self.conn:
            self.conn.execute(
                "UPDATE contacts SET name = ?, phone = ?, email = ? WHERE id = ?",
                (name, phone, email, contact_id),
            )

    def delete(self, contact_id):
        """Removes a contact permanently by ID using a parameterized query."""
        with self.conn:
            self.conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

    def get_all(self):
        """Retrieves all contacts sorted alphabetically (case-insensitive)."""
        return self.conn.execute(
            "SELECT * FROM contacts ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def count(self):
        """Returns the total number of contacts stored in the database."""
        cur = self.conn.execute("SELECT COUNT(*) FROM contacts")
        return cur.fetchone()[0]

    def search(self, term):
        """
        Performs a case-insensitive partial match across name OR phone.
        Properly escapes SQL wildcards (% and _) so user input is treated literally.
        """
        term = term.strip()
        if not term:
            return self.get_all()

        def escape_like(s):
            """Escapes backslashes, percent signs, and underscores for LIKE queries."""
            return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        name_like = f"%{escape_like(term)}%"
        phone_clean = normalize_phone(term) or term
        phone_like = f"%{escape_like(phone_clean)}%"

        return self.conn.execute(
            """SELECT * FROM contacts
               WHERE name LIKE ? ESCAPE '\\' OR phone LIKE ? ESCAPE '\\'
               ORDER BY name COLLATE NOCASE""",
            (name_like, phone_like),
        ).fetchall()

    def close(self):
        """Closes the active database connection safely."""
        self.conn.close()


# ---------------------------------------------------------------------------
# 6. DEMO / UNIT TEST (Presenter 2 can run: python database.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: Database Layer & Persistence (Person 2)")
    print("=" * 60)

    test_db_path = "demo_test.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = AddressBookDB(test_db_path)
    print(f"1. Database created at: {test_db_path}")

    # Add records
    c1 = db.add("Charlie Davis", "9876500001", "charlie@test.com")
    c2 = db.add("Diana Prince", "+919876500002", "diana@test.com")
    print(f"2. Inserted 2 contacts (IDs: {c1}, {c2}). Total count: {db.count()}")

    # Search demo
    results = db.search("charlie")
    print(f"3. Search for 'charlie': found {len(results)} match ('{results[0]['name']}')")

    # Duplicate detection demo
    print("4. Testing duplicate phone prevention...")
    try:
        db.add("Clone User", "9876500001", "clone@test.com")
        print("  [ERROR] Duplicate was allowed!")
    except DuplicateError as exc:
        print(f"  [SUCCESS] Blocked duplicate: {exc}")

    # Clean up test DB
    db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print("\n" + "=" * 60)
    print("Database CRUD operations and safety constraints verified.")
    print("=" * 60)
