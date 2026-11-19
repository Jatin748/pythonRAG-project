import json
import os

filename = "tasks.json"

def load_tasks():
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)

    return []

def save_tasks(tasks):
    with open(filename, "w") as file:
        json.dump(tasks, file, indent=4)

def add_task():
    tasks = load_tasks()

    task_name = input("Enter task name: ")

    task = {
        "task": task_name,
        "completed": False
    }

    tasks.append(task)
    save_tasks(tasks)

    print("Task added successfully!")

def view_tasks():
    tasks = load_tasks()

    if not tasks:
        print("No tasks found.")
        return

    for i, task in enumerate(tasks):
        status = "Completed" if task["completed"] else "Pending"

        print(i + 1, task["task"], "-", status)

def update_task():
    tasks = load_tasks()
    view_tasks()

    if not tasks:
        return

    choice = int(input("Enter task number to complete: "))

    if 1 <= choice <= len(tasks):
        tasks[choice - 1]["completed"] = True
        save_tasks(tasks)

        print("Task updated successfully!")

    else:
        print("Invalid task number")

def delete_task():
    tasks = load_tasks()
    view_tasks()

    if not tasks:
        return

    choice = int(input("Enter task number to delete: "))

    if 1 <= choice <= len(tasks):
        tasks.pop(choice - 1)
        save_tasks(tasks)

        print("Task deleted successfully!")

    else:
        print("Invalid task number")

while True:
    print("\n--- Task Management System ---")
    print("1. Add Task")
    print("2. View Tasks")
    print("3. Update Task")
    print("4. Delete Task")
    print("5. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        add_task()

    elif choice == "2":
        view_tasks()

    elif choice == "3":
        update_task()

    elif choice == "4":
        delete_task()

    elif choice == "5":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")
