import json

import pytest

from app import cli


def test_export_benchmark_draft_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    candidate_path = tmp_path / "candidates.json"
    output_path = tmp_path / "draft.json"
    candidate_report = {
        "candidates": [
            {
                "candidate_id": "feedback-1",
                "status": "accepted",
                "source_feedback_id": "1",
                "source_type": "agent_trace",
                "source_id": "line:1",
                "comment": "工具选错",
                "tags": ["routing_error"],
                "metadata": {},
                "review": {"reviewer": "buan496"},
            },
            {
                "candidate_id": "feedback-2",
                "status": "needs_review",
                "source_feedback_id": "2",
                "source_type": "agent_trace",
                "source_id": "line:2",
                "comment": "待复核",
                "tags": [],
                "metadata": {},
            },
        ]
    }
    candidate_path.write_text(
        json.dumps(candidate_report, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-benchmark-draft",
            "--candidate-file",
            str(candidate_path),
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "BENCHMARK DRAFT EXPORTED" in output
    assert "DRAFT COUNT: 1" in output

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["count"] == 1
    assert saved["items"][0]["source_candidate_id"] == "feedback-1"


def test_export_benchmark_draft_command_handles_missing_file(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-benchmark-draft",
            "--candidate-file",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "draft.json"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "BENCHMARK DRAFT ERROR" in output
