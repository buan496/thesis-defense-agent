import json

import pytest

from app import cli


def test_record_feedback_command_writes_feedback(
    monkeypatch,
    capsys,
    tmp_path,
):
    feedback_path = tmp_path / "feedback.jsonl"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "record-feedback",
            "--source-type",
            "agent_trace",
            "--source-id",
            "line:1",
            "--rating",
            "5",
            "--comment",
            "回答有依据，可以沉淀。",
            "--tag",
            "useful",
            "--tag",
            "grounded",
            "--metadata",
            '{"query":"系统架构"}',
            "--file",
            str(feedback_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "FEEDBACK RECORDED" in output
    assert "SOURCE TYPE: agent_trace" in output
    assert "SOURCE ID: line:1" in output
    assert "RATING: 5" in output

    saved = json.loads(
        feedback_path.read_text(encoding="utf-8").strip()
    )
    assert saved["source_type"] == "agent_trace"
    assert saved["source_id"] == "line:1"
    assert saved["rating"] == 5
    assert saved["comment"] == "回答有依据，可以沉淀。"
    assert saved["tags"] == ["useful", "grounded"]
    assert saved["metadata"] == {"query": "系统架构"}


def test_record_feedback_command_rejects_invalid_rating(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "record-feedback",
            "--source-type",
            "agent_trace",
            "--source-id",
            "line:1",
            "--rating",
            "9",
            "--comment",
            "评分非法",
            "--file",
            str(tmp_path / "feedback.jsonl"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "FEEDBACK ERROR" in output
    assert "rating" in output


def test_record_feedback_command_rejects_invalid_metadata(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "record-feedback",
            "--source-type",
            "agent_trace",
            "--source-id",
            "line:1",
            "--rating",
            "3",
            "--comment",
            "metadata 非法",
            "--metadata",
            "[1, 2, 3]",
            "--file",
            str(tmp_path / "feedback.jsonl"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "FEEDBACK ERROR" in output


def test_summarize_feedback_command_outputs_summary(
    monkeypatch,
    capsys,
    tmp_path,
):
    feedback_path = tmp_path / "feedback.jsonl"
    records = [
        {
            "id": "1",
            "source_type": "agent_trace",
            "source_id": "line:1",
            "rating": 5,
            "comment": "好",
            "tags": ["useful"],
            "metadata": {},
        },
        {
            "id": "2",
            "source_type": "defense_task",
            "source_id": "task-1",
            "rating": 3,
            "comment": "一般",
            "tags": ["needs_follow_up"],
            "metadata": {},
        },
    ]
    feedback_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "summarize-feedback",
            "--file",
            str(feedback_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "FEEDBACK SUMMARY" in output
    assert "COUNT: 2" in output
    assert "AVERAGE RATING: 4.0" in output
    assert "agent_trace" in output
    assert "needs_follow_up" in output
