import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PRODUCTION_DB = (ROOT / "task_manger.db").resolve()

# Must be set before `app` is imported. load_dotenv() will not override it.
os.environ["JWT_SECRET_KEY"] = "pytest-only-jwt-secret-not-for-production"
os.environ.setdefault("MAIL_USERNAME", "pytest-mailer@example.com")
os.environ.setdefault("MAIL_PASSWORD", "pytest-not-a-real-mail-password")

import database as database_module

# Fail closed: never let an accidental import initialize the real DB.
database_module.table = str((ROOT / "tests" / "_unused_bootstrap.db").resolve())


PASSWORD = "secret1a"
REGISTER_PAYLOAD = {
    "username": "alice",
    "email": "alice@example.com",
    "password": PASSWORD,
    "confirm_password": PASSWORD,
}


class EmailInbox:
    def __init__(self):
        self.messages = []

    def send(self, receiver_email, otp):
        self.messages.append({"email": receiver_email, "otp": otp})
        return True

    def last(self):
        assert self.messages, "expected an email to be sent"
        return self.messages[-1]

    def last_otp(self):
        return self.last()["otp"]

    def otps_for(self, email):
        return [m["otp"] for m in self.messages if m["email"] == email]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def query_db(db_path, sql, params=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute_db(db_path, sql, params=()):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def get_user_row(db_path, email):
    rows = query_db(db_path, "SELECT * FROM users WHERE email = ?", (email,))
    return rows[0] if rows else None


def get_latest_otp_row(db_path, user_id, purpose):
    rows = query_db(
        db_path,
        """
        SELECT * FROM otp_codes
        WHERE user_id = ? AND purpose = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, purpose),
    )
    return rows[0] if rows else None


@pytest.fixture(autouse=True)
def mock_email(monkeypatch):
    inbox = EmailInbox()
    monkeypatch.setattr("task_services.send_verification_email", inbox.send)
    monkeypatch.setattr("routes.email_service.send_verification_email", inbox.send)
    return inbox


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_path = str((tmp_path / "pytest_task_manager.db").resolve())
    assert Path(db_path).resolve() != PRODUCTION_DB
    assert Path(db_path).name != "task_manger.db"

    monkeypatch.setattr(database_module, "table", db_path)

    from extensions import block_list

    block_list.clear()

    from task_services import initialize_database

    initialize_database()

    import app as app_module

    flask_app = app_module.app
    flask_app.config["TESTING"] = True
    flask_app.config["TEST_DB"] = db_path
    yield flask_app
    block_list.clear()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_path(app):
    return app.config["TEST_DB"]


def register_user(client, username, email, password=PASSWORD):
    return client.post(
        "/api/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )


def verify_email(client, inbox, email):
    otp = inbox.otps_for(email)[-1]
    return client.post("/api/verify-email", json={"email": email, "otp": otp})


def login_user(client, email, password=PASSWORD):
    return client.post("/api/login", json={"email": email, "password": password})


def tokens_from_login(response):
    payload = response.get_json()
    token = payload["token"]
    return token["access_token"], token["refresh_token"], token["role"]


def register_verify_login(client, inbox, username, email, password=PASSWORD):
    register_user(client, username, email, password)
    verify_email(client, inbox, email)
    response = login_user(client, email, password)
    access, refresh, role = tokens_from_login(response)
    return {
        "email": email,
        "username": username,
        "password": password,
        "access_token": access,
        "refresh_token": refresh,
        "role": role,
        "headers": auth_header(access),
    }


@pytest.fixture
def user_a(client, mock_email):
    return register_verify_login(client, mock_email, "alice", "alice@example.com")


@pytest.fixture
def user_b(client, mock_email):
    return register_verify_login(client, mock_email, "bob", "bob@example.com")


@pytest.fixture
def admin_user(client, mock_email, db_path):
    register_user(client, "adminuser", "admin@example.com")
    verify_email(client, mock_email, "admin@example.com")
    user = get_user_row(db_path, "admin@example.com")
    from database import update_user_role

    update_user_role(user["id"], "admin")
    response = login_user(client, "admin@example.com")
    access, refresh, role = tokens_from_login(response)
    return {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": PASSWORD,
        "access_token": access,
        "refresh_token": refresh,
        "role": role,
        "id": user["id"],
        "headers": auth_header(access),
    }
