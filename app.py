import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    initialize_db, add_expense, get_expenses_by_month,
    edit_expense, delete_expense, set_budget, get_budget,
    VALID_CATEGORIES
)
from logic import check_budget_warning, compute_totals_by_category, save_to_file
from graphs import generate_pie_chart, compare_months

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Expense Tracker")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        self.current_month = datetime.now().strftime("%Y-%m")

        initialize_db()
        self._build_ui()
        self._load_expenses()
        self._update_budget_display()

    # ── UI BUILDER ──────────────────────────────────────────────

    def _build_ui(self):
        """Builds the full UI layout."""

        # Top bar
        top = tk.Frame(self.root, pady=8, padx=12)
        top.pack(fill="x")

        tk.Label(top, text="Student Expense Tracker", font=("Helvetica", 16, "bold")).pack(side="left")

        # Month selector
        tk.Label(top, text="Month:").pack(side="left", padx=(20, 4))
        self.month_var = tk.StringVar(value=self.current_month)
        month_entry = tk.Entry(top, textvariable=self.month_var, width=10)
        month_entry.pack(side="left")
        tk.Button(top, text="Load", command=self._on_load_month).pack(side="left", padx=4)

        # Budget display
        self.budget_label = tk.Label(top, text="", font=("Helvetica", 10))
        self.budget_label.pack(side="right", padx=12)

        # Button bar
        btn_bar = tk.Frame(self.root, pady=4, padx=12)
        btn_bar.pack(fill="x")

        buttons = [
            ("+ Add Expense",   self._open_add_dialog),
            ("Edit Expense",    self._open_edit_dialog),
            ("Delete Expense",  self._on_delete),
            ("Set Budget",      self._open_budget_dialog),
            ("Pie Chart",       self._on_pie_chart),
            ("Compare Months",  self._open_compare_dialog),
            ("Export to .txt",  self._on_export),
        ]

        for label, command in buttons:
            tk.Button(btn_bar, text=label, command=command, width=14).pack(side="left", padx=3)

        # Expense table
        table_frame = tk.Frame(self.root, padx=12, pady=8)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "date", "category", "amount", "description")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id",          text="ID")
        self.tree.heading("date",        text="Date")
        self.tree.heading("category",    text="Category")
        self.tree.heading("amount",      text="Amount (₱)")
        self.tree.heading("description", text="Description")

        self.tree.column("id",          width=40,  anchor="center")
        self.tree.column("date",        width=100, anchor="center")
        self.tree.column("category",    width=120, anchor="center")
        self.tree.column("amount",      width=100, anchor="center")
        self.tree.column("description", width=400)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self.root, textvariable=self.status_var, anchor="w",
                 padx=12, pady=4, fg="gray").pack(fill="x", side="bottom")


    # ── DATA LOADING ─────────────────────────────────────────────

    def _load_expenses(self):
        """Clears and reloads the expense table for the current month."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        month = self.month_var.get().strip()
        rows = get_expenses_by_month(month)

        for row in rows:
            self.tree.insert("", "end", values=(
                row["id"],
                row["date"],
                row["category"],
                f"₱{row['amount']:.2f}",
                row["description"] or ""
            ))

        self.status_var.set(f"Loaded {len(rows)} expense(s) for {month}.")
        self._update_budget_display()

    def _update_budget_display(self):
        """Updates the budget label in the top bar."""
        month = self.month_var.get().strip()
        result = check_budget_warning(month)

        if result["status"] == "no_budget":
            self.budget_label.config(text="No budget set.", fg="gray")
        elif result["status"] == "exceeded":
            self.budget_label.config(
                text=f"EXCEEDED: ₱{result['spent']:.2f} / ₱{result['budget']:.2f}",
                fg="red"
            )
            messagebox.showerror("Budget Exceeded!", result["message"])
        elif result["status"] == "warning":
            self.budget_label.config(
                text=f"WARNING: ₱{result['spent']:.2f} / ₱{result['budget']:.2f} ({result['percentage']*100:.1f}%)",
                fg="orange"
            )
            messagebox.showwarning("Budget Warning", result["message"])
        else:
            self.budget_label.config(
                text=f"Budget OK: ₱{result['spent']:.2f} / ₱{result['budget']:.2f} ({result['percentage']*100:.1f}%)",
                fg="green"
            )

    def _on_load_month(self):
        """Validates month input and reloads the table."""
        month = self.month_var.get().strip()
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            messagebox.showerror("Invalid Format", "Please enter month as YYYY-MM, e.g. 2025-04")
            return
        self._load_expenses()


    # ── ADD EXPENSE DIALOG ────────────────────────────────────────

    def _open_add_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Expense")
        dialog.geometry("360x280")
        dialog.grab_set()  # locks focus to this window

        fields = {}

        def add_field(label, row, widget_fn):
            tk.Label(dialog, text=label, anchor="w").grid(row=row, column=0, padx=16, pady=6, sticky="w")
            widget = widget_fn()
            widget.grid(row=row, column=1, padx=16, pady=6, sticky="ew")
            fields[label] = widget

        dialog.columnconfigure(1, weight=1)

        # Category dropdown
        tk.Label(dialog, text="Category", anchor="w").grid(row=0, column=0, padx=16, pady=6, sticky="w")
        cat_var = tk.StringVar(value=VALID_CATEGORIES[0])
        cat_menu = ttk.Combobox(dialog, textvariable=cat_var, values=VALID_CATEGORIES, state="readonly")
        cat_menu.grid(row=0, column=1, padx=16, pady=6, sticky="ew")

        # Amount
        tk.Label(dialog, text="Amount (₱)", anchor="w").grid(row=1, column=0, padx=16, pady=6, sticky="w")
        amount_entry = tk.Entry(dialog)
        amount_entry.grid(row=1, column=1, padx=16, pady=6, sticky="ew")

        # Date
        tk.Label(dialog, text="Date (YYYY-MM-DD)", anchor="w").grid(row=2, column=0, padx=16, pady=6, sticky="w")
        date_entry = tk.Entry(dialog)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=2, column=1, padx=16, pady=6, sticky="ew")

        # Description
        tk.Label(dialog, text="Description", anchor="w").grid(row=3, column=0, padx=16, pady=6, sticky="w")
        desc_entry = tk.Entry(dialog)
        desc_entry.grid(row=3, column=1, padx=16, pady=6, sticky="ew")

        def on_submit():
            category = cat_var.get()
            date = date_entry.get().strip()
            description = desc_entry.get().strip()

            # Validate amount
            try:
                amount = float(amount_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Amount must be a number.", parent=dialog)
                return

            # Validate date
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Input", "Date must be YYYY-MM-DD.", parent=dialog)
                return

            success = add_expense(category, amount, date, description)
            if success:
                dialog.destroy()
                self._load_expenses()

        tk.Button(dialog, text="Add Expense", command=on_submit).grid(
            row=4, column=0, columnspan=2, pady=16)


    # ── EDIT EXPENSE DIALOG ───────────────────────────────────────

    def _open_edit_dialog(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showinfo("No Selection", "Please click on an expense to select it first.")
            return

        values = self.tree.item(selected, "values")
        expense_id = values[0]
        current_date = values[1]
        current_category = values[2]
        current_amount = values[3].replace("₱", "")
        current_desc = values[4]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Expense #{expense_id}")
        dialog.geometry("360x280")
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)

        tk.Label(dialog, text="Category", anchor="w").grid(row=0, column=0, padx=16, pady=6, sticky="w")
        cat_var = tk.StringVar(value=current_category)
        cat_menu = ttk.Combobox(dialog, textvariable=cat_var, values=VALID_CATEGORIES, state="readonly")
        cat_menu.grid(row=0, column=1, padx=16, pady=6, sticky="ew")

        tk.Label(dialog, text="Amount (₱)", anchor="w").grid(row=1, column=0, padx=16, pady=6, sticky="w")
        amount_entry = tk.Entry(dialog)
        amount_entry.insert(0, current_amount)
        amount_entry.grid(row=1, column=1, padx=16, pady=6, sticky="ew")

        tk.Label(dialog, text="Date (YYYY-MM-DD)", anchor="w").grid(row=2, column=0, padx=16, pady=6, sticky="w")
        date_entry = tk.Entry(dialog)
        date_entry.insert(0, current_date)
        date_entry.grid(row=2, column=1, padx=16, pady=6, sticky="ew")

        tk.Label(dialog, text="Description", anchor="w").grid(row=3, column=0, padx=16, pady=6, sticky="w")
        desc_entry = tk.Entry(dialog)
        desc_entry.insert(0, current_desc)
        desc_entry.grid(row=3, column=1, padx=16, pady=6, sticky="ew")

        def on_submit():
            try:
                amount = float(amount_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Amount must be a number.", parent=dialog)
                return

            date = date_entry.get().strip()
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Input", "Date must be YYYY-MM-DD.", parent=dialog)
                return

            edit_expense(
                int(expense_id),
                category=cat_var.get(),
                amount=amount,
                date=date,
                description=desc_entry.get().strip()
            )
            dialog.destroy()
            self._load_expenses()

        tk.Button(dialog, text="Save Changes", command=on_submit).grid(
            row=4, column=0, columnspan=2, pady=16)


    # ── DELETE ────────────────────────────────────────────────────

    def _on_delete(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showinfo("No Selection", "Please click on an expense to select it first.")
            return

        values = self.tree.item(selected, "values")
        expense_id = values[0]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete expense #{expense_id}? This cannot be undone."
        )
        if confirm:
            delete_expense(int(expense_id))
            self._load_expenses()


    # ── SET BUDGET DIALOG ─────────────────────────────────────────

    def _open_budget_dialog(self):
        month = self.month_var.get().strip()
        current = get_budget(month)

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Set Budget — {month}")
        dialog.geometry("300x160")
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)

        tk.Label(dialog, text=f"Month: {month}").grid(row=0, column=0, columnspan=2, pady=12)
        tk.Label(dialog, text="Budget (₱)", anchor="w").grid(row=1, column=0, padx=16, sticky="w")

        amount_entry = tk.Entry(dialog)
        amount_entry.insert(0, str(current) if current else "")
        amount_entry.grid(row=1, column=1, padx=16, sticky="ew")

        def on_submit():
            try:
                amount = float(amount_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Budget must be a number.", parent=dialog)
                return

            set_budget(month, amount)
            dialog.destroy()
            self._update_budget_display()

        tk.Button(dialog, text="Set Budget", command=on_submit).grid(
            row=2, column=0, columnspan=2, pady=16)


    # ── CHARTS ────────────────────────────────────────────────────

    def _on_pie_chart(self):
        month = self.month_var.get().strip()
        totals = compute_totals_by_category(month)
        if not totals:
            messagebox.showinfo("No Data", f"No expenses found for {month}.")
            return
        generate_pie_chart(month)

    def _open_compare_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Months")
        dialog.geometry("300x160")
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)

        tk.Label(dialog, text="Month 1 (YYYY-MM)", anchor="w").grid(row=0, column=0, padx=16, pady=8, sticky="w")
        month1_entry = tk.Entry(dialog)
        month1_entry.insert(0, self.month_var.get())
        month1_entry.grid(row=0, column=1, padx=16, sticky="ew")

        tk.Label(dialog, text="Month 2 (YYYY-MM)", anchor="w").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        month2_entry = tk.Entry(dialog)
        month2_entry.grid(row=1, column=1, padx=16, sticky="ew")

        def on_submit():
            m1 = month1_entry.get().strip()
            m2 = month2_entry.get().strip()
            for m in [m1, m2]:
                try:
                    datetime.strptime(m, "%Y-%m")
                except ValueError:
                    messagebox.showerror("Invalid Format", f"{m} is not valid. Use YYYY-MM.", parent=dialog)
                    return
            dialog.destroy()
            compare_months(m1, m2)

        tk.Button(dialog, text="Compare", command=on_submit).grid(
            row=2, column=0, columnspan=2, pady=16)

    def _on_export(self):
         from logic import save_to_file
         month = self.month_var.get().strip()
         success = save_to_file(month)
         if success:
             messagebox.showinfo(
              "Export Successful",
              f"Summary saved as summary_{month}.txt\nin your project folder."
        )
         else:
             messagebox.showwarning("No Data", f"No expenses found for {month}.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()