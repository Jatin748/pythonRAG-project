
# Import FastAPI to create our API application.
# HTTPException is used to return HTTP errors such as 404.
# Depends is used for dependency injection.
from fastapi import FastAPI, HTTPException, Depends

# Middleware that allows our frontend to communicate with the backend.
from fastapi.middleware.cors import CORSMiddleware

# BaseModel is used to create data models.
# Field adds validation rules to model fields.
# field_validator allows us to write custom validation logic.
from pydantic import BaseModel, Field, field_validator

# sqlite3 allows Python to interact with an SQLite database.
import sqlite3

# time is used to calculate how long an API request takes.
import time


# Create the FastAPI application instance.
app = FastAPI()


# --------------------------------------------------
# CORS MIDDLEWARE
# --------------------------------------------------

# CORS allows specified frontend applications to communicate
# with our backend through a browser.
app.add_middleware(
    CORSMiddleware,

    # Only these frontend origins are allowed.
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],

    # Allows credentials such as cookies to be included.
    allow_credentials=True,

    # Allows all HTTP methods: GET, POST, PUT, PATCH, DELETE, etc.
    allow_methods=["*"],

    # Allows all request headers.
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST LOGGING MIDDLEWARE
# --------------------------------------------------

# Middleware runs before and after an HTTP request reaches
# and returns from its endpoint.
@app.middleware("http")
async def log_requests(request, call_next):

    # Record the time when the request arrives.
    start_time = time.time()

    # Print the HTTP method and requested URL path.
    # Example: Request: GET /tasks
    print(f"Request: {request.method} {request.url.path}")

    # Forward the request to the next part of the application.
    # This waits until the endpoint produces a response.
    response = await call_next(request)

    # Calculate how much time the request took.
    process_time = time.time() - start_time

    # Print the HTTP response status code.
    print(f"Response status: {response.status_code}")

    # Print processing time up to four decimal places.
    print(f"Processing time: {process_time:.4f} seconds")

    # Send the response back to the client.
    return response


# --------------------------------------------------
# DATABASE DEPENDENCY
# --------------------------------------------------

# This function provides a database connection to endpoints.
def get_db():

    # Open a connection to our SQLite database.
    connection = sqlite3.connect("tasks.db")

    try:
        # yield provides the connection to the endpoint.
        # FastAPI resumes this function after the request finishes.
        yield connection

    finally:
        # Close the database connection even if an error occurs.
        connection.close()


# --------------------------------------------------
# CREATE DATABASE TABLE
# --------------------------------------------------

def create_table():

    # Open a direct SQLite connection.
    # We use this here because table creation happens during startup,
    # not as part of an incoming API request.
    connection = sqlite3.connect("tasks.db")

    # Create the tasks table if it doesn't already exist.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL
        )
    """)

    # Save the database changes.
    connection.commit()

    # Close the connection.
    connection.close()


# Execute table creation when this module is loaded.
create_table()


# --------------------------------------------------
# PYDANTIC MODELS
# --------------------------------------------------

# Task represents the data required when creating
# a new task or performing a full update.
class Task(BaseModel):

    # Title must contain 1–100 characters.
    title: str = Field(min_length=1, max_length=100)

    # completed must be a boolean value.
    completed: bool

    # Custom validation for the title field.
    @field_validator("title")
    @classmethod
    def validate_title(cls, value):

        # Reject titles containing only spaces.
        if not value.strip():
            raise ValueError("Title cannot contain only spaces")

        # Remove unnecessary spaces from the beginning and end.
        return value.strip()


# TaskUpdate is used for PATCH requests.
# Unlike Task, its fields are optional because PATCH
# allows the user to update only selected fields.
class TaskUpdate(BaseModel):

    # Title can be omitted, but if supplied it must be valid.
    title: str | None = Field(default=None, min_length=1, max_length=100)

    # completed can also be omitted.
    completed: bool | None = None

    # Validate the title only when it is supplied.
    @field_validator("title")
    @classmethod
    def validate_title(cls, value):

        # Explicitly reject null titles.
        if value is None:
            raise ValueError("Title cannot be null")

        # Reject titles containing only spaces.
        if not value.strip():
            raise ValueError("Title cannot contain only spaces")

        return value.strip()


# TaskResponse defines the structure of data
# that our API is allowed to return.
class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool


# --------------------------------------------------
# HOME ENDPOINT
# --------------------------------------------------

# GET request to the root URL.
@app.get("/")
def home():

    # Return a welcome message.
    return {"message": "Welcome to Task Manager API"}


# --------------------------------------------------
# GET ALL TASKS
# --------------------------------------------------

# response_model validates and structures the API response.
# list[TaskResponse] means the endpoint returns a list of tasks.
@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(connection=Depends(get_db)):

    # Create a cursor to execute SQL queries.
    cursor = connection.cursor()

    # Retrieve every row from the tasks table.
    cursor.execute("SELECT * FROM tasks")

    # fetchall() returns all matching database rows.
    tasks = cursor.fetchall()

    # Convert each database row into a dictionary.
    # SQLite returns rows as tuples by default:
    # task[0] = id, task[1] = title, task[2] = completed.
    return [
        {
            "id": task[0],
            "title": task[1],
            "completed": bool(task[2])
        }
        for task in tasks
    ]


# --------------------------------------------------
# FILTER TASKS
# --------------------------------------------------

# Filter tasks based on their completed status.
# Example: GET /tasks/filter?completed=true
@app.get("/tasks/filter", response_model=list[TaskResponse])
def filter_tasks(completed: bool, connection=Depends(get_db)):

    cursor = connection.cursor()

    # ? is a placeholder for the value supplied by the user.
    # This helps prevent SQL injection.
    cursor.execute(
        "SELECT * FROM tasks WHERE completed = ?",
        (completed,)
    )

    # Retrieve all tasks matching the condition.
    tasks = cursor.fetchall()

    # Convert database rows into dictionaries.
    return [
        {
            "id": task[0],
            "title": task[1],
            "completed": bool(task[2])
        }
        for task in tasks
    ]


# --------------------------------------------------
# GET TASK BY ID
# --------------------------------------------------

# The task_id is taken from the URL path.
# Example: GET /tasks/1
@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, connection=Depends(get_db)):

    cursor = connection.cursor()

    # Retrieve the task matching the supplied ID.
    # (task_id,) is a single-item tuple.
    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    # fetchone() retrieves one matching row.
    task = cursor.fetchone()

    # If no matching task exists, return HTTP 404.
    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Return the task as a dictionary.
    return {
        "id": task[0],
        "title": task[1],
        "completed": bool(task[2])
    }


# --------------------------------------------------
# CREATE TASK
# --------------------------------------------------

# POST creates a new task.
# HTTP 201 means the resource was successfully created.
@app.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(task: Task, connection=Depends(get_db)):

    cursor = connection.cursor()

    # Insert the incoming task data into the database.
    # The ID is generated automatically by SQLite.
    cursor.execute(
        "INSERT INTO tasks (title, completed) VALUES (?, ?)",
        (task.title, task.completed)
    )

    # Save the inserted task.
    connection.commit()

    # lastrowid gives us the ID generated for the new task.
    new_id = cursor.lastrowid

    # Return the newly created task.
    return {
        "id": new_id,
        "title": task.title,
        "completed": task.completed
    }


# --------------------------------------------------
# FULL UPDATE
# --------------------------------------------------

# PUT replaces the task's supplied fields with new values.
# Both title and completed are required by the Task model.
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    updated_task: Task,
    connection=Depends(get_db)
):

    cursor = connection.cursor()

    # Update both title and completed for the matching ID.
    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, completed = ?
        WHERE id = ?
        """,
        (updated_task.title, updated_task.completed, task_id)
    )

    # Save the update.
    connection.commit()

    # rowcount tells us how many rows were affected.
    # If no row was updated, the task ID doesn't exist.
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Retrieve the updated task so we can return it.
    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    task = cursor.fetchone()

    return {
        "id": task[0],
        "title": task[1],
        "completed": bool(task[2])
    }


# --------------------------------------------------
# PARTIAL UPDATE
# --------------------------------------------------

# PATCH updates only the fields supplied by the user.
@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def partial_update_task(
    task_id: int,
    updated_task: TaskUpdate,
    connection=Depends(get_db)
):

    # Convert the Pydantic model into a dictionary.
    # exclude_unset=True includes only fields actually supplied.
    update_data = updated_task.model_dump(exclude_unset=True)

    # Reject a PATCH request containing no fields.
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # These lists will help us build a dynamic SQL query.
    updates = []
    values = []

    # Loop through the fields supplied by the user.
    for key, value in update_data.items():

        # Create an SQL assignment for each supplied field.
        # Example: title = ? or completed = ?
        updates.append(f"{key} = ?")

        # Store the corresponding value separately.
        values.append(value)

    # Add the task ID as the final query parameter.
    values.append(task_id)

    # Build an SQL query containing only the supplied fields.
    # Example: UPDATE tasks SET completed = ? WHERE id = ?
    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"

    cursor = connection.cursor()

    # Execute the dynamically generated query.
    # User-provided values are still passed separately.
    cursor.execute(query, values)

    # Save the changes.
    connection.commit()

    # If no task was updated, return 404.
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Retrieve the updated task.
    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    task = cursor.fetchone()

    return {
        "id": task[0],
        "title": task[1],
        "completed": bool(task[2])
    }


# --------------------------------------------------
# DELETE TASK
# --------------------------------------------------

# DELETE removes a task using its ID.
# HTTP 204 means successful deletion with no response body.
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, connection=Depends(get_db)):

    cursor = connection.cursor()

    # Delete the row matching the supplied ID.
    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    # Save the deletion.
    connection.commit()

    # If no row was deleted, the task doesn't exist.
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # No response body is returned because the status is 204.
    return