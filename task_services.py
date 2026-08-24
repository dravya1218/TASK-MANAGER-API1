import math, secrets
from flask_jwt_extended import create_access_token, create_refresh_token
from database import *
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime, timedelta, timezone
from routes.email_service import send_verification_email


def login_user_service(data):
    email=data["email"]
    password=data["password"]

    user=get_user_by_email(email)
    if not user:
        return "invalid email or password",None
    if not check_password_hash(user["password_hash"],password):
        return "invalid email or password",None

    if not user["email_verified"]:
        return "Please verify your email before logging in", None
    
    user=dict(user)
    
    access_token=create_access_token(identity=str(user["id"]),additional_claims={"role":user["role"]},fresh=True)
    refresh_token=create_refresh_token(identity=str(user["id"]),additional_claims={"role":user["role"]})
    return None,{
        "access_token":access_token,
        "refresh_token":refresh_token,
        "role":user["role"]
    }

def refresh_access_token(user_id, role):
    access_token=create_access_token(
        identity=str(user_id),
        additional_claims={"role": role}
    )
    return {
        "access_token":access_token
    }

def get_all_tasks_service(user_id,page,limit,sort_by,order,search,status,priority):
    offset=(page - 1)*limit
    total_task=count_task(user_id,search,status,priority)
    if total_task==0:
        total_page=0
    else:    
        total_page=math.ceil(total_task/limit)
    rows=get_all_task(user_id,limit,offset,sort_by,order,search,status,priority)
    
    tasks=[]

    for row in rows:
        tasks.append(dict(row))
    return {
        "page":page,
        "limit":limit,
        "total task":total_task,
        "total page":total_page,
        "tasks":tasks
    }


def create_task_service(user_id, data):

    title = data["title"].strip()

    description = data.get("description", "").strip()

    status = data.get("status", "pending")

    priority = data.get("priority", "medium")

    due_date = data.get("due_date") or None

    category_id = data.get("category_id")

    success = insert_task(
        user_id,
        title,
        description,
        status,
        priority,
        due_date,
        category_id
    )

    if not success:
        return "cannot able to insert task", None

    return None, {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "category_id": category_id,
        "user_id": user_id
    }

def get_task_by_id_service(user_id,task_id):
    row=get_specific_task(task_id)
    if not row:
        return"task not found",None
    row=dict(row)
    if int(row["user_id"])!=int(user_id):
        return "forbidden",None
    return None,row

def update_task_service(user_id, task_id, data):

    error, task = get_task_by_id_service(user_id, task_id)

    if error:
        return error, None

    title = data["title"].strip()

    description = data.get("description", "").strip()

    status = data.get("status")

    priority = data.get("priority")

    due_date = data.get("due_date") or None

    category_id = data.get("category_id")

    success = update_task(
        task_id,
        title,
        description,
        status,
        priority,
        due_date,
        category_id
    )

    if not success:
        return "cannot able to update", None

    return get_task_by_id_service(user_id, task_id)


def delete_task_service(user_id,task_id):
    error, task = get_task_by_id_service(user_id,task_id)

    if error:
        return error, None
    
    success = delete_task(user_id, task_id)

    if not success:
        return "Task not found", None

    return None, {
        "message": "Task deleted successfully",
        "deleted_task": task
    }

def registration_user_service(data):

    username = data["username"].strip()
    email = data["email"]
    password = data["password"]

    role_name = "user"

    if get_user_by_username(username):

        return "username already exists", None

    if get_user_by_email(email):

        return "email already exists", None

    hash_password = generate_password_hash(password)

    role_id = find_role_id_by_name(role_name)

    if role_id is None:

        return "register unscueessfull", None

    user_id = insert_user(
        username,
        email,
        hash_password,
        role_id
    )

    if user_id is None:
        return "user cannot be registered", None

    otp = generate_otp()

    expires_at = datetime.now() + timedelta(minutes=10)

    success = insert_otp(
        user_id,
        otp,
        "email_verification",
        expires_at
    )

    if not success:
        return "unable to generate verification OTP", None

    try:
        send_verification_email(
            email,
            otp
        )

    except Exception as error:
        print("REGISTRATION EMAIL ERROR:", repr(error))
        return "unable to send verification email", None

    user = {
        "username": username,
        "email": email,
        "role": role_name,
        
    }

    return None, user


def verify_email_otp_service(user_id, otp):

    otp_record = get_latest_otp(
        user_id,
        "email_verification"
    )

    if not otp_record:
        return "No active OTP found"

    otp_id = otp_record["id"]
    stored_otp = otp_record["otp"]
    expires_at = otp_record["expires_at"]
    attempts = otp_record["attempts"]

    # Maximum attempts
    if attempts >= 5:
        return "Too many incorrect attempts. Please request a new OTP"

    # Check expiration
    
    try:
        expiry_time = datetime.fromisoformat(expires_at)

        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(tzinfo=timezone.utc)

    except (ValueError, TypeError):
        return "Invalid OTP expiration time"

    if datetime.now(timezone.utc) > expiry_time:
        return "OTP has expired"

    # Check OTP
    if otp != stored_otp:

        increment_otp_attempts(otp_id)

        return "Invalid OTP"

    # Verify email
    success = verify_user_email(user_id)

    if not success:
        return "Unable to verify email"

    # Prevent OTP reuse
    success = mark_otp_used(otp_id)

    if not success:
        return "Unable to complete OTP verification"

    return None


def verify_email_by_otp_service(email, otp):

    user = get_user_by_email(email)

    if not user:
        return "User not found"

    user_id = user["id"]

    # Already verified
    if user["email_verified"] == 1:
        return "Email is already verified"

    error = verify_email_otp_service(
        user_id,
        otp
    )

    if error:
        return error

    return None


def resend_email_verification_otp(email):

    user = get_user_by_email(email)

    if not user:
        return "User not found"

    user_id = user["id"]

    if user["email_verified"] == 1:
        return "Email is already verified"

    last_otp = get_latest_otp_time(
        user_id,
        "email_verification"
    )

    if last_otp:

        try:
            created_at = datetime.fromisoformat(
                last_otp["created_at"]
            )

            created_at = created_at.replace(tzinfo=timezone.utc)

        except (ValueError, TypeError):
            return "Invalid OTP creation time"

        now = datetime.now(timezone.utc)

        elapsed = now - created_at

        if elapsed.total_seconds() < 60:

            remaining = 60 - int(elapsed.total_seconds())

            return f"Please wait {remaining} seconds before requesting another OTP"

    success = invalidate_otp_codes(
        user_id,
        "email_verification"
    )

    if not success:
        return "Unable to invalidate previous OTP"

    otp = generate_otp()

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    success = insert_otp(
        user_id,
        otp,
        "email_verification",
        expires_at
    )

    if not success:
        return "Unable to generate new OTP"

    try:

        send_verification_email(
            email,
            otp
        )

    except Exception:

        return "Unable to send verification email"

    return None


def resend_email_change_otp(user_id):

    user = get_user_by_id(user_id)

    if not user:
        return "User not found"

    pending_email = user["pending_email"]

    if not pending_email:
        return "No pending email change"

    last_otp = get_latest_otp_time(
        user_id,
        "email_change"
    )

    if last_otp:

        try:
            created_at = datetime.fromisoformat(
                last_otp["created_at"]
            )

            if created_at.tzinfo is None:
                created_at = created_at.replace(
                    tzinfo=timezone.utc
                )

        except (ValueError, TypeError):

            return "Invalid OTP creation time"

        now = datetime.now(timezone.utc)

        elapsed = now - created_at

        if elapsed.total_seconds() < 60:

            remaining = 60 - int(
                elapsed.total_seconds()
            )

            return (
                f"Please wait {remaining} seconds "
                "before requesting another OTP"
            )

    # Invalidate previous email-change OTP
    success = invalidate_otp_codes(
        user_id,
        "email_change"
    )

    if not success:
        return "Unable to invalidate previous OTP"

    # Generate new OTP
    otp = generate_otp()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )

    success = insert_otp(
        user_id,
        otp,
        "email_change",
        expires_at
    )

    if not success:
        return "Unable to generate new OTP"

    # Send to pending email
    try:

        send_verification_email(
            pending_email,
            otp
        )

    except Exception as e:

        print(
            "EMAIL CHANGE RESEND ERROR:",
            repr(e)
        )

        return "Unable to send email change OTP"

    return None


def request_password_reset_otp(email):

    user = get_user_by_email(email)

    if not user:
        return "User not found"

    user_id = user["id"]

    last_otp = get_latest_otp_time(
        user_id,
        "password_reset"
    )

    if last_otp:

        try:
            created_at = datetime.fromisoformat(
                last_otp["created_at"]
            )

            if created_at.tzinfo is None:
                created_at = created_at.replace(
                    tzinfo=timezone.utc

                )

        except (ValueError, TypeError):
            return "Invalid OTP creation time"

        elapsed = datetime.now(timezone.utc) - created_at

        if elapsed.total_seconds() < 60:

            remaining = 60 - int(elapsed.total_seconds())

            return f"Please wait {remaining} seconds before requesting another OTP"

    # Generate OTP
    otp = generate_otp()

    # OTP valid for 10 minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Invalidate previous password-reset OTPs
    success = invalidate_otp_codes(
        user_id,
        "password_reset"
    )

    if not success:
        return "Unable to invalidate previous OTP"

    # Store new OTP
    success = insert_otp(
        user_id,
        otp,
        "password_reset",
        expires_at
    )

    if not success:
        return "Unable to generate password reset OTP"

    # Send OTP
    try:

        send_verification_email(
            email,
            otp
        )

    except Exception:

        return "Unable to send password reset email"

    return None


def verify_password_reset_otp_service(email, otp):
    user = get_user_by_email(email)
    if not user:
        return "User not found", None  # Changed here

    user_id = user["id"]
    otp_record = get_latest_otp(user_id, "password_reset")
    if not otp_record:
        return "No active password reset OTP found", None  # Changed here

    otp_id = otp_record["id"]
    stored_otp = otp_record["otp"]
    expires_at = otp_record["expires_at"]
    attempts = otp_record["attempts"]

    if attempts >= 5:
        return "Too many incorrect attempts. Please request a new OTP", None  # Changed here

    try:
        expiry_time = datetime.fromisoformat(expires_at)
        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return "Invalid OTP expiration time", None  # Changed here

    if datetime.now(timezone.utc) > expiry_time:
        return "OTP has expired", None  # Changed here

    if otp != stored_otp:
        increment_otp_attempts(otp_id)
        return "Invalid OTP", None  # Changed here

    success = mark_otp_used(otp_id)
    if not success:
        return "Unable to complete OTP verification", None  # Changed here

    reset_token = create_access_token(
        identity=str(user_id),
        additional_claims={"purpose": "password_reset"},
        expires_delta=timedelta(minutes=10)
    )

    return None, reset_token  # This one is already correct!

    
def reset_password_service(user_id, new_password):

    password_hash = generate_password_hash(new_password)

    success = update_user_password(
        user_id,
        password_hash
    )

    if not success:
        return "Unable to update password"

    return None


def change_password_service(user_id, current_password, new_password):

    user = get_user_by_id(user_id)

    if not user:
        return "User not found"

    if not check_password_hash(user["password_hash"], current_password):
        return "Current password is incorrect"

    password_hash = generate_password_hash(new_password)

    if not update_user_password(user_id, password_hash):
        return "Unable to update password"

    return None

def assign_permission_to_role(role_name,permission_name):
    role_id=find_role_id_by_name(role_name)
    if role_id is None:
        return "role_id cannot found"
    permission_id=find_permission_id_by_name(permission_name)
    if permission_id is None:
        return "permission id not found"
    success=insert_role_permission(role_id,permission_id)
    if not success:
        return "permission already assigned"
    return "permission assigned successfully" 

def remove_permission_from_role(role_name,permission_name):
    role_id=find_role_id_by_name(role_name)
    if role_id is None:
        return "role_id cannot found"
    permission_id=find_permission_id_by_name(permission_name)
    if permission_id is None:
        return "permission id not found"
    success=delete_role_permission(role_id,permission_id)
    if not success:
        return "permission was not assigned"
    return "permission removed successfully" 

    
def seed_role_permissions():
    assignments = [
        ("admin", "create_task"),
        ("admin", "view_task"),
        ("admin", "update_task"),
        ("admin", "delete_task"),
        ("admin", "view_all_users"),
        ("admin", "view_user_task_count"),
        ("admin", "update_user"),
        ("admin", "delete_user"),
        ("admin", "manage_roles"),

        ("user", "create_task"),
        ("user", "view_task"),
        ("user", "update_task"),
        ("user", "delete_task"),
    ]

    for role_name, permission_name in assignments:
        assign_permission_to_role(role_name, permission_name)

def get_all_users_service():
    rows= get_all_users()
    users=[]
    for row in rows:
        users.append(dict(row))
    return None,users

def delete_user_service(user_id):
    success=delete_users(user_id)
    if not success:
        return "user not found",None

    return None,{"message":"user deleted successfully"}

def get_roles_and_permissions_service():

    rows = get_roles_and_permissions()

    roles = []
    permissions = []

    for row in rows:

        if row["type"] == "role":
            roles.append({
                "id": row["id"],
                "name": row["name"]
            })

        else:
            permissions.append({
                "id": row["id"],
                "name": row["name"]
            })

    return None, {
        "roles": roles,
        "permissions": permissions
    }

def get_role_permissions_service(role_name):

    role_id = find_role_id_by_name(role_name)

    if role_id is None:
        return "Role not found", None

    permissions = get_role_permissions(role_id)

    result = []

    for permission in permissions:

        result.append({
            "id": permission["id"],
            "name": permission["name"]
        })

    return None, result
def get_profile_service(user_id):

    user = get_user_by_id(user_id)

    if not user:
        return "User not found", None

    return None, dict(user)

def update_profile_service(user_id, data):

    user = get_user_by_id(user_id)

    if not user:
        return "User not found", None

    if not isinstance(data, dict):
        return "JSON body is required", None

    username = data.get("username")
    new_email = data.get("email")
    username_changed = False
    email_changed = False

    # -------------------------
    # Username
    # -------------------------

    if username is not None:

        if not isinstance(username, str):
            return "Username must be a string", None

        username = username.strip()

        if not username:
            return "Username cannot be empty", None

        if username != user["username"]:
            username_changed = True

            existing_user = get_user_by_username(username)

            if existing_user and int(existing_user["id"]) != int(user_id):
                return "Username already exists", None

    # -------------------------
    # Email
    # -------------------------

    if new_email is not None:

        if not isinstance(new_email, str):
            return "Email must be a string", None

        new_email = new_email.strip().lower()

        if not new_email:
            return "Email cannot be empty", None

        if "@" not in new_email or "." not in new_email:
            return "Invalid email format", None

        if new_email != user["email"]:
            email_changed = True

            existing_user = get_user_by_email(new_email)

            if existing_user and int(existing_user["id"]) != int(user_id):
                return "Email already exists", None

    # -------------------------
    # Update username
    # -------------------------

    if username_changed:

        success = update_username(
            user_id,
            username
        )

        if not success:
            return "Unable to update username", None

    # -------------------------
    # Email change
    # -------------------------

    if email_changed:

        success = set_pending_email(
            user_id,
            new_email
        )

        if not success:
            return "Unable to request email change", None

        invalidate_otp_codes(
            user_id,
            "email_change"
        )

        otp = generate_otp()

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        success = insert_otp(
            user_id,
            otp,
            "email_change",
            expires_at
        )

        if not success:
            return "Unable to generate email change OTP", None

        try:

            send_verification_email(
                new_email,
                otp
            )

        except Exception as e:
            print("EMAIL CHANGE ERROR:", repr(e))
            return "Unable to send email change OTP", None

    # -------------------------
    # Get updated profile
    # -------------------------

    error, updated_user = get_profile_service(user_id)

    if error:
        return error, None

    message = "Profile updated successfully"

    if email_changed:
        message = "Profile updated. Verify the OTP sent to your new email."

    return None, {
        "user": updated_user,
        "email_verification_required": email_changed,
        "message": message
    }


def verify_email_change_otp_service(user_id, otp):

    otp_record = get_latest_otp(
        user_id,
        "email_change"
    )

    if not otp_record:
        return "No active OTP found"

    otp_id = otp_record["id"]
    stored_otp = otp_record["otp"]
    expires_at = otp_record["expires_at"]
    attempts = otp_record["attempts"]

    # -------------------------
    # Maximum attempts
    # -------------------------

    if attempts >= 5:
        return "Too many incorrect attempts. Please request a new OTP"

    # -------------------------
    # Check expiration
    # -------------------------

    try:

        expiry_time = datetime.fromisoformat(
            expires_at
        )

        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(
                tzinfo=timezone.utc
            )

    except (ValueError, TypeError):

        return "Invalid OTP expiration time"

    if datetime.now(timezone.utc) > expiry_time:

        return "OTP has expired"

    # -------------------------
    # Check OTP
    # -------------------------

    if otp != stored_otp:

        increment_otp_attempts(otp_id)

        return "Invalid OTP"

    # -------------------------
    # Complete email change
    # -------------------------

    success = complete_email_change(user_id)

    if not success:
        return "Unable to complete email change"

    # -------------------------
    # Prevent OTP reuse
    # -------------------------

    success = mark_otp_used(otp_id)

    if not success:
        return "Unable to complete OTP verification"

    return None


def update_user_role_service(user_id, role):

    success = update_user_role(user_id, role)

    if not success:
        return "User not found", None

    return None, {
        "message": "Role updated successfully"
    }


def update_role_permissions_service(role_name, permission_names):

    role_id = find_role_id_by_name(role_name)

    if role_id is None:
        return "Role not found.", None

    clear_permissions_for_role(role_id)

    for permission_name in permission_names:
        assign_permission_to_role(role_name, permission_name)

    return None, "Permissions updated successfully."


def get_categories_service(user_id):

    rows = get_all_categories(user_id)

    categories = []

    for row in rows:

        categories.append(dict(row))

    return None, categories


def create_category_service(user_id, data):

    name = data.get("name", "").strip()

    if not name:
        return "Category name is required.", None

    # Check if category already exists
    if category_exists(user_id, name):
        return "Category already exists.", None

    success = insert_category(user_id, name)

    if not success:
        return "Unable to create category.", None

    return None, {
        "message": "Category created successfully."
    }


def delete_category_service(user_id, category_id):

    if not category_id:
        return "Category ID is required.", None

    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        return "Category ID must be an integer.", None

    success = delete_category(
        user_id,
        category_id
    )

    if not success:
        return "Category not found.", None

    return None, {
        "message": "Category deleted successfully."
    }


def generate_otp():
    return str(secrets.randbelow(900000) + 100000)



def initialize_database():

    create_role_table()
    seed_role()

    create_user_table()

    create_permission_table()
    seed_permission()

    create_role_permissions()
    seed_role_permissions()

    create_category_table()

    create_task_table()

    create_otp_table()
