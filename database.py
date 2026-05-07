import sqlite3

DB_NAME = "expenses.db"

VALID_CATEGORIES = ["Food", "Transportation", "Education", "Utilities", "Entertainment", "Other"]

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Creates the tables if they don't exist yet. Run this once at startup."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            month   TEXT PRIMARY KEY,
            amount  REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_expense(category, amount, date, description=""):
    """Inserts a new expense into the database."""
    if category not in VALID_CATEGORIES:
        print(f"Invalid category: {category}. Choose from: {VALID_CATEGORIES}")
        return False

    if not isinstance(amount, (int, float)) or amount <= 0:
        print("Amount must be a positive number.")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses (category, amount, date, description)
        VALUES (?, ?, ?, ?)
    """, (category, amount, date, description))

    conn.commit()
    conn.close()
    print(f"Expense added: {category} - ₱{amount:.2f} on {date}")
    return True

def get_expenses_by_month(month):
    """Retrieves all expenses for a given month (format: YYYY-MM)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM expenses
        WHERE date LIKE ?
        ORDER BY date ASC
    """, (f"{month}%",))

    rows = cursor.fetchall()
    conn.close()
    return rows

def edit_expense(expense_id, category=None, amount=None, date=None, description=None):
    """Updates one or more fields of an existing expense."""
    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    values = []

    if category is not None:
        if category not in VALID_CATEGORIES:
            print(f"Invalid category: {category}")
            conn.close()
            return False
        fields.append("category = ?")
        values.append(category)

    if amount is not None:
        if amount <= 0:
            print("Amount must be positive.")
            conn.close()
            return False
        fields.append("amount = ?")
        values.append(amount)

    if date is not None:
        fields.append("date = ?")
        values.append(date)

    if description is not None:
        fields.append("description = ?")
        values.append(description)

    if not fields:
        print("No fields provided to update.")
        conn.close()
        return False

    values.append(expense_id)
    query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"

    cursor.execute(query, values)
    conn.commit()
    conn.close()
    print(f"Expense ID {expense_id} updated.")
    return True

def delete_expense(expense_id):
    """Deletes an expense by its ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    print(f"Expense ID {expense_id} deleted.")

def set_budget(month, amount):
    """Sets or updates the monthly budget for a given month (format: YYYY-MM)."""
    if amount <= 0:
        print("Budget must be a positive number.")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO budgets (month, amount)
        VALUES (?, ?)
    """, (month, amount))

    conn.commit()
    conn.close()
    print(f"Budget for {month} set to ₱{amount:.2f}")
    return True

def get_budget(month):
    """Returns the budget amount for a given month, or 0.0 if not set."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT amount FROM budgets WHERE month = ?", (month,))
    row = cursor.fetchone()
    conn.close()

    return row["amount"] if row else 0.0
