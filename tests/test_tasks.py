import pytest

from tests.conftest import query_db


def create_task(client, headers, **overrides):
    payload = {
        "title": "Buy milk",
        "description": "2%",
        "status": "pending",
        "priority": "medium",
    }
    payload.update(overrides)
    return client.post("/api/tasks", headers=headers, json=payload)


def first_task_id(client, headers):
    tasks = client.get("/api/tasks", headers=headers).get_json()["tasks"]
    return tasks[0]["id"]


class TestTasks:
    def test_create_task_success(self, client, user_a, db_path):
        response = create_task(client, user_a["headers"])
        assert response.status_code == 201
        body = response.get_json()
        assert body["title"] == "Buy milk"
        assert body["description"] == "2%"
        assert body["status"] == "pending"
        assert body["priority"] == "medium"
        assert body["due_date"] is None
        rows = query_db(db_path, "SELECT * FROM tasks")
        assert len(rows) == 1
        assert rows[0]["title"] == "Buy milk"

    def test_create_task_defaults(self, client, user_a):
        response = client.post(
            "/api/tasks",
            headers=user_a["headers"],
            json={"title": "Only title"},
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body["status"] == "pending"
        assert body["priority"] == "medium"
        assert body["description"] == ""

    def test_create_task_requires_auth(self, client):
        assert create_task(client, {}).status_code == 401

    @pytest.mark.parametrize(
        "payload,error",
        [
            (None, "JSON body is required"),
            ({}, "Title is required"),
            ({"description": "x"}, "Title is required"),
            ({"title": ""}, "Title cannot be empty"),
            ({"title": "   "}, "Title cannot be empty"),
            ({"title": "123"}, "Title cannot be all digits"),
            ({"title": 1}, "Title must be a string"),
            ({"title": "ok", "description": 1}, "Description must be a string"),
            ({"title": "ok", "description": "x" * 1001}, "Description is too long"),
            ({"title": "ok", "status": "banana"}, "Status must be pending or completed"),
            ({"title": "ok", "status": "123"}, "Status cannot be all digits"),
            ({"title": "ok", "priority": "urgent"}, "Priority must be low, medium or high"),
            ({"title": "ok", "due_date": "01-01-2026"}, "Invalid due date format"),
            ({"title": "ok", "category_id": "1"}, "Category id must be an integer"),
            ({"title": "ok", "category_id": 0}, "Invalid category"),
        ],
    )
    def test_create_task_validation(self, client, user_a, payload, error):
        if payload is None:
            response = client.post(
                "/api/tasks",
                headers=user_a["headers"],
                data="null",
                content_type="application/json",
            )
        else:
            response = client.post(
                "/api/tasks", headers=user_a["headers"], json=payload
            )
        assert response.status_code == 400
        assert response.get_json()["error"] == error

    def test_create_task_malformed_json(self, client, user_a):
        response = client.post(
            "/api/tasks",
            headers=user_a["headers"],
            data="{not-json",
            content_type="application/json",
        )
        assert response.status_code in (400, 415)

    def test_list_tasks_empty(self, client, user_a):
        response = client.get("/api/tasks", headers=user_a["headers"])
        assert response.status_code == 200
        body = response.get_json()
        assert body["tasks"] == []
        assert body["total task"] == 0
        assert body["page"] == 1

    def test_list_tasks_filters_and_pagination(self, client, user_a):
        create_task(client, user_a["headers"], title="Alpha", priority="high")
        create_task(
            client,
            user_a["headers"],
            title="Beta",
            status="completed",
            priority="low",
        )
        create_task(client, user_a["headers"], title="Gamma")

        listed = client.get("/api/tasks", headers=user_a["headers"])
        assert listed.status_code == 200
        assert listed.get_json()["total task"] == 3

        search = client.get("/api/tasks?search=alp", headers=user_a["headers"])
        assert search.get_json()["total task"] == 1
        assert search.get_json()["tasks"][0]["title"] == "Alpha"

        status = client.get("/api/tasks?status=completed", headers=user_a["headers"])
        assert status.get_json()["total task"] == 1

        priority = client.get("/api/tasks?priority=high", headers=user_a["headers"])
        assert priority.get_json()["total task"] == 1

        page = client.get("/api/tasks?page=1&limit=2", headers=user_a["headers"])
        body = page.get_json()
        assert body["limit"] == 2
        assert len(body["tasks"]) == 2
        assert body["total page"] == 2

    @pytest.mark.parametrize(
        "query,error",
        [
            ("search=" + ("a" * 101), "search querey too long"),
            ("priority=urgent", "invalid priority"),
            ("status=done", "invalid status"),
            ("page=0", "page must be an positive integer"),
            ("limit=0", "limit must be an positive integer and 1-20 "),
            ("limit=21", "limit must be an positive integer and 1-20 "),
            ("sort_by=title", "invalid sort feild"),
            ("order=up", "invalid order"),
        ],
    )
    def test_list_tasks_query_validation(self, client, user_a, query, error):
        response = client.get(f"/api/tasks?{query}", headers=user_a["headers"])
        assert response.status_code == 400
        assert response.get_json()["error"] == error

    def test_get_update_delete_own_task(self, client, user_a):
        created = create_task(client, user_a["headers"], title="Own task")
        assert created.status_code == 201
        task_id = first_task_id(client, user_a["headers"])

        fetched = client.get(f"/api/tasks/{task_id}", headers=user_a["headers"])
        assert fetched.status_code == 200
        assert fetched.get_json()["title"] == "Own task"

        updated = client.put(
            f"/api/tasks/{task_id}",
            headers=user_a["headers"],
            json={
                "title": "Updated",
                "description": "changed",
                "status": "completed",
                "priority": "high",
                "due_date": "2026-12-31",
            },
        )
        assert updated.status_code == 200
        assert updated.get_json()["title"] == "Updated"
        assert updated.get_json()["status"] == "completed"

        deleted = client.delete(f"/api/tasks/{task_id}", headers=user_a["headers"])
        assert deleted.status_code == 200
        assert deleted.get_json()["message"] == "Task deleted successfully"
        missing = client.get(f"/api/tasks/{task_id}", headers=user_a["headers"])
        assert missing.status_code == 404
        assert missing.get_json()["error"] == "task not found"

    def test_cannot_access_other_users_task(self, client, user_a, user_b):
        create_task(client, user_a["headers"], title="Alice only")
        alice_id = first_task_id(client, user_a["headers"])

        listed = client.get("/api/tasks", headers=user_b["headers"])
        assert listed.get_json()["tasks"] == []

        fetched = client.get(f"/api/tasks/{alice_id}", headers=user_b["headers"])
        assert fetched.status_code == 404
        assert fetched.get_json()["error"] == "forbidden"

        updated = client.put(
            f"/api/tasks/{alice_id}",
            headers=user_b["headers"],
            json={"title": "Hacked"},
        )
        assert updated.status_code == 404
        assert updated.get_json()["error"] == "forbidden"

        deleted = client.delete(f"/api/tasks/{alice_id}", headers=user_b["headers"])
        assert deleted.status_code == 404
        assert deleted.get_json()["error"] == "forbidden"

        still_there = client.get(f"/api/tasks/{alice_id}", headers=user_a["headers"])
        assert still_there.status_code == 200

    def test_missing_task(self, client, user_a):
        response = client.get("/api/tasks/999", headers=user_a["headers"])
        assert response.status_code == 404
        assert response.get_json()["error"] == "task not found"

    def test_update_task_validation(self, client, user_a):
        create_task(client, user_a["headers"])
        task_id = first_task_id(client, user_a["headers"])
        response = client.put(
            f"/api/tasks/{task_id}",
            headers=user_a["headers"],
            json={"title": ""},
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "Title cannot be empty"

    def test_tasks_wrong_methods_and_unauthenticated(self, client, user_a):
        create_task(client, user_a["headers"])
        task_id = first_task_id(client, user_a["headers"])
        assert client.patch("/api/tasks", headers=user_a["headers"]).status_code == 405
        assert client.get("/api/tasks").status_code == 401
        assert client.get(f"/api/tasks/{task_id}").status_code == 401
        assert client.delete(f"/api/tasks/{task_id}").status_code == 401
