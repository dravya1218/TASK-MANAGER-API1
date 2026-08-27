from tests.conftest import get_user_row


class TestAdmin:
    def test_admin_dashboard_is_public_html(self, client):
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"html" in response.data.lower() or response.mimetype == "text/html"

    def test_list_users_requires_admin_permission(self, client, user_a, admin_user):
        denied = client.get("/api/users", headers=user_a["headers"])
        assert denied.status_code == 403
        body = denied.get_json()
        assert body["message"] == "Forbidden"
        assert body["required_permission"] == "view_all_users"

        allowed = client.get("/api/users", headers=admin_user["headers"])
        assert allowed.status_code == 200
        emails = {user["email"] for user in allowed.get_json()}
        assert "alice@example.com" in emails
        assert "admin@example.com" in emails

    def test_list_users_requires_auth(self, client):
        assert client.get("/api/users").status_code == 401

    def test_delete_user(self, client, admin_user, user_b, db_path):
        bob = get_user_row(db_path, "bob@example.com")
        response = client.delete(
            f"/api/users/{bob['id']}",
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "user deleted successfully"
        assert get_user_row(db_path, "bob@example.com") is None

    def test_admin_cannot_delete_self_when_jwt_identity_is_string(
        self, client, admin_user, db_path
    ):
        response = client.delete(
            f"/api/users/{int(admin_user['id'])}",
            headers=admin_user["headers"],
        )
        assert response.status_code == 400
        assert "cannot delete your own account" in response.get_json()["error"]
        assert get_user_row(db_path, "admin@example.com") is not None

    def test_delete_user_not_found(self, client, admin_user):
        response = client.delete("/api/users/999", headers=admin_user["headers"])
        assert response.status_code == 404
        assert response.get_json()["error"] == "user not found"

    def test_non_admin_cannot_delete_user(self, client, user_a, user_b, db_path):
        bob = get_user_row(db_path, "bob@example.com")
        response = client.delete(f"/api/users/{bob['id']}", headers=user_a["headers"])
        assert response.status_code == 403
        assert get_user_row(db_path, "bob@example.com") is not None

    def test_change_user_role(self, client, admin_user, user_a, db_path):
        alice = get_user_row(db_path, "alice@example.com")
        response = client.put(
            f"/api/users/{alice['id']}/role",
            headers=admin_user["headers"],
            json={"role": "admin"},
        )
        assert response.status_code == 200
        assert response.get_json()["message"] == "Role updated successfully"
        from database import find_role_id_by_name

        assert get_user_row(db_path, "alice@example.com")[
            "role_id"
        ] == find_role_id_by_name("admin")

        invalid = client.put(
            f"/api/users/{alice['id']}/role",
            headers=admin_user["headers"],
            json={"role": "manager"},
        )
        assert invalid.status_code == 400
        assert invalid.get_json()["error"] == "Invalid role."

        missing = client.put(
            "/api/users/999/role",
            headers=admin_user["headers"],
            json={"role": "user"},
        )
        assert missing.status_code == 404
        assert missing.get_json()["error"] == "User not found"

    def test_admin_cannot_change_own_role_when_jwt_identity_is_string(
        self, client, admin_user, db_path
    ):
        before = get_user_row(db_path, "admin@example.com")["role_id"]
        response = client.put(
            f"/api/users/{int(admin_user['id'])}/role",
            headers=admin_user["headers"],
            json={"role": "user"},
        )
        assert response.status_code == 400
        assert "cannot change your own role" in response.get_json()["error"]
        assert get_user_row(db_path, "admin@example.com")["role_id"] == before

    def test_non_admin_cannot_change_role(self, client, user_a, user_b, db_path):
        bob = get_user_row(db_path, "bob@example.com")
        response = client.put(
            f"/api/users/{bob['id']}/role",
            headers=user_a["headers"],
            json={"role": "admin"},
        )
        assert response.status_code == 403

    def test_assign_and_remove_permission(self, client, admin_user, user_a):
        assigned = client.post(
            "/api/assign_permission",
            headers=admin_user["headers"],
            json={"role_name": "user", "permission_name": "view_all_users"},
        )
        assert assigned.status_code == 200
        assert assigned.get_json()["message"] == "permission assigned successfully"

        already = client.post(
            "/api/assign_permission",
            headers=admin_user["headers"],
            json={"role_name": "user", "permission_name": "view_all_users"},
        )
        assert already.status_code == 200
        assert already.get_json()["message"] == "permission already assigned"

        allowed = client.get("/api/users", headers=user_a["headers"])
        assert allowed.status_code == 200

        removed = client.delete(
            "/api/remove_permission",
            headers=admin_user["headers"],
            json={"role_name": "user", "permission_name": "view_all_users"},
        )
        assert removed.status_code == 200
        assert removed.get_json()["message"] == "permission removed successfully"

        denied = client.get("/api/users", headers=user_a["headers"])
        assert denied.status_code == 403

        unknown_role = client.post(
            "/api/assign_permission",
            headers=admin_user["headers"],
            json={"role_name": "nope", "permission_name": "view_all_users"},
        )
        assert unknown_role.status_code == 200
        assert unknown_role.get_json()["message"] == "role_id cannot found"

    def test_roles_and_permissions_catalog(self, client, admin_user, user_a):
        denied = client.get(
            "/api/admin/roles-permissions", headers=user_a["headers"]
        )
        assert denied.status_code == 403

        catalog = client.get(
            "/api/admin/roles-permissions", headers=admin_user["headers"]
        )
        assert catalog.status_code == 200
        body = catalog.get_json()
        role_names = {role["name"] for role in body["roles"]}
        assert {"admin", "manager", "user"} <= role_names
        permission_names = {item["name"] for item in body["permissions"]}
        assert "manage_roles" in permission_names

        role_perms = client.get(
            "/api/admin/roles/user/permissions",
            headers=admin_user["headers"],
        )
        assert role_perms.status_code == 200
        names = {item["name"] for item in role_perms.get_json()}
        assert "create_task" in names

        missing_role = client.get(
            "/api/admin/roles/does-not-exist/permissions",
            headers=admin_user["headers"],
        )
        assert missing_role.status_code == 404
        assert missing_role.get_json()["error"] == "Role not found"

        updated = client.put(
            "/api/admin/roles/user/permissions",
            headers=admin_user["headers"],
            json={"permissions": ["view_task"]},
        )
        assert updated.status_code == 200
        assert updated.get_json()["message"] == "Permissions updated successfully."
        after = client.get(
            "/api/admin/roles/user/permissions",
            headers=admin_user["headers"],
        )
        assert [item["name"] for item in after.get_json()] == ["view_task"]

        unknown = client.put(
            "/api/admin/roles/nope/permissions",
            headers=admin_user["headers"],
            json={"permissions": []},
        )
        assert unknown.status_code == 400
        assert unknown.get_json()["error"] == "Role not found."

    def test_admin_json_routes_require_auth_and_wrong_methods(
        self, client, admin_user, db_path
    ):
        assert client.get("/api/assign_permission").status_code == 405
        assert client.post("/api/assign_permission").status_code == 401
        assert client.get("/api/admin/roles-permissions").status_code == 401
        admin = get_user_row(db_path, "admin@example.com")
        assert (
            client.get(
                f"/api/users/{admin['id']}/role", headers=admin_user["headers"]
            ).status_code
            == 405
        )
