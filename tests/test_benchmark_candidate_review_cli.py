import json

import pytest

from app import cli


def write_candidate_report(path):
    report = {
        "count": 2,
        "candidates": [
            {
                "candidate_id": "feedback-1",
                "status": "needs_review",
                "comment": "工具选错了",
            },
            {
                "candidate_id": "feedback-2",
                "status": "rejected",
                "comment": "不适合",
            },
        ],
    }
    path.write_text(
        json.dumps(report, ensure_ascii=False),
        encoding="utf-8",
    )


def test_review_benchmark_candidate_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    candidate_path = tmp_path / "candidates.json"
    write_candidate_report(candidate_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "review-benchmark-candidate",
            "--file",
            str(candidate_path),
            "--candidate-id",
            "feedback-1",
            "--status",
            "accepted",
            "--reviewer",
            "buan496",
            "--reason",
            "适合作为工具路由回归样本",
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "BENCHMARK CANDIDATE REVIEWED" in output
    assert "CANDIDATE ID: feedback-1" in output
    assert "STATUS: accepted" in output

    saved = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = saved["candidates"][0]
    assert candidate["status"] == "accepted"
    assert candidate["review"]["reviewer"] == "buan496"
    assert candidate["review"]["reason"] == "适合作为工具路由回归样本"


def test_review_benchmark_candidate_command_handles_missing_candidate(
    monkeypatch,
    capsys,
    tmp_path,
):
    candidate_path = tmp_path / "candidates.json"
    write_candidate_report(candidate_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "review-benchmark-candidate",
            "--file",
            str(candidate_path),
            "--candidate-id",
            "missing",
            "--status",
            "accepted",
            "--reviewer",
            "buan496",
            "--reason",
            "不存在",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "BENCHMARK CANDIDATE REVIEW ERROR" in output
    assert "candidate not found" in output


def test_summarize_benchmark_candidates_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    candidate_path = tmp_path / "candidates.json"
    write_candidate_report(candidate_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "summarize-benchmark-candidates",
            "--file",
            str(candidate_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "BENCHMARK CANDIDATE SUMMARY" in output
    assert "COUNT: 2" in output
    assert "needs_review" in output
    assert "rejected" in output
