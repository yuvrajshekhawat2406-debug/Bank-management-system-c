

import csv
import os
import random
import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

# ======================================================================
# 1. SETTINGS
# ======================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "expenses.csv")
CHART_DIR = os.path.join(BASE_DIR, "charts")

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Education",
    "Entertainment",
    "Health",
    "Other",
]
DATE_FORMAT = "%Y-%m-%d"
FIELDNAMES = ["id", "date", "title", "category", "amount", "note"]

LINE = "=" * 66
TABLE_HEAD = f"{'ID':<5}{'DATE':<12}{'TITLE':<26}{'CATEGORY':<15}{'AMOUNT':>10}"


# ======================================================================
# 2. MODELS  (Object-Oriented Programming)
# ======================================================================
class InvalidExpenseError(ValueError):
    """Raised when expense data entered by the user is not valid."""


class Transaction:
    """Base class: any money movement with an amount and a date."""

    def __init__(self, amount, txn_date=None):
        self.amount = amount
        self.date = txn_date

    # ---- encapsulation: validated properties -------------------------
    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        try:
            value = round(float(value), 2)
        except (TypeError, ValueError):
            raise InvalidExpenseError("Amount must be a number.")
        if value <= 0:
            raise InvalidExpenseError("Amount must be greater than zero.")
        self._amount = value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        if value is None or value == "":
            value = date.today()
        elif isinstance(value, datetime):
            value = value.date()
        elif isinstance(value, str):
            try:
                value = datetime.strptime(value.strip(), DATE_FORMAT).date()
            except ValueError:
                raise InvalidExpenseError("Date must be in YYYY-MM-DD format.")
        self._date = value


class Expense(Transaction):
    """A single expense entry (inherits from Transaction)."""

    def __init__(self, title, amount, category, txn_date=None, note="", expense_id=None):
        super().__init__(amount, txn_date)
        self.title = title
        self.category = category
        self.note = note.strip() if note else ""
        self.expense_id = expense_id

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        value = (value or "").strip()
        if not value:
            raise InvalidExpenseError("Title cannot be empty.")
        self._title = value

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        value = (value or "").strip().title()
        if value not in CATEGORIES:
            raise InvalidExpenseError("Category must be one of: " + ", ".join(CATEGORIES))
        self._category = value

    def to_dict(self):
        return {
            "id": self.expense_id,
            "date": self.date.strftime(DATE_FORMAT),
            "title": self.title,
            "category": self.category,
            "amount": f"{self.amount:.2f}",
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, row):
        return cls(
            title=row["title"],
            amount=row["amount"],
            category=row["category"],
            txn_date=row["date"],
            note=row.get("note") or "",
            expense_id=int(row["id"]),
        )

    def __str__(self):
        return (
            f"{self.expense_id:<5}{self.date.strftime(DATE_FORMAT):<12}"
            f"{self.title[:24]:<26}{self.category:<15}{self.amount:>10.2f}"
        )


# ======================================================================
# 3. STORAGE  (File handling with CSV)
# ======================================================================
class ExpenseStorage:
    """Stores expenses permanently in a CSV file."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.expenses = []
        self.skipped_rows = 0
        self._load()

    def _load(self):
        self.expenses = []
        self.skipped_rows = 0
        if not os.path.exists(self.filepath):
            self._save()  # create an empty file with headers
            return
        try:
            with open(self.filepath, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        self.expenses.append(Expense.from_dict(row))
                    except (InvalidExpenseError, KeyError, ValueError, TypeError):
                        self.skipped_rows += 1  # ignore corrupted rows
        except OSError as err:
            raise RuntimeError(f"Could not read {self.filepath}: {err}")

    def _save(self):
        folder = os.path.dirname(self.filepath)
        if folder:
            os.makedirs(folder, exist_ok=True)
        try:
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                for exp in self.expenses:
                    writer.writerow(exp.to_dict())
        except OSError as err:
            raise RuntimeError(f"Could not write {self.filepath}: {err}")

    def _next_id(self):
        return max((e.expense_id for e in self.expenses), default=0) + 1

    def add(self, expense):
        expense.expense_id = self._next_id()
        self.expenses.append(expense)
        self._save()
        return expense

    def delete(self, expense_id):
        for exp in self.expenses:
            if exp.expense_id == expense_id:
                self.expenses.remove(exp)
                self._save()
                return True
        return False

    def all(self):
        return sorted(self.expenses, key=lambda e: (e.date, e.expense_id))

    def by_category(self, category):
        category = category.strip().title()
        return [e for e in self.all() if e.category == category]

    def search(self, keyword):
        keyword = keyword.strip().lower()
        return [e for e in self.all() if keyword in e.title.lower() or keyword in e.note.lower()]


# ======================================================================
# 4. ANALYSIS  (NumPy, Pandas, Matplotlib)
# ======================================================================
def load_dataframe(filepath):
    """Read the expenses CSV into a clean Pandas DataFrame."""
    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df["month"] = df["date"].dt.strftime("%Y-%m")
    return df.sort_values("date").reset_index(drop=True)


def summary_stats(df):
    """Return key statistics as a dictionary (uses NumPy)."""
    if df.empty:
        return {}
    amounts = df["amount"].to_numpy()
    top = df.loc[df["amount"].idxmax()]
    return {
        "transactions": int(len(df)),
        "total": float(np.sum(amounts)),
        "average": float(np.mean(amounts)),
        "median": float(np.median(amounts)),
        "highest": float(np.max(amounts)),
        "highest_title": str(top["title"]),
        "std_dev": float(np.std(amounts)),
        "first_date": df["date"].min().strftime("%Y-%m-%d"),
        "last_date": df["date"].max().strftime("%Y-%m-%d"),
    }


def category_totals(df):
    return df.groupby("category")["amount"].sum().sort_values(ascending=False)


def monthly_totals(df):
    return df.groupby("month")["amount"].sum().sort_index()


def save_charts(df, out_dir, show=False):
    """Create and save the charts. Returns the list of saved file paths."""
    import matplotlib

    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(out_dir, exist_ok=True)
    saved = []

    cats = category_totals(df)
    months = monthly_totals(df)

    # ---- Chart 1: dashboard with three charts in one picture ----------
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.8))
    fig.suptitle("Smart Expense Tracker - Spending Analysis", fontsize=15, fontweight="bold")

    colors = plt.cm.Set3(np.linspace(0, 1, len(cats)))
    wedges, _, _ = axes[0].pie(
        cats.values,
        autopct=lambda p: f"{p:.1f}%" if p >= 6 else "",
        startangle=90,
        colors=colors,
        pctdistance=0.75,
    )
    axes[0].legend(wedges, cats.index, loc="upper center", bbox_to_anchor=(0.5, 0.02),
                   ncol=2, fontsize=8, frameon=False)
    axes[0].set_title("Spending by Category")

    bars = axes[1].bar(cats.index, cats.values, color=colors, edgecolor="black")
    axes[1].set_title("Total Amount per Category")
    axes[1].set_ylabel("Amount (Rs.)")
    axes[1].tick_params(axis="x", rotation=45)
    for bar in bars:
        axes[1].annotate(f"{bar.get_height():,.0f}",
                         (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                         ha="center", va="bottom", fontsize=8)

    axes[2].plot(months.index, months.values, marker="o", linewidth=2, color="#1f77b4")
    axes[2].set_title("Monthly Spending Trend")
    axes[2].set_ylabel("Amount (Rs.)")
    axes[2].set_ylim(0, months.max() * 1.15)
    axes[2].grid(True, linestyle="--", alpha=0.5)
    for x, y in zip(months.index, months.values):
        axes[2].annotate(f"{y:,.0f}", (x, y), textcoords="offset points",
                         xytext=(0, 8), ha="center")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(out_dir, "spending_dashboard.png")
    fig.savefig(path, dpi=130)
    saved.append(path)

    # ---- Chart 2: daily spending bars with running average ------------
    daily = df.groupby("date")["amount"].sum()
    running_avg = np.cumsum(daily.values) / np.arange(1, len(daily) + 1)
    fig2, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(daily.index, daily.values, color="#ff7f0e", label="Daily spending")
    ax.plot(daily.index, running_avg, color="black", linewidth=2, label="Running average per day")
    ax.set_title("Daily Spending and Running Average")
    ax.set_ylabel("Amount (Rs.)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)
    fig2.autofmt_xdate()
    fig2.tight_layout()
    path2 = os.path.join(out_dir, "daily_spending.png")
    fig2.savefig(path2, dpi=130)
    saved.append(path2)

    if show:
        plt.show()
    plt.close("all")
    return saved


# ======================================================================
# 5. SAMPLE DATA  (so the project works even with an empty file)
# ======================================================================
SAMPLE_ITEMS = {
    "Food": [("Canteen lunch", 60, 140), ("Groceries", 250, 900),
             ("Tea and snacks", 30, 90), ("Dinner with friends", 300, 700)],
    "Travel": [("Metro recharge", 200, 500), ("Auto fare", 40, 150),
               ("Cab to station", 180, 450), ("Bus ticket", 30, 120)],
    "Shopping": [("T-shirt", 399, 899), ("Headphones", 699, 1499), ("Backpack", 799, 1699)],
    "Bills": [("Mobile recharge", 199, 399), ("Wi-Fi bill", 499, 799),
              ("Electricity share", 300, 650)],
    "Education": [("Python course notes", 150, 400), ("Online course fee", 499, 1999),
                  ("Stationery", 50, 250)],
    "Entertainment": [("Movie ticket", 180, 420), ("OTT subscription", 149, 299),
                      ("Gaming top-up", 99, 499)],
    "Health": [("Medicines", 80, 350), ("Doctor consultation", 300, 600)],
    "Other": [("Gift", 200, 800), ("Printing", 20, 120)],
}
# some categories appear more often than others, like real life
SAMPLE_WEIGHTS = (["Food"] * 9 + ["Travel"] * 6 + ["Bills"] * 3 + ["Education"] * 3
                  + ["Entertainment"] * 3 + ["Shopping"] * 2 + ["Health"] + ["Other"] * 2)


def load_sample_data(storage):
    """Add about 70 sample expenses between 01/07/2026 and 03/09/2026."""
    rng = random.Random(2026)  # fixed seed -> same data every time
    day, last_day = date(2026, 7, 1), date(2026, 9, 3)
    added = 0
    while day <= last_day:
        for _ in range(rng.choice([0, 1, 1, 2])):
            category = rng.choice(SAMPLE_WEIGHTS)
            title, low, high = rng.choice(SAMPLE_ITEMS[category])
            storage.add(Expense(title, rng.randint(low, high), category, day))
            added += 1
        day += timedelta(days=1)
    return added


# ======================================================================
# 6. USER INTERFACE  (console menu)
# ======================================================================
def banner():
    print(LINE)
    print("           SMART EXPENSE TRACKER  |  Python Developer Intern")
    print(LINE)


def show_menu():
    print("\n  MAIN MENU")
    print("  " + "-" * 40)
    print("  1. Add a new expense")
    print("  2. View all expenses")
    print("  3. View expenses by category")
    print("  4. Search expenses")
    print("  5. Delete an expense")
    print("  6. Summary report")
    print("  7. Generate charts")
    print("  8. Load sample data")
    print("  0. Exit")
    print("  " + "-" * 40)


def print_table(expenses):
    if not expenses:
        print("\n  No expenses found.")
        return
    print("\n" + TABLE_HEAD)
    print("-" * 68)
    for exp in expenses:
        print(exp)
    print("-" * 68)
    total = sum(e.amount for e in expenses)
    label = f"Total ({len(expenses)} record{'' if len(expenses) == 1 else 's'})"
    print(f"{label:<58}{total:>10.2f}")


def ask(prompt):
    return input(prompt).strip()


def add_expense(storage):
    print("\n  --- Add New Expense ---")
    print("  Categories:", ", ".join(CATEGORIES))
    while True:
        try:
            expense = Expense(
                title=ask("  Title            : "),
                amount=ask("  Amount (Rs.)     : "),
                category=ask("  Category         : "),
                txn_date=ask("  Date (YYYY-MM-DD, blank = today): "),
                note=ask("  Note (optional)  : "),
            )
            saved = storage.add(expense)
            print(f"\n  [OK] Expense saved with ID {saved.expense_id}.")
            return
        except InvalidExpenseError as err:
            print(f"\n  [Error] {err}")
            if ask("  Try again? (y/n): ").lower() != "y":
                return


def view_all(storage):
    print_table(storage.all())


def view_by_category(storage):
    print("  Categories:", ", ".join(CATEGORIES))
    category = ask("  Enter category: ")
    if category.title() not in CATEGORIES:
        print("  [Error] Unknown category.")
        return
    print_table(storage.by_category(category))


def search(storage):
    keyword = ask("  Enter keyword to search: ")
    if not keyword:
        print("  [Error] Keyword cannot be empty.")
        return
    print_table(storage.search(keyword))


def delete_expense(storage):
    try:
        expense_id = int(ask("  Enter the ID of the expense to delete: "))
    except ValueError:
        print("  [Error] ID must be a whole number.")
        return
    if storage.delete(expense_id):
        print(f"  [OK] Expense {expense_id} deleted.")
    else:
        print(f"  [Error] No expense found with ID {expense_id}.")


def summary_report(storage):
    df = load_dataframe(storage.filepath)
    stats = summary_stats(df)
    if not stats:
        print("\n  No data available for a report. Add expenses or choose option 8.")
        return
    print("\n" + LINE)
    print("                     EXPENSE SUMMARY REPORT")
    print(LINE)
    print(f"  Period              : {stats['first_date']}  to  {stats['last_date']}")
    print(f"  Total transactions  : {stats['transactions']}")
    print(f"  Total spent         : Rs. {stats['total']:,.2f}")
    print(f"  Average per expense : Rs. {stats['average']:,.2f}")
    print(f"  Median expense      : Rs. {stats['median']:,.2f}")
    print(f"  Highest expense     : Rs. {stats['highest']:,.2f}  ({stats['highest_title']})")
    print(f"  Standard deviation  : Rs. {stats['std_dev']:,.2f}")

    print("\n  Spending by category")
    print("  " + "-" * 50)
    for name, value in category_totals(df).items():
        share = value / stats["total"] * 100
        bar = "#" * int(share / 2)
        print(f"  {name:<14}{value:>10,.2f}  {share:5.1f}%  {bar}")

    print("\n  Monthly spending")
    print("  " + "-" * 50)
    for month, value in monthly_totals(df).items():
        print(f"  {month:<14}{value:>10,.2f}")
    print(LINE)


def make_charts(storage):
    df = load_dataframe(storage.filepath)
    if df.empty:
        print("\n  No data available for charts. Add expenses or choose option 8.")
        return
    show = ask("  Open the charts in a window as well? (y/n): ").lower() == "y"
    files = save_charts(df, CHART_DIR, show=show)
    print("\n  [OK] Charts saved:")
    for f in files:
        print("   -", os.path.relpath(f, BASE_DIR))


def sample_data(storage):
    if storage.expenses:
        answer = ask(f"  {len(storage.expenses)} records already exist. Add sample data too? (y/n): ")
        if answer.lower() != "y":
            return
    count = load_sample_data(storage)
    print(f"  [OK] {count} sample expenses added.")


def main():
    try:
        storage = ExpenseStorage(DATA_FILE)
    except RuntimeError as err:
        print("Fatal error:", err)
        sys.exit(1)

    banner()
    print(f"  Loaded {len(storage.expenses)} expense records from data/expenses.csv")
    if storage.skipped_rows:
        print(f"  (Skipped {storage.skipped_rows} invalid rows)")

    actions = {
        "1": add_expense,
        "2": view_all,
        "3": view_by_category,
        "4": search,
        "5": delete_expense,
        "6": summary_report,
        "7": make_charts,
        "8": sample_data,
    }

    while True:
        show_menu()
        try:
            choice = ask("  Enter your choice (0-8): ")
        except (EOFError, KeyboardInterrupt):
            choice = "0"
        if choice == "0":
            print("\n  Thank you for using Smart Expense Tracker. Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("  [Error] Invalid choice. Please enter a number from 0 to 8.")
            continue
        try:
            action(storage)
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.")
        except RuntimeError as err:
            print(f"  [File error] {err}")


if __name__ == "__main__":
    main()
