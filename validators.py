from datetime import datetime
import os
from datetime import datetime

def validate_task_data(data):

    if data is None:
        return "JSON body is required"

    if not isinstance(data, dict):
        return "JSON body is required"

    if "title" not in data:
        return "Title is required"

    title = data["title"]

    if not isinstance(title, str):
        return "Title must be a string"

    if not title.strip():
        return "Title cannot be empty"

    if title.isdigit():
        return "Title cannot be all digits"

    # -------------------------
    # Description
    # -------------------------

    description = data.get("description", "")

    if not isinstance(description, str):
        return "Description must be a string"

    if len(description) > 1000:
        return "Description is too long"

    # -------------------------
    # Status
    # -------------------------

    status = data.get("status", "pending")

    if not isinstance(status, str):
        return "Status must be a string"

    if status.isdigit():
        return "Status cannot be all digits"

    if not status.strip():
        return "Status cannot be empty"

    if status not in ["pending", "completed"]:
        return "Status must be pending or completed"

    # -------------------------
    # Priority
    # -------------------------

    priority = data.get("priority", "medium")

    if not isinstance(priority, str):
        return "Priority must be a string"

    if not priority.strip():
        return "Priority cannot be empty"

    if priority.isdigit():
        return "Priority cannot be all digits"

    if priority not in ["low", "medium", "high"]:
        return "Priority must be low, medium or high"

    # -------------------------
    # Due Date
    # -------------------------

    due_date = data.get("due_date")

    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return "Invalid due date format"

    # -------------------------
    # Category
    # -------------------------

    category_id = data.get("category_id")

    if category_id is not None:

        if not isinstance(category_id, int):
            return "Category id must be an integer"

        if category_id < 1:
            return "Invalid category"

    return None


def validate_registration_data(data):

    if data is None:
        return "JSON body is required"

    if not isinstance(data, dict):
        return "JSON body must be an object"

    required_fields = [
        "username",
        "email",
        "password",
        "confirm_password"
    ]

    for field in required_fields:

        if field not in data:
            return f"{field} is required"

    username = data["username"]
    email = data["email"]
    password = data["password"]
    confirm_password = data["confirm_password"]

    if not all(
        isinstance(value, str)
        for value in [
            username,
            email,
            password,
            confirm_password
        ]
    ):
        return "All fields must be strings"

    if not username.strip():
        return "Username cannot be empty"

    if not email.strip():
        return "Email cannot be empty"

    if not password.strip():
        return "Password cannot be empty"

    if not confirm_password.strip():
        return "Confirm password cannot be empty"

    if username.isdigit():
        return "Username cannot contain only digits"

    if "@" not in email or "." not in email:
        return "Invalid email format"

    if password.isdigit():
        return "Password cannot contain only digits"

    if len(password) < 6:
        return "Password must be at least 6 characters"

    if password != confirm_password:
        return "Passwords do not match"

    return None


def validate_login_data(data):
    if data is None or not isinstance(data, dict):
        return "cannot be empty"
    reqiured_felid=["email","password"]
    for feild in reqiured_felid:
        if feild not in data:
            return f"{feild} is required"
        
    email=data["email"]
    password=data["password"]

    if not email.strip():
        return "email cannot be empty"
    if not password.strip():
        return "password cannot be empty"
    if "@" not in email or "." not in email:
        return "invaid email format"
    return None