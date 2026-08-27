import pytest

from tests.conftest import (
    PASSWORD,
    REGISTER_PAYLOAD,
    auth_header,
    execute_db,
    get_latest_otp_row,
    get_user_row,
    login_user,
    query_db,
    register_user,
    verify_email,
)


class TestRegister:
    def test_register_success_creates_unverified_user_and_otp(
        self, client, mock_email, db_path
    ):
        response = client.post("/api/register", json=REGISTER_PAYLOAD)
        assert response.status_code == 201
        body = response.get_json()
        assert body["message"] == "User registered successfully"
        assert body["user"] == {
            "username": "alice",
            "email": "alice@example.com",
            "role": "user",
        }

        user = get_user_row(db_path, "alice@example.com")
        assert user is not None
        assert user["email_verified"] == 0
        assert user["password_hash"] != PASSWORD
        assert len(user["password_hash"]) > 20

        otp_row = get_latest_otp_row(db_path, user["id"], "email_verification")
        assert otp_row is not None
        assert otp_row["used"] == 0
        assert otp_row["otp"] == mock_email.last_otp()
        assert mock_email.last()["email"] == "alice@example.com"
        assert mock_email.last_otp().isdigit()
        assert len(mock_email.last_otp()) == 6

    @pytest.mark.parametrize(
        "payload,substring",
        [
            ({}, "username is required"),
            (
                {
                    "email": "alice@example.com",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "username is required",
            ),
            (
                {
                    "username": "alice",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "email is required",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "confirm_password": PASSWORD,
                },
                "password is required",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": PASSWORD,
                },
                "confirm_password is required",
            ),
            (
                {
                    "username": "   ",
                    "email": "alice@example.com",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "Username cannot be empty",
            ),
            (
                {
                    "username": "alice",
                    "email": "   ",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "Email cannot be empty",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "   ",
                    "confirm_password": "   ",
                },
                "Password cannot be empty",
            ),
            (
                {
                    "username": "12345",
                    "email": "alice@example.com",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "Username cannot contain only digits",
            ),
            (
                {
                    "username": "alice",
                    "email": "not-an-email",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "Invalid email format",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "123456",
                    "confirm_password": "123456",
                },
                "Password cannot contain only digits",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "ab12",
                    "confirm_password": "ab12",
                },
                "Password must be at least 6 characters",
            ),
            (
                {
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": PASSWORD,
                    "confirm_password": "other12",
                },
                "Passwords do not match",
            ),
            (
                {
                    "username": 1,
                    "email": "alice@example.com",
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                },
                "All fields must be strings",
            ),
        ],
    )
    def test_register_validation_errors(self, client, payload, substring):
        response = client.post("/api/register", json=payload)
        assert response.status_code == 400
        body = response.get_json()
        assert "error" in body
        assert substring in body["error"]

    def test_register_missing_json_body(self, client):
        response = client.post(
            "/api/register",
            data="null",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "JSON body is required"

    def test_register_malformed_json(self, client):
        response = client.post(
            "/api/register",
            data="{not-json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "JSON body is required"

    def test_duplicate_username(self, client, mock_email):
        assert register_user(client, "alice", "alice@example.com").status_code == 201
        response = register_user(client, "alice", "alice2@example.com")
        assert response.status_code == 409
        assert response.get_json()["error"] == "username already exists"

    def test_duplicate_email(self, client, mock_email):
        assert register_user(client, "alice", "alice@example.com").status_code == 201
        response = register_user(client, "alice2", "alice@example.com")
        assert response.status_code == 409
        assert response.get_json()["error"] == "email already exists"

    def test_register_rejects_get(self, client):
        assert client.get("/api/register").status_code == 405


class TestEmailVerification:
    def test_verify_email_success(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        response = verify_email(client, mock_email, "alice@example.com")
        assert response.status_code == 200
        assert response.get_json()["message"] == "Email verified successfully"
        user = get_user_row(db_path, "alice@example.com")
        assert user["email_verified"] == 1
        otp = get_latest_otp_row(db_path, user["id"], "email_verification")
        assert otp["used"] == 1

    def test_verify_email_missing_body_and_fields(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        response = client.post(
            "/api/verify-email",
            data="null",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "JSON body is required"

        response = client.post("/api/verify-email", json={"otp": "123456"})
        assert response.status_code == 400
        assert response.get_json()["error"] == "Email is required"

        response = client.post(
            "/api/verify-email", json={"email": "alice@example.com"}
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "OTP is required"

        response = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": 123456},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "OTP must be a string"

        response = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": "12"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "OTP must be a 6-digit number"

    def test_verify_email_unknown_user(self, client):
        response = client.post(
            "/api/verify-email",
            json={"email": "missing@example.com", "otp": "123456"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "User not found"

    def test_invalid_otp_increments_attempts(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        response = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": "000000"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Invalid OTP"
        user = get_user_row(db_path, "alice@example.com")
        otp = get_latest_otp_row(db_path, user["id"], "email_verification")
        assert otp["attempts"] == 1
        assert user["email_verified"] == 0

    def test_too_many_otp_attempts(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        user = get_user_row(db_path, "alice@example.com")
        execute_db(
            db_path,
            "UPDATE otp_codes SET attempts = 5 WHERE user_id = ?",
            (user["id"],),
        )
        response = client.post(
            "/api/verify-email",
            json={
                "email": "alice@example.com",
                "otp": mock_email.last_otp(),
            },
        )
        assert response.status_code == 400
        assert "Too many incorrect attempts" in response.get_json()["error"]

    def test_expired_otp_fails(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        user = get_user_row(db_path, "alice@example.com")
        execute_db(
            db_path,
            "UPDATE otp_codes SET expires_at = ? WHERE user_id = ?",
            ("2000-01-01T00:00:00+00:00", user["id"]),
        )
        response = client.post(
            "/api/verify-email",
            json={
                "email": "alice@example.com",
                "otp": mock_email.last_otp(),
            },
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "OTP has expired"

    def test_otp_cannot_be_reused(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        otp = mock_email.last_otp()
        first = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": otp},
        )
        assert first.status_code == 200
        second = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": otp},
        )
        assert second.status_code == 400
        assert second.get_json()["error"] == "Email is already verified"

        execute_db(
            db_path,
            "UPDATE users SET email_verified = 0 WHERE email = ?",
            ("alice@example.com",),
        )
        third = client.post(
            "/api/verify-email",
            json={"email": "alice@example.com", "otp": otp},
        )
        assert third.status_code == 400
        assert third.get_json()["error"] == "No active OTP found"

    def test_resend_verification_success(self, client, mock_email, db_path):
        register_user(client, "alice", "alice@example.com")
        user = get_user_row(db_path, "alice@example.com")
        first_otp_id = get_latest_otp_row(
            db_path, user["id"], "email_verification"
        )["id"]
        execute_db(
            db_path,
            "UPDATE otp_codes SET created_at = ? WHERE user_id = ?",
            ("2000-01-01 00:00:00", user["id"]),
        )
        response = client.post(
            "/api/resend-verification",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "A new verification OTP has been sent"
        old = query_db(
            db_path, "SELECT used FROM otp_codes WHERE id = ?", (first_otp_id,)
        )
        assert old[0]["used"] == 1
        assert mock_email.last()["email"] == "alice@example.com"
        new_otp = get_latest_otp_row(db_path, user["id"], "email_verification")
        assert new_otp["used"] == 0
        assert new_otp["otp"] == mock_email.last_otp()

    def test_resend_verification_cooldown(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        response = client.post(
            "/api/resend-verification",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 400
        assert "Please wait" in response.get_json()["error"]

    def test_resend_verification_validation(self, client, mock_email):
        response = client.post(
            "/api/resend-verification",
            data="null",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "JSON body is required"

        response = client.post("/api/resend-verification", json={})
        assert response.status_code == 400
        assert response.get_json()["error"] == "Email is required"

        response = client.post(
            "/api/resend-verification",
            json={"email": "missing@example.com"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "User not found"

        register_user(client, "alice", "alice@example.com")
        verify_email(client, mock_email, "alice@example.com")
        response = client.post(
            "/api/resend-verification",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Email is already verified"

    def test_verify_and_resend_reject_wrong_methods(self, client):
        assert client.get("/api/verify-email").status_code == 405
        assert client.get("/api/resend-verification").status_code == 405


class TestLoginLogoutRefresh:
    def test_login_blocked_until_email_verified(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        response = login_user(client, "alice@example.com")
        assert response.status_code == 401
        assert response.get_json()["error"] == (
            "Please verify your email before logging in"
        )

    def test_login_success(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        verify_email(client, mock_email, "alice@example.com")
        response = login_user(client, "alice@example.com")
        assert response.status_code == 201
        body = response.get_json()
        assert body["message"] == "User login successfully"
        assert "access_token" in body["token"]
        assert "refresh_token" in body["token"]
        assert body["token"]["role"] == "user"

    def test_login_wrong_password(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        verify_email(client, mock_email, "alice@example.com")
        response = login_user(client, "alice@example.com", "wrong12")
        assert response.status_code == 401
        assert response.get_json()["error"] == "invalid email or password"

    def test_login_unknown_email(self, client):
        response = login_user(client, "nobody@example.com")
        assert response.status_code == 401
        assert response.get_json()["error"] == "invalid email or password"

    @pytest.mark.parametrize(
        "payload,substring",
        [
            (None, "cannot be empty"),
            ({}, "email is required"),
            ({"email": "alice@example.com"}, "password is required"),
            ({"password": PASSWORD}, "email is required"),
            ({"email": "   ", "password": PASSWORD}, "email cannot be empty"),
            (
                {"email": "alice@example.com", "password": "   "},
                "password cannot be empty",
            ),
            (
                {"email": "not-an-email", "password": PASSWORD},
                "invaid email format",
            ),
        ],
    )
    def test_login_validation_errors(self, client, payload, substring):
        if payload is None:
            response = client.post(
                "/api/login",
                data="null",
                content_type="application/json",
            )
        else:
            response = client.post("/api/login", json=payload)
        assert response.status_code == 401
        assert substring in response.get_json()["error"]

    def test_login_malformed_json(self, client):
        response = client.post(
            "/api/login",
            data="{not-json",
            content_type="application/json",
        )
        assert response.status_code == 401
        assert response.get_json()["error"] == "cannot be empty"

    def test_login_allows_get_with_json_body(self, client, mock_email):
        register_user(client, "alice", "alice@example.com")
        verify_email(client, mock_email, "alice@example.com")
        response = client.open(
            "/api/login",
            method="GET",
            json={"email": "alice@example.com", "password": PASSWORD},
        )
        assert response.status_code == 201

    def test_login_rejects_put(self, client):
        response = client.put("/api/login", json=REGISTER_PAYLOAD)
        assert response.status_code == 405

    def test_protected_route_without_token(self, client):
        response = client.get("/api/profile")
        assert response.status_code == 401

    def test_protected_route_after_login(self, user_a, client):
        response = client.get("/api/profile", headers=user_a["headers"])
        assert response.status_code == 200
        body = response.get_json()
        assert body["email"] == "alice@example.com"
        assert body["username"] == "alice"

    def test_protected_route_with_invalid_token(self, client):
        response = client.get(
            "/api/profile",
            headers=auth_header("not-a-real-token"),
        )
        assert response.status_code == 401
        assert "message" in response.get_json()

    def test_refresh_success(self, client, user_a):
        response = client.post(
            "/api/refresh",
            headers=auth_header(user_a["refresh_token"]),
        )
        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_refresh_rejects_access_token(self, client, user_a):
        response = client.post("/api/refresh", headers=user_a["headers"])
        assert response.status_code == 401

    def test_logout_revokes_access_token(self, client, user_a):
        response = client.post("/api/logout", headers=user_a["headers"])
        assert response.status_code == 200
        assert response.get_json()["message"] == "access token revoked"
        blocked = client.get("/api/profile", headers=user_a["headers"])
        assert blocked.status_code == 401
        assert "revoked" in blocked.get_json()["message"].lower()

    def test_logout_does_not_revoke_refresh_token(self, client, user_a):
        client.post("/api/logout", headers=user_a["headers"])
        refresh = client.post(
            "/api/refresh",
            headers=auth_header(user_a["refresh_token"]),
        )
        assert refresh.status_code == 200

    def test_logout_refresh_revokes_refresh_token(self, client, user_a):
        response = client.post(
            "/api/logout/refresh",
            headers=auth_header(user_a["refresh_token"]),
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "refresh token revoked"
        retry = client.post(
            "/api/refresh",
            headers=auth_header(user_a["refresh_token"]),
        )
        assert retry.status_code == 401

    def test_logout_requires_auth(self, client):
        assert client.post("/api/logout").status_code == 401
        assert client.post("/api/logout/refresh").status_code == 401
        assert client.get("/api/logout").status_code == 405
