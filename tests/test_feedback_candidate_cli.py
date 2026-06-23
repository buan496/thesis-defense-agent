import json

from app import cli


def test_export_feedback_candidates_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    feedback_path = tmp_path / "feedback.jsonl"
    output_path = tmp_path / "candidates.json"
    records = [
        {
            "id": "bad",
            "source_type": "agent_trace",
            "source_id": "line:1",
            "rating": 1,
            "comment": "工具选择错误",
            "tags": [],
            "metadata": {},
        },
        {
            "id": "good",
            "source_type": "agent_trace",
            "source_id": "line:2",
            "rating": 5,
            "comment": "正常输出",
            "tags": ["useful"],
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
            "export-feedback-candidates",
            "--feedback-file",
            str(feedback_path),
            "--output",
            str(output_path),
            "--max-rating",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "FEEDBACK CANDIDATES EXPORTED" in output
    assert "CANDIDATE COUNT: 1" in output

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["count"] == 1
    assert saved["candidates"][0]["source_feedback_id"] == "bad"


def test_export_feedback_candidates_command_can_filter_by_tag(
    monkeypatch,
    capsys,
    tmp_path,
):
    feedback_path = tmp_path / "feedback.jsonl"
    output_path = tmp_path / "candidates.json"
    records = [
        {
            "id": "tagged",
            "source_type": "defense_task",
            "source_id": "task-1",
            "rating": 5,
            "comment": "适合做评估样本",
            "tags": ["needs_benchmark"],
            "metadata": {},
        }
    ]
    feedback_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-feedback-candidates",
            "--feedback-file",
            str(feedback_path),
            "--output",
            str(output_path),
            "--max-rating",
            "2",
            "--tag",
            "needs_benchmark",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "CANDIDATE COUNT: 1" in output
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["candidates"][0]["source_feedback_id"] == "tagged"
