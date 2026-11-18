"""
validation.py
-------------
Module 1: Data Modeling, Validation Engine & Custom Exceptions
Presenter: Person 1

Responsible for:
1. Domain entity representation (Contact class)
2. Regular expression pattern compilation
3. Input sanitization and normalization
4. Custom OOP exception hierarchy
5. Composite validation pipeline with live feedback support
"""

import re


# 1. REGULAR EXPRESSIONS (Compiled Patterns)


# Name : Starts with an alphabet, allows letters, spaces, dots, hyphens, apostrophes (2-50 chars)
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")

# Phone: Optional international country code (+ and 1-3 digits) followed by exactly 10 digits
#        Examples: 9876543210, +919876543210, +19876543210
PHONE_RE = re.compile(r"^(\+\d{1,3})?\d{10}$")

# Email: RFC-compliant standard format (local_part @ domain_labels . TLD of >=2 letters)
#        Example: student.name@university.ac.in
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")



# 2. SANITIZATION & NORMALIZATION HELPERS


def normalize_phone(raw):
    """
    Strips formatting characters (spaces, dashes, parentheses, dots).
    e.g. '+91 (987) 65-43210' -> '+919876543210'
    """
    return re.sub(r"[\s\-().]", "", raw)


def clean_name(raw):
    """
    Trims outer whitespace and collapses internal multiple spaces into one.
    e.g. '   John    Doe  ' -> 'John Doe'
    """
    return " ".join(raw.split())



def is_valid_name(text):
    """Check if the provided name matches NAME_RE after normalization."""
    return bool(NAME_RE.match(clean_name(text)))


def is_valid_phone(text):
    """Check if the phone number matches PHONE_RE after stripping delimiters."""
    return bool(PHONE_RE.match(normalize_phone(text.strip())))


def is_valid_email(text):
    """Check if the email string matches EMAIL_RE."""
    return bool(EMAIL_RE.match(text.strip().lower()))




class AddressBookException(Exception):
    """Base class for domain-level exceptions in the application."""
    pass


class ValidationError(AddressBookException):
    """Raised when one or more form fields fail validation rules."""
    pass


class DuplicateError(AddressBookException):
    """Raised when attempting to save a phone number that already exists."""

    def __init__(self, existing):
        self.existing = existing  # Row or dict of the conflicting contact
        phone = existing['phone'] if isinstance(existing, dict) or hasattr(existing, '__getitem__') else getattr(existing, 'phone', 'unknown')
        name = existing['name'] if isinstance(existing, dict) or hasattr(existing, '__getitem__') else getattr(existing, 'name', 'unknown')
        super().__init__(f"Phone number {phone} already belongs to '{name}'.")




class Contact:
    """Represents a clean, validated Contact entity in the system."""

    def __init__(self, name, phone, email, contact_id=None):
        self.id = contact_id
        self.name = clean_name(name)
        self.phone = normalize_phone(phone.strip())
        self.email = email.strip().lower()

    def to_tuple(self):
        """Returns attributes as a tuple for SQL queries (name, phone, email)."""
        return self.name, self.phone, self.email

    def __repr__(self):
        return f"<Contact id={self.id} name='{self.name}' phone='{self.phone}'>"


def validate_contact(name, phone, email):
    """
    Validates all contact fields collectively before database operations.
    Returns cleaned (name, phone, email) or raises ValidationError with combined issues.
    """
    problems = []
    if not is_valid_name(name):
        problems.append(
            "Name: 2-50 characters, must start with a letter "
            "(letters, spaces, . ' - allowed)."
        )
    if not is_valid_phone(phone):
        problems.append(
            "Phone: 10 digits, optionally with a country code "
            "(e.g. 9876543210 or +919876543210)."
        )
    if not is_valid_email(email):
        problems.append("Email: must look like name@domain.com.")

    if problems:
        raise ValidationError("\n".join(problems))

    return clean_name(name), normalize_phone(phone.strip()), email.strip().lower()



if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: Validation Engine & Regular Expressions (Person 1)")
    print("=" * 60)

    sample_tests = [
        ("Alice Smith", "+91 98765-43210", "alice@example.com"),
        ("123BadName", "12345", "not-an-email"),
        ("Bob O'Connor", "9876543210", "bob.oc@college.edu"),
    ]

    for n, p, e in sample_tests:
        print(f"\nTesting input -> Name: '{n}', Phone: '{p}', Email: '{e}'")
        try:
            valid_n, valid_p, valid_e = validate_contact(n, p, e)
            print(f"  [PASSED] Sanitized: Name='{valid_n}', Phone='{valid_p}', Email='{valid_e}'")
        except ValidationError as err:
            print("  [FAILED Validation]:")
            for line in str(err).splitlines():
                print(f"    - {line}")

    print("\n" + "=" * 60)
    print("All validation rules and normalization functions verified.")
    print("=" * 60)
