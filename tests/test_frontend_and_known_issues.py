from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from tests.conftest import auth_header, get_user_row


HTML_PAGES = [
    "/",
    "/login",
    "/register",
    "/dashboard",
    "/profile",
    "/manage-permissions",
    "/forgot_password",
]


@pytest.mark.parametrize("path", HTML_PAGES)
def test_frontend_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.mimetype == "text/html"


def test_frontend_pages_reject_post(client):
    assert client.post("/login").status_code == 405
    assert client.post("/register").status_code == 405


def test_profile_should_not_include_password_hash(client, user_a):
    body = client.get("/api/profile", headers=user_a["headers"]).get_json()
    assert "password_hash" not in body


def test_admin_cannot_delete_own_account(client, admin_user, db_path):
    response = client.delete(
        f"/api/users/{admin_user['id']}",
        headers=admin_user["headers"],
    )
    assert response.status_code == 400
    assert "cannot delete your own account" in response.get_json()["error"]
    assert get_user_row(db_path, "admin@example.com") is not None


def test_admin_cannot_change_own_role(client, admin_user):
    response = client.put(
        f"/api/users/{admin_user['id']}/role",
        headers=admin_user["headers"],
        json={"role": "user"},
    )
    assert response.status_code == 400
    assert "cannot change your own role" in response.get_json()["error"]


def test_password_reset_token_cannot_access_tasks(
    client, user_a, mock_email
):
    client.post("/api/forgot-password", json={"email": "alice@example.com"})
    verify = client.post(
        "/api/verify-password-reset",
        json={"email": "alice@example.com", "otp": mock_email.last_otp()},
    )
    reset_token = verify.get_json()["reset_token"]
    response = client.get("/api/tasks", headers=auth_header(reset_token))
    assert response.status_code == 403
    assert response.get_json()["error"] == "Invalid password reset token"


def test_password_reset_token_cannot_access_other_protected_routes(
    client, user_a, mock_email
):
    client.post("/api/forgot-password", json={"email": "alice@example.com"})
    verify = client.post(
        "/api/verify-password-reset",
        json={"email": "alice@example.com", "otp": mock_email.last_otp()},
    )
    headers = auth_header(verify.get_json()["reset_token"])

    profile = client.get("/api/profile", headers=headers)
    assert profile.status_code == 403
    assert profile.get_json()["error"] == "Invalid password reset token"

    change_password = client.post(
        "/api/change-password",
        headers=headers,
        json={
            "current_password": "secret1a",
            "new_password": "newpass1",
            "confirm_password": "newpass1",
        },
    )
    assert change_password.status_code == 403

    users = client.get("/api/users", headers=headers)
    assert users.status_code == 403

    categories = client.get("/api/categories", headers=headers)
    assert categories.status_code == 403


def test_expired_access_token_is_rejected(client, user_a, app, db_path):
    user = get_user_row(db_path, "alice@example.com")
    with app.app_context():
        token = create_access_token(
            identity=str(user["id"]),
            additional_claims={"role": "user"},
            expires_delta=timedelta(seconds=-2),
        )
    response = client.get("/api/profile", headers=auth_header(token))
    assert response.status_code == 401


def test_expired_password_reset_token_is_rejected(
    client, user_a, app, db_path
):
    user = get_user_row(db_path, "alice@example.com")
    with app.app_context():
        token = create_access_token(
            identity=str(user["id"]),
            additional_claims={"purpose": "password_reset"},
            expires_delta=timedelta(seconds=-2),
        )
    response = client.post(
        "/api/reset-password",
        headers=auth_header(token),
        json={"new_password": "resetpw1", "confirm_password": "resetpw1"},
    )
    assert response.status_code == 401


def test_admin_user_list_does_not_leak_password_hash(client, admin_user):
    response = client.get("/api/users", headers=admin_user["headers"])
    assert response.status_code == 200
    for user in response.get_json():
        assert "password_hash" not in user
        assert "password" not in user
