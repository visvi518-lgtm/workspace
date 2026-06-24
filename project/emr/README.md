# MINI EMR

MINI EMR is a lightweight desktop EMR prototype built with Python, Tkinter, and SQLite.
It focuses on the core workflow of small clinical environments: patient management,
visit notes, drug management, and patient-specific prescriptions.

## Features

- Login with password hashing using PBKDF2-HMAC-SHA256 and salt
- Patient registration, lookup, update, and deletion
- Patient-specific visit record management
- Drug master management with code, name, price, and search
- Prescription creation with quantity, directions, notes, and total price calculation
- Prescription price snapshot to preserve historical prescription amounts
- SQLite foreign keys for relational integrity
- Simple tab-based desktop UI designed around everyday workflow

## Tech Stack

- Python
- Tkinter
- SQLite
- hashlib
- calendar

## Project Structure

```text
mini-emr/
├── emr.py
├── README.md
└── .gitignore
```

## How to Run

```bash
python emr.py
```

On first run, the app creates the required SQLite tables automatically.

Default login:

```text
ID: admin
Password: admin123
```

## What I Learned

This project helped me understand that data consistency is more important than simply
building screens. I considered patient-record relationships, prescription price history,
duplicate drug code handling, and UI state synchronization.

## Future Improvements

- Stronger input validation
- Audit logs for create, update, and delete actions
- Role-based access control
- Database encryption and backup
- Transaction rollback for multi-table prescription saves
- Packaging as a standalone executable

