# Web Frontend

## Purpose

The first web frontend is a static FastAPI-served page for operating the
existing DefenseTask workflow.

It intentionally avoids React, Vite, Node.js, and a frontend build pipeline.
The goal is to learn the browser-to-FastAPI interaction model before adding a
larger frontend stack.

## Files

```text
app/api/routes/frontend.py
app/api/static/index.html
app/api/static/styles.css
app/api/static/app.js
tests/test_api_frontend.py
```

## Route

```text
GET /
GET /static/styles.css
GET /static/app.js
```

## Supported Workflow

The page calls existing Task API endpoints:

```text
POST /tasks
GET  /tasks/{task_id}
POST /tasks/{task_id}/steps/start
POST /tasks/{task_id}/steps/execute
POST /tasks/{task_id}/answer
POST /tasks/{task_id}/follow-up-answer
GET  /tasks/{task_id}/analysis
POST /tasks/{task_id}/report/export
```

This supports the same core task loop as the CLI:

```text
create task
-> start next step
-> execute automatic step
-> submit answer
-> submit follow-up answer
-> analyze task
-> export markdown report
```

## Local Run

Start the API:

```powershell
uv run uvicorn app.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

Docker Compose:

```powershell
docker compose up -d api
```

Open:

```text
http://127.0.0.1:8000/
```

## Current Boundary

Completed:

```text
static frontend entry
task creation
task loading
step start
step execution
student answer submission
follow-up answer submission
task analysis view
markdown report export view
responsive CSS
offline FastAPI TestClient coverage
```

Not completed:

```text
React / Vue / frontend build pipeline
authentication
user accounts
visual trace graph
SSE progress integration
WebSocket task control integration
file upload UI
frontend E2E browser tests
```
