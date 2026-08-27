from tests.conftest import execute_db, get_latest_otp_row, get_user_row


class TestProfile:
    def test_get_profile_success(self, client, user_a, db_path):
        response = client.get("/api/profile", headers=user_a["headers"])
        assert response.status_code == 200
        body = response.get_json()
        db_user = get_user_row(db_path, "alice@example.com")
        assert body["id"] == db_user["id"]
        assert body["username"] == "alice"
        assert body["email"] == "alice@example.com"
        assert body["role"] == "user"
        assert body["email_verified"] == 1
        assert "pending_email" in body
        assert "password_hash" not in body

    def test_get_profile_requires_auth(self, client):
        assert client.get("/api/profile").status_code == 401

    def test_user_sees_only_own_profile(self, client, user_a, user_b):
        alice = client.get("/api/profile", headers=user_a["headers"]).get_json()
        bob = client.get("/api/profile", headers=user_b["headers"]).get_json()
        assert alice["email"] == "alice@example.com"
        assert bob["email"] == "bob@example.com"
        assert alice["id"] != bob["id"]

    def test_update_username_success(self, client, user_a, db_path):
        response = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"username": "alice2"},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["email_verification_required"] is False
        assert body["message"] == "Profile updated successfully"
        assert body["user"]["username"] == "alice2"
        assert "password_hash" not in body
        assert "password_hash" not in body["user"]
        assert get_user_row(db_path, "alice@example.com")["username"] == "alice2"

    def test_update_email_sets_pending_and_sends_otp(
        self, client, user_a, mock_email, db_path
    ):
        response = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "alice-new@example.com"},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["email_verification_required"] is True
        assert "Verify the OTP" in body["message"]
        user = get_user_row(db_path, "alice@example.com")
        assert user["email"] == "alice@example.com"
        assert user["pending_email"] == "alice-new@example.com"
        assert mock_email.last()["email"] == "alice-new@example.com"
        otp_row = get_latest_otp_row(db_path, user["id"], "email_change")
        assert otp_row["otp"] == mock_email.last_otp()

    def test_verify_email_change_success(self, client, user_a, mock_email, db_path):
        client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "alice-new@example.com"},
        )
        otp = mock_email.last_otp()
        response = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={"otp": otp},
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "Email changed successfully"
        assert get_user_row(db_path, "alice@example.com") is None
        updated = get_user_row(db_path, "alice-new@example.com")
        assert updated["pending_email"] is None
        assert updated["email_verified"] == 1

        reused = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={"otp": otp},
        )
        assert reused.status_code == 400
        assert reused.get_json()["error"] == "No active OTP found"

    def test_verify_email_change_invalid_and_expired(
        self, client, user_a, mock_email, db_path
    ):
        client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "alice-new@example.com"},
        )
        invalid = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={"otp": "000000"},
        )
        assert invalid.status_code == 400
        assert invalid.get_json()["error"] == "Invalid OTP"

        execute_db(
            db_path,
            "UPDATE otp_codes SET expires_at = ? WHERE purpose = ?",
            ("2000-01-01T00:00:00+00:00", "email_change"),
        )
        expired = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={"otp": mock_email.last_otp()},
        )
        assert expired.status_code == 400
        assert expired.get_json()["error"] == "OTP has expired"

    def test_resend_email_change(self, client, user_a, mock_email, db_path):
        no_pending = client.post(
            "/api/resend-email-change", headers=user_a["headers"]
        )
        assert no_pending.status_code == 400
        assert no_pending.get_json()["error"] == "No pending email change"

        client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "alice-new@example.com"},
        )
        cooldown = client.post(
            "/api/resend-email-change", headers=user_a["headers"]
        )
        assert cooldown.status_code == 400
        assert "Please wait" in cooldown.get_json()["error"]

        execute_db(
            db_path,
            "UPDATE otp_codes SET created_at = ? WHERE purpose = ?",
            ("2000-01-01 00:00:00", "email_change"),
        )
        resend = client.post("/api/resend-email-change", headers=user_a["headers"])
        assert resend.status_code == 200
        assert resend.get_json()["message"] == "Email change OTP sent successfully"
        assert mock_email.last()["email"] == "alice-new@example.com"

    def test_profile_update_validation(self, client, user_a, user_b):
        missing_body = client.put(
            "/api/profile",
            headers=user_a["headers"],
            data="null",
            content_type="application/json",
        )
        assert missing_body.status_code == 400
        assert missing_body.get_json()["error"] == "JSON body is required"

        empty_username = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"username": "   "},
        )
        assert empty_username.status_code == 400
        assert empty_username.get_json()["error"] == "Username cannot be empty"

        bad_type = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"username": 123},
        )
        assert bad_type.status_code == 400
        assert bad_type.get_json()["error"] == "Username must be a string"

        empty_email = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "   "},
        )
        assert empty_email.status_code == 400
        assert empty_email.get_json()["error"] == "Email cannot be empty"

        bad_email = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "not-an-email"},
        )
        assert bad_email.status_code == 400
        assert bad_email.get_json()["error"] == "Invalid email format"

        taken_username = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"username": "bob"},
        )
        assert taken_username.status_code == 400
        assert taken_username.get_json()["error"] == "Username already exists"

        taken_email = client.put(
            "/api/profile",
            headers=user_a["headers"],
            json={"email": "bob@example.com"},
        )
        assert taken_email.status_code == 400
        assert taken_email.get_json()["error"] == "Email already exists"

    def test_verify_email_change_validation(self, client, user_a):
        missing_body = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            data="null",
            content_type="application/json",
        )
        assert missing_body.status_code == 400
        assert missing_body.get_json()["error"] == "JSON body is required"

        missing_otp = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={},
        )
        assert missing_otp.status_code == 400
        assert missing_otp.get_json()["error"] == "OTP is required"

        no_otp = client.post(
            "/api/verify-email-change",
            headers=user_a["headers"],
            json={"otp": "123456"},
        )
        assert no_otp.status_code == 400
        assert no_otp.get_json()["error"] == "No active OTP found"

    def test_email_change_routes_require_auth(self, client):
        assert (
            client.post(
                "/api/verify-email-change", json={"otp": "123456"}
            ).status_code
            == 401
        )
        assert client.post("/api/resend-email-change").status_code == 401
        assert client.put("/api/profile", json={"username": "x"}).status_code == 401

    def test_profile_wrong_methods(self, client, user_a):
        assert client.post("/api/profile", headers=user_a["headers"]).status_code == 405
        assert (
            client.get(
                "/api/verify-email-change", headers=user_a["headers"]
            ).status_code
            == 405
        )
        assert (
            client.get(
                "/api/resend-email-change", headers=user_a["headers"]
            ).status_code
            == 405
        )
