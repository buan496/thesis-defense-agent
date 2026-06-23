import json

import pytest

from app import cli


def test_export_validated_benchmark_draft_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    draft_path = tmp_path / "draft.json"
    output_directory = tmp_path / "exports"
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
            "export-validated-benchmark-draft",
            "--draft-file",
            str(draft_path),
            "--output-directory",
            str(output_directory),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "VALIDATED BENCHMARK DRAFT EXPORTED" in output
    assert "rag_retrieval" in output

    exported = json.loads(
        (output_directory / "rag_benchmark_draft.json").read_text(
            encoding="utf-8"
        )
    )
    assert exported == [
        {
            "query": "系统架构有哪些模块？",
            "expected_keywords": ["特征处理模块"],
        }
    ]


def test_export_validated_benchmark_draft_command_rejects_invalid_draft(
    monkeypatch,
    capsys,
    tmp_path,
):
    draft_path = tmp_path / "draft.json"
    output_directory = tmp_path / "exports"
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
            "export-validated-benchmark-draft",
            "--draft-file",
            str(draft_path),
            "--output-directory",
            str(output_directory),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "VALIDATED BENCHMARK EXPORT ERROR" in output
