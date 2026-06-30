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
    assert '<script src="/static/app.js"></script>' in body


def test_web_frontend_serves_stylesheet():
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert ".layout" in response.text
    assert ".state-grid" in response.text
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
