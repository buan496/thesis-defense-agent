from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_web_frontend_serves_index_html():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    body = response.text

    assert "<title>Thesis Defense Agent</title>" in body
    assert "论文答辩训练" in body
    assert 'id="topicInput"' in body
    assert 'id="createTaskButton"' in body
    assert 'id="executeStepButton"' in body
    assert 'id="submitAnswerButton"' in body
    assert 'id="submitFollowUpAnswerButton"' in body
    assert 'id="reportButton"' in body
    assert 'id="connectWebSocketButton"' in body
    assert 'id="downloadReportButton"' in body
    assert 'id="documentFileInput"' in body
    assert 'id="uploadDocumentButton"' in body
    assert 'id="streamMessageInput"' in body
    assert 'id="streamEchoButton"' in body
    assert 'id="websocketStatus"' in body
    assert 'id="traceMetrics"' in body
    assert 'id="stepDetailOutput"' in body
    assert 'id="streamOutput"' in body
    assert '<script src="/static/app.js"></script>' in body


def test_web_frontend_serves_stylesheet():
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert ".layout" in response.text
    assert ".state-grid" in response.text
    assert ".metric-grid" in response.text
    assert ".step-button" in response.text
    assert ".header-actions" in response.text
    assert "@media (max-width: 920px)" in response.text


def test_web_frontend_serves_javascript():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "async function createTask()" in response.text
    assert 'requestJson("/tasks"' in response.text
    assert "steps/start" in response.text
    assert "steps/execute" in response.text
    assert "follow-up-answer" in response.text
    assert "report/export" in response.text
    assert "async function uploadDocument()" in response.text
    assert "async function streamEcho()" in response.text
    assert "function connectWebSocket()" in response.text
    assert "function downloadReport()" in response.text
    assert "new EventSource" in response.text
    assert "new WebSocket" in response.text
    assert "/documents/upload" in response.text
    assert "/stream/echo" in response.text
    assert "/ws/tasks/" in response.text
