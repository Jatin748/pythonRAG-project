import csv
import os

filename = "expenses.csv"

def add_expense():
    date = input("Enter date: ")
    category = input("Enter category: ")
    description = input("Enter description: ")
    amount = float(input("Enter amount: "))

    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)

        # Add column names when creating the file
        if not file_exists:
            writer.writerow(["Date", "Category", "Description", "Amount"])

        writer.writerow([date, category, description, amount])

    print("Expense added successfully!")


def view_expenses():
    if not os.path.exists(filename):
        print("No expenses found.")
        return

    with open(filename, "r") as file:
        reader = csv.reader(file)

        for row in reader:
            print(row)


def total_expenses():
    total = 0

    if not os.path.exists(filename):
        print("No expenses found.")
        return

    with open(filename, "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            total += float(row["Amount"])

    print("Total Expenses:", total)


while True:
    print("\n--- Personal Expense Tracker ---")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Calculate Total")
    print("4. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        add_expense()

    elif choice == "2":
        view_expenses()

    elif choice == "3":
        total_expenses()

    elif choice == "4":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")
