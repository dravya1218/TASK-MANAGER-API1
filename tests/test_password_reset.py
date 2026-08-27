from tests.conftest import (
    PASSWORD,
    auth_header,
    execute_db,
    get_latest_otp_row,
    get_user_row,
    login_user,
)


class TestChangePassword:
    def test_change_password_success(self, client, user_a):
        response = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            json={
                "current_password": PASSWORD,
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            },
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "Password changed successfully"
        old_login = login_user(client, "alice@example.com", PASSWORD)
        assert old_login.status_code == 401
        new_login = login_user(client, "alice@example.com", "newpass1")
        assert new_login.status_code == 201

    def test_change_password_requires_auth(self, client):
        response = client.post(
            "/api/change-password",
            json={
                "current_password": PASSWORD,
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            },
        )
        assert response.status_code == 401

    def test_change_password_validation(self, client, user_a):
        missing = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            data="null",
            content_type="application/json",
        )
        assert missing.status_code == 400
        assert missing.get_json()["error"] == "JSON body is required"

        empty = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            json={
                "current_password": "",
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            },
        )
        assert empty.status_code == 400
        assert empty.get_json()["error"] == "All password fields are required"

        short = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            json={
                "current_password": PASSWORD,
                "new_password": "ab12",
                "confirm_password": "ab12",
            },
        )
        assert short.status_code == 400
        assert short.get_json()["error"] == "Password must be at least 6 characters"

        mismatch = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            json={
                "current_password": PASSWORD,
                "new_password": "newpass1",
                "confirm_password": "newpass2",
            },
        )
        assert mismatch.status_code == 400
        assert mismatch.get_json()["error"] == "Passwords do not match"

        wrong = client.post(
            "/api/change-password",
            headers=user_a["headers"],
            json={
                "current_password": "wrong12",
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            },
        )
        assert wrong.status_code == 400
        assert wrong.get_json()["error"] == "Current password is incorrect"

    def test_change_password_rejects_get(self, client, user_a):
        assert (
            client.get("/api/change-password", headers=user_a["headers"]).status_code
            == 405
        )


class TestPasswordReset:
    def test_forgot_password_sends_otp(self, client, user_a, mock_email, db_path):
        before = len(mock_email.messages)
        response = client.post(
            "/api/forgot-password",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "Password reset OTP sent successfully"
        assert len(mock_email.messages) == before + 1
        user = get_user_row(db_path, "alice@example.com")
        otp = get_latest_otp_row(db_path, user["id"], "password_reset")
        assert otp is not None
        assert otp["used"] == 0
        assert mock_email.last()["email"] == "alice@example.com"
        assert mock_email.last_otp() == otp["otp"]

    def test_forgot_password_validation(self, client):
        missing_body = client.post(
            "/api/forgot-password",
            data="null",
            content_type="application/json",
        )
        assert missing_body.status_code == 400
        assert missing_body.get_json()["error"] == "JSON body is required"

        missing_email = client.post("/api/forgot-password", json={})
        assert missing_email.status_code == 400
        assert missing_email.get_json()["error"] == "Email is required"

        unknown = client.post(
            "/api/forgot-password",
            json={"email": "missing@example.com"},
        )
        assert unknown.status_code == 400
        assert unknown.get_json()["error"] == "User not found"

    def test_forgot_password_cooldown(self, client, user_a):
        client.post("/api/forgot-password", json={"email": "alice@example.com"})
        response = client.post(
            "/api/forgot-password", json={"email": "alice@example.com"}
        )
        assert response.status_code == 400
        assert "Please wait" in response.get_json()["error"]

    def test_verify_password_reset_and_reset_password(
        self, client, user_a, mock_email, db_path
    ):
        client.post("/api/forgot-password", json={"email": "alice@example.com"})
        otp = mock_email.last_otp()
        verify = client.post(
            "/api/verify-password-reset",
            json={"email": "alice@example.com", "otp": otp},
        )
        assert verify.status_code == 200
        body = verify.get_json()
        assert body["message"] == "Password reset OTP verified successfully"
        reset_token = body["reset_token"]

        user = get_user_row(db_path, "alice@example.com")
        otp_row = get_latest_otp_row(db_path, user["id"], "password_reset")
        assert otp_row["used"] == 1

        reset = client.post(
            "/api/reset-password",
            headers=auth_header(reset_token),
            json={
                "new_password": "resetpw1",
                "confirm_password": "resetpw1",
            },
        )
        assert reset.status_code == 200
        assert reset.get_json()["message"] == "Password reset successfully"

        old = login_user(client, "alice@example.com", PASSWORD)
        assert old.status_code == 401
        new = login_user(client, "alice@example.com", "resetpw1")
        assert new.status_code == 201

        reused = client.post(
            "/api/verify-password-reset",
            json={"email": "alice@example.com", "otp": otp},
        )
        assert reused.status_code == 400
        assert reused.get_json()["error"] == "No active password reset OTP found"

    def test_verify_password_reset_validation(self, client, user_a, mock_email):
        missing_body = client.post(
            "/api/verify-password-reset",
            data="null",
            content_type="application/json",
        )
        assert missing_body.status_code == 400
        assert missing_body.get_json()["error"] == "JSON body is required"

        missing_email = client.post(
            "/api/verify-password-reset", json={"otp": "123456"}
        )
        assert missing_email.status_code == 400
        assert missing_email.get_json()["error"] == "Email is required"

        missing_otp = client.post(
            "/api/verify-password-reset",
            json={"email": "alice@example.com"},
        )
        assert missing_otp.status_code == 400
        assert missing_otp.get_json()["error"] == "OTP is required"

        unknown = client.post(
            "/api/verify-password-reset",
            json={"email": "missing@example.com", "otp": "123456"},
        )
        assert unknown.status_code == 400
        assert unknown.get_json()["error"] == "User not found"

        client.post("/api/forgot-password", json={"email": "alice@example.com"})
        invalid = client.post(
            "/api/verify-password-reset",
            json={"email": "alice@example.com", "otp": "000000"},
        )
        assert invalid.status_code == 400
        assert invalid.get_json()["error"] == "Invalid OTP"

    def test_password_reset_otp_expired(self, client, user_a, mock_email, db_path):
        client.post("/api/forgot-password", json={"email": "alice@example.com"})
        execute_db(
            db_path,
            "UPDATE otp_codes SET expires_at = ? WHERE purpose = ?",
            ("2000-01-01T00:00:00+00:00", "password_reset"),
        )
        response = client.post(
            "/api/verify-password-reset",
            json={
                "email": "alice@example.com",
                "otp": mock_email.last_otp(),
            },
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "OTP has expired"

    def test_reset_password_rejects_normal_access_token(self, client, user_a):
        response = client.post(
            "/api/reset-password",
            headers=user_a["headers"],
            json={
                "new_password": "resetpw1",
                "confirm_password": "resetpw1",
            },
        )
        assert response.status_code == 403
        assert response.get_json()["error"] == "Invalid password reset token"

    def test_reset_password_validation(self, client, user_a, mock_email):
        client.post("/api/forgot-password", json={"email": "alice@example.com"})
        verify = client.post(
            "/api/verify-password-reset",
            json={
                "email": "alice@example.com",
                "otp": mock_email.last_otp(),
            },
        )
        token = verify.get_json()["reset_token"]
        headers = auth_header(token)

        missing_body = client.post(
            "/api/reset-password",
            headers=headers,
            data="null",
            content_type="application/json",
        )
        assert missing_body.status_code == 400
        assert missing_body.get_json()["error"] == "JSON body is required"

        missing_new = client.post(
            "/api/reset-password",
            headers=headers,
            json={"confirm_password": "resetpw1"},
        )
        assert missing_new.status_code == 400
        assert missing_new.get_json()["error"] == "New password is required"

        missing_confirm = client.post(
            "/api/reset-password",
            headers=headers,
            json={"new_password": "resetpw1"},
        )
        assert missing_confirm.status_code == 400
        assert missing_confirm.get_json()["error"] == "Confirm password is required"

        mismatch = client.post(
            "/api/reset-password",
            headers=headers,
            json={
                "new_password": "resetpw1",
                "confirm_password": "resetpw2",
            },
        )
        assert mismatch.status_code == 400
        assert mismatch.get_json()["error"] == "Passwords do not match"

        short = client.post(
            "/api/reset-password",
            headers=headers,
            json={"new_password": "ab12", "confirm_password": "ab12"},
        )
        assert short.status_code == 400
        assert short.get_json()["error"] == "Password must be at least 6 characters"

    def test_reset_password_requires_auth(self, client):
        response = client.post(
            "/api/reset-password",
            json={
                "new_password": "resetpw1",
                "confirm_password": "resetpw1",
            },
        )
        assert response.status_code == 401

    def test_password_reset_wrong_methods(self, client):
        assert client.get("/api/forgot-password").status_code == 405
        assert client.get("/api/verify-password-reset").status_code == 405
        assert client.get("/api/reset-password").status_code == 405
