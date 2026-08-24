Agreed.

Before moving to any new topic, we'll do:

```text id="utj5hm"
1. Notes
2. Recall Questions
3. Your Explanation
4. Then next topic
```

That matches how you've learned Flask successfully.

---

# Notes: Backend Engineering - Day 1

## Client and Server

```text id="ut0f7q"
Client:
The system that sends requests.

Examples:
- Browser
- Mobile App
- React Frontend
- Another Server

Server:
The system that receives requests and sends responses.

In our project:

Client = Browser
Server = Flask
```

---

## Request-Response Cycle

```text id="em4c7r"
Browser
↓ Request
Flask
↓
SQLite
↓
Flask
↓ Response
Browser
```

Important:

```text id="3ug86d"
SQLite never talks directly to the browser.

Browser ↔ Flask

Flask ↔ SQLite
```

---

## Web Application vs API

### Web Route

```python id="sj4zjh"
return render_template(...)
```

Response:

```text id="dvw5c4"
HTML
```

Purpose:

```text id="0vfdrs"
Show a webpage.
```

---

### API Route

```python id="0r6ay5"
return jsonify(...)
```

Response:

```text id="xjlwm7"
JSON
```

Purpose:

```text id="7hsmph"
Provide data.
```

---

## Why APIs Exist

Without APIs:

```text id="6vkobc"
Browser
↓
Flask
↓
HTML
```

Only browsers easily understand the response.

With APIs:

```text id="vjlwm8"
Browser
Mobile App
React App
Another Server
↓
Flask API
↓
JSON
```

Many clients can use the same backend.

---

## HTML vs JSON

```text id="c2g2d4"
HTML = Presentation

Answers:
"How should it look?"
```

```text id="jlwm3x"
JSON = Data

Answers:
"What is the data?"
```

---

## HTTP Methods

### GET

Purpose:

```text id="jlwm4p"
Read data
View data
Show pages
```

Examples:

```text id="jlwm8r"
GET /expense
GET /profile
GET /login
```

Rule:

```text id="jlwm6c"
GET should not modify data.
```

---

### POST

Purpose:

```text id="jlwm2e"
Create data
Submit data
```

Examples:

```text id="jlwm1j"
POST /login
POST /signup
POST /add_expense
```

---

### PUT

Purpose:

```text id="jlwm9b"
Update existing data.
```

API Example:

```text id="jlwm0k"
PUT /api/expenses/5
```

---

### DELETE

Purpose:

```text id="jlwm5n"
Delete existing data.
```

API Example:

```text id="jlwm7f"
DELETE /api/expenses/5
```

---

## API CRUD Mapping

```text id="jlwm4u"
Create -> POST
Read   -> GET
Update -> PUT
Delete -> DELETE
```

---
---

# Notes: JSON Revision

## Single Item

Python:

```python id="n8f1dw"
expense = {
    "id": 1,
    "name": "Food"
}
```

Type:

```text id="t9r3va"
Dictionary
```

---

## Multiple Items

Python:

```python id="v5m7qe"
expenses = [
    {"id": 1, "name": "Food"},
    {"id": 2, "name": "Travel"}
]
```

Type:

```text id="w1k8ys"
List of Dictionaries
```

---

## jsonify()

```python id="u7p4hn"
return jsonify(expense)
```

Purpose:

```text id="z2c6mr"
Convert Python data
↓
JSON Response
↓
Send to Client
```

---

## Important Distinction

Inside Flask:

```python id="r4n8jt"
expense = {
    "id": 1
}
```

is:

```text id="q8v3yl"
Python Dictionary
```

After:

```python id="d1h6wf"
return jsonify(expense)
```

Client receives:

```json id="x7b2mp"
{
  "id": 1
}
```

which is:

```text id="j5u9kd"
JSON
```

---

## JSON Rules

```text id="k3e7qw"
Strings -> quotes

Numbers -> no quotes

Boolean -> true/false

Null -> null
```

---

# Notes: HTTP Status Codes
200 -> Success

201 -> Created

400 -> Invalid client input

401 -> Not logged in

403 -> Permission denied    User IS logged in
                            BUT lacks permission.

404 -> Resource not found

500 -> Server error


# API Fundamentals Notes

## 1. Client and Server

### Client

Sends requests.

Examples:

```text
Browser
Mobile App
React Frontend
Thunder Client
```

### Server

Receives requests and sends responses.

In our project:

```text
Client = Thunder Client

Server = Flask
```

---

## 2. Request Response Cycle

```text
Client
↓ Request
Flask
↓ Response
Client
```

Example:

```text
Thunder Client
↓
GET /api/tasks
↓
Flask
↓
JSON Response
↓
Thunder Client
```

---

## 3. API vs Web Route

### Web Route

```python
return render_template(...)
```

Returns:

```text
HTML
```

Purpose:

```text
Show UI
```

---

### API Route

```python
return jsonify(...)
```

Returns:

```text
JSON
```

Purpose:

```text
Provide Data
```

---

## 4. JSON

### JSON Object

```json
{
  "id": 1,
  "title": "Learn APIs"
}
```

Python:

```python
{
    "id": 1,
    "title": "Learn APIs"
}
```

Type:

```text
Dictionary
```

---

### JSON Array

```json
[
  {
    "id": 1
  },
  {
    "id": 2
  }
]
```

Python:

```python
[
    {"id": 1},
    {"id": 2}
]
```

Type:

```text
List of Dictionaries
```

---

## 5. jsonify()

Purpose:

```text
Convert Python data
↓
JSON Response
↓
Send to Client
```

Example:

```python
return jsonify(task)
```

---

## 6. Request Body

Client sends:

```json
{
  "title": "Learn APIs",
  "status": "pending"
}
```

Read in Flask:

```python
data = request.get_json()
```

Result:

```python
{
    "title": "Learn APIs",
    "status": "pending"
}
```

Type:

```text
Dictionary
```

---

## 7. HTTP Methods

### GET

Purpose:

```text
Read Data
```

Examples:

```http
GET /api/tasks

GET /api/tasks/1
```

---

### POST

Purpose:

```text
Create Data
```

Example:

```http
POST /api/tasks
```

---

## 8. Status Codes

```text
200 -> Success

201 -> Resource Created

400 -> Invalid Client Input

401 -> Not Logged In

403 -> Logged In But Not Allowed

404 -> Resource Not Found

500 -> Server Error
```

---

## 9. URL Parameters

Example:

```text
/api/tasks/7
```

Flask:

```python
@app.route("/api/tasks/<int:id>")
```

Result:

```python
id = 7
```

Purpose:

```text
Identify a specific resource.
```

---

## 10. Routes Built

### Health Check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok"
}
```

---

### Create Task

```http
POST /api/tasks
```

Response:

```json
{
  "id": 1,
  "title": "Learn APIs",
  "status": "pending"
}
```

Status:

```text
201 Created
```

---

### View All Tasks

```http
GET /api/tasks
```

Response:

```json
[
  {...},
  {...}
]
```

---

### View Single Task

```http
GET /api/tasks/1
```

Response:

```json
{
  "id": 1,
  "title": "Learn APIs"
}
```

or

```json
{
  "error": "Task not found"
}
```

with:

```text
404
```
Before next topic, notes first.

## Notes: API CRUD + Validation

### REST Route Pattern

```text
GET    /api/tasks        → read all tasks
POST   /api/tasks        → create task
GET    /api/tasks/<id>   → read one task
PUT    /api/tasks/<id>   → update one task
DELETE /api/tasks/<id>   → delete one task
```

### Core Rule

```text
URL = resource
HTTP method = action
```

Example:

```text
/api/tasks/2 = task with id 2

GET    = read it
PUT    = update it
DELETE = remove it
```

### Request Body

Used when client sends data:

```text
POST → needs request body
PUT  → needs request body
GET  → usually no body
DELETE → usually no body
```

### Flask API Tools

```python
data = request.get_json()
```

Reads JSON sent by client.

```python
return jsonify(data), status_code
```

Sends JSON response to client.

### Status Codes

```text
200 → success
201 → created
400 → bad client input
404 → resource not found
```

### Validation

Validation protects the API from bad input.

Bad input examples:

```json
{}
```

```json
{"title": ""}
```

```json
{"title": "   "}
```

```json
{"title": "Learn APIs", "status": "banana"}
```

Correct response:

```json
{
  "error": "clear error message"
}
```

with:

```text
400
```

### Key Bug You Fixed

Wrong:

```python
return jsonify({"not found"}), 404
```

That is a set.

Correct:

```python
return jsonify({"error": "Task not found"}), 404
```

That is a dictionary.

### Main Lesson

Your Flask Expense Tracker used:

```text
request.form
render_template()
HTML
```

Your API uses:

```text
request.get_json()
jsonify()
JSON
```

Same backend thinking, different response format.

Next topic: separate this API into proper files — routes, validation, and service logic.
