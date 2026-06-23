import json

import pytest

from app import cli


def test_validate_benchmark_draft_command_passes(
    monkeypatch,
    capsys,
    tmp_path,
):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "draft_id": "draft-1",
                        "benchmark_type": "rag_retrieval",
                        "draft_fields": {
                            "query": "系统架构有哪些模块？",
                            "expected_keywords": ["特征处理模块"],
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "validate-benchmark-draft",
            "--file",
            str(draft_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "BENCHMARK DRAFT VALIDATION" in output
    assert "PASSED: True" in output
    assert "VALID COUNT: 1" in output


def test_validate_benchmark_draft_command_can_fail_on_error(
    monkeypatch,
    capsys,
    tmp_path,
):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "draft_id": "draft-1",
                        "benchmark_type": "rag_retrieval",
                        "draft_fields": {
                            "query": "",
                            "expected_keywords": [],
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "validate-benchmark-draft",
            "--file",
            str(draft_path),
            "--fail-on-error",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "PASSED: False" in output
    assert "field query must not be empty" in output


def test_validate_benchmark_draft_command_handles_missing_file(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "validate-benchmark-draft",
            "--file",
            str(tmp_path / "missing.json"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "BENCHMARK DRAFT VALIDATION ERROR" in output
