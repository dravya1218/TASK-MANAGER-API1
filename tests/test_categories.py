from tests.conftest import query_db


class TestCategories:
    def test_create_and_list_categories(self, client, user_a, db_path):
        empty = client.get("/api/categories", headers=user_a["headers"])
        assert empty.status_code == 200
        assert empty.get_json() == []

        created = client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "Work"},
        )
        assert created.status_code == 201
        assert created.get_json()["message"] == "Category created successfully."
        rows = query_db(db_path, "SELECT * FROM categories")
        assert len(rows) == 1
        assert rows[0]["name"] == "Work"

        listed = client.get("/api/categories", headers=user_a["headers"])
        assert listed.status_code == 200
        assert listed.get_json()[0]["name"] == "Work"

    def test_duplicate_category(self, client, user_a):
        client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "Work"},
        )
        duplicate = client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "work"},
        )
        assert duplicate.status_code == 400
        assert duplicate.get_json()["error"] == "Category already exists."

    def test_create_category_validation(self, client, user_a):
        missing_name = client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={},
        )
        assert missing_name.status_code == 400
        assert missing_name.get_json()["error"] == "Category name is required."

        blank = client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "   "},
        )
        assert blank.status_code == 400
        assert blank.get_json()["error"] == "Category name is required."

    def test_delete_category(self, client, user_a, db_path):
        client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "Work"},
        )
        category_id = query_db(db_path, "SELECT id FROM categories")[0]["id"]
        deleted = client.delete(
            f"/api/categories/{category_id}",
            headers=user_a["headers"],
        )
        assert deleted.status_code == 200
        assert deleted.get_json()["message"] == "Category deleted successfully."
        assert query_db(db_path, "SELECT * FROM categories") == []

        missing = client.delete(
            f"/api/categories/{category_id}",
            headers=user_a["headers"],
        )
        assert missing.status_code == 400
        assert missing.get_json()["error"] == "Category not found."

    def test_cannot_delete_other_users_category(self, client, user_a, user_b, db_path):
        client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "AliceCat"},
        )
        category_id = query_db(db_path, "SELECT id FROM categories")[0]["id"]
        listed_b = client.get("/api/categories", headers=user_b["headers"])
        assert listed_b.get_json() == []
        deleted = client.delete(
            f"/api/categories/{category_id}",
            headers=user_b["headers"],
        )
        assert deleted.status_code == 400
        assert deleted.get_json()["error"] == "Category not found."
        assert query_db(db_path, "SELECT name FROM categories")[0]["name"] == "AliceCat"

    def test_task_can_use_category(self, client, user_a, db_path):
        client.post(
            "/api/categories",
            headers=user_a["headers"],
            json={"name": "Work"},
        )
        category_id = query_db(db_path, "SELECT id FROM categories")[0]["id"]
        created = client.post(
            "/api/tasks",
            headers=user_a["headers"],
            json={"title": "With cat", "category_id": category_id},
        )
        assert created.status_code == 201
        assert created.get_json()["category_id"] == category_id
        listed = client.get("/api/tasks", headers=user_a["headers"])
        assert listed.get_json()["tasks"][0]["category_name"] == "Work"

    def test_categories_require_auth_and_wrong_methods(self, client, user_a):
        assert client.get("/api/categories").status_code == 401
        assert client.post("/api/categories", json={"name": "x"}).status_code == 401
        assert client.delete("/api/categories/1").status_code == 401
        assert client.put("/api/categories", headers=user_a["headers"]).status_code == 405
