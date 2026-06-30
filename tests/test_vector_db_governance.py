import pytest

from app import cli
from app.vector_db_governance import (
    build_vector_db_governance_report,
    render_vector_db_governance_report,
)


def test_build_vector_db_governance_report_includes_json_qdrant_and_milvus():
    report = build_vector_db_governance_report()

    assert report.current_backend == "json"
    assert report.target_backend == "qdrant"
    assert [candidate.name for candidate in report.candidates] == [
        "json",
        "qdrant",
        "milvus",
    ]
    assert any("quality gate" in gate for gate in report.promotion_gates)
    assert any("snapshot" in step for step in report.recommended_next_steps)


def test_build_vector_db_governance_report_can_exclude_milvus():
    report = build_vector_db_governance_report(include_milvus=False)

    assert [candidate.name for candidate in report.candidates] == [
        "json",
        "qdrant",
    ]


def test_build_vector_db_governance_report_supports_milvus_target():
    report = build_vector_db_governance_report(target_backend="milvus")

    assert report.target_backend == "milvus"
    assert any("MilvusVectorStoreRepository" in step for step in report.recommended_next_steps)
    assert any(candidate.name == "milvus" for candidate in report.candidates)


def test_build_vector_db_governance_report_rejects_invalid_backends():
    with pytest.raises(ValueError, match="current_backend"):
        build_vector_db_governance_report(current_backend="unknown")

    with pytest.raises(ValueError, match="target_backend"):
        build_vector_db_governance_report(target_backend="json")


def test_render_vector_db_governance_report_outputs_markdown():
    report = build_vector_db_governance_report()
    rendered = render_vector_db_governance_report(report)

    assert "# Vector DB Governance Report" in rendered
    assert "- Current backend: `json`" in rendered
    assert "- Target backend: `qdrant`" in rendered
    assert "### qdrant" in rendered
    assert "## Promotion Gates" in rendered
    assert "## Recommended Next Steps" in rendered


def test_vector_db_governance_report_cli_prints_report(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "vector-db-governance-report",
            "--current-backend",
            "json",
            "--target-backend",
            "qdrant",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "# Vector DB Governance Report" in output
    assert "### qdrant" in output
    assert "### milvus" in output
    assert "quality gate" in output


def test_vector_db_governance_report_cli_can_write_markdown(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "vector-db-governance.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "vector-db-governance-report",
            "--exclude-milvus",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved = output_path.read_text(encoding="utf-8")

    assert "OUTPUT:" in output
    assert str(output_path) in output
    assert "### qdrant" in saved
    assert "### milvus" not in saved


def test_vector_db_governance_report_cli_rejects_invalid_current_backend(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "vector-db-governance-report",
            "--current-backend",
            "unknown",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 2
    assert "VECTOR DB GOVERNANCE ERROR:" in output
    assert "current_backend" in output
