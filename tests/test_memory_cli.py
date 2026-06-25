import json

from app import cli


def test_memory_show_command_displays_empty_memory(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-show",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MEMORY PATH:" in output
    assert "MEMORY JSON:" in output
    assert "MEMORY CONTEXT:" in output
    assert "<empty>" in output


def test_memory_set_profile_command_writes_profile_field(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-set-profile",
            "--key",
            "thesis_direction",
            "--value",
            "bilingual speech recognition",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert "MEMORY PROFILE UPDATED" in output
    assert "KEY: thesis_direction" in output
    assert "VALUE: bilingual speech recognition" in output
    assert memory["profile"]["thesis_direction"] == (
        "bilingual speech recognition"
    )


def test_memory_set_profile_command_rejects_empty_value(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-set-profile",
            "--key",
            "thesis_direction",
            "--value",
            "   ",
            "--path",
            str(tmp_path / "memory.json"),
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("empty profile value should fail")

    output = capsys.readouterr().out

    assert "ARGUMENT ERROR: --value cannot be empty" in output


def test_memory_add_weakness_command_appends_weakness(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-add-weakness",
            "--text",
            "architecture answers need module examples",
            "--task-id",
            "task-001",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert "MEMORY WEAKNESS ADDED" in output
    assert "architecture answers need module examples" in output
    assert memory["weaknesses"][0]["weakness"] == (
        "architecture answers need module examples"
    )
    assert memory["weaknesses"][0]["source_task_id"] == "task-001"


def test_memory_add_summary_command_appends_training_summary(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-add-summary",
            "--summary",
            "practice explaining module boundaries",
            "--task-id",
            "task-001",
            "--topic",
            "system architecture",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert "MEMORY SUMMARY ADDED" in output
    assert "practice explaining module boundaries" in output
    assert memory["training_summaries"][0]["summary"] == (
        "practice explaining module boundaries"
    )
    assert memory["training_summaries"][0]["task_id"] == "task-001"
    assert memory["training_summaries"][0]["topic"] == (
        "system architecture"
    )


def test_memory_show_command_displays_existing_memory_context(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-set-profile",
            "--key",
            "thesis_direction",
            "--value",
            "bilingual speech recognition",
            "--path",
            str(memory_path),
        ],
    )
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-show",
            "--path",
            str(memory_path),
        ],
    )
    cli.main()

    output = capsys.readouterr().out

    assert "Long-term memory:" in output
    assert "- thesis_direction: bilingual speech recognition" in output


def test_memory_prune_command_prunes_memory(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"

    commands = [
        [
            "app.cli",
            "memory-add-weakness",
            "--text",
            "old weakness",
            "--path",
            str(memory_path),
        ],
        [
            "app.cli",
            "memory-add-weakness",
            "--text",
            "recent weakness",
            "--path",
            str(memory_path),
        ],
        [
            "app.cli",
            "memory-add-summary",
            "--summary",
            "old summary",
            "--path",
            str(memory_path),
        ],
        [
            "app.cli",
            "memory-add-summary",
            "--summary",
            "recent summary",
            "--path",
            str(memory_path),
        ],
    ]

    for command in commands:
        monkeypatch.setattr("sys.argv", command)
        cli.main()
        capsys.readouterr()

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-prune",
            "--max-weaknesses",
            "1",
            "--max-summaries",
            "1",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert "MEMORY PRUNED" in output
    assert "WEAKNESSES: 2 -> 1" in output
    assert "SUMMARIES: 2 -> 1" in output
    assert memory["weaknesses"][0]["weakness"] == "recent weakness"
    assert memory["training_summaries"][0]["summary"] == "recent summary"


def test_memory_prune_command_rejects_negative_limits(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-prune",
            "--max-weaknesses",
            "-1",
            "--path",
            str(tmp_path / "memory.json"),
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("negative memory prune limit should fail")

    output = capsys.readouterr().out
    assert "ARGUMENT ERROR" in output
    assert "--max-weaknesses" in output


def test_memory_audit_command_outputs_clean_report(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"
    memory_path.write_text(
        json.dumps(
            {
                "profile": {"thesis_direction": "bilingual ASR"},
                "weaknesses": [{"weakness": "需要补充模块案例"}],
                "training_summaries": [{"summary": "练习系统架构"}],
                "metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-audit",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MEMORY AUDIT" in output
    assert "PASSED: True" in output
    assert "PROFILE COUNT: 1" in output
    assert "WEAKNESS COUNT: 1" in output
    assert "SUMMARY COUNT: 1" in output
    assert "ISSUE COUNT: 0" in output


def test_memory_audit_command_outputs_issue_report(
    monkeypatch,
    capsys,
    tmp_path,
):
    memory_path = tmp_path / "memory.json"
    memory_path.write_text(
        json.dumps(
            {
                "profile": {"thesis_direction": ""},
                "weaknesses": [
                    {"weakness": "需要补充模块案例"},
                    {"weakness": "需要补充模块案例"},
                ],
                "training_summaries": [
                    {"summary": ""},
                ],
                "metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "memory-audit",
            "--path",
            str(memory_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "MEMORY AUDIT" in output
    assert "PASSED: False" in output
    assert "DUPLICATE WEAKNESS COUNT: 1" in output
    assert "EMPTY PROFILE FIELD COUNT: 1" in output
    assert "EMPTY SUMMARY COUNT: 1" in output
    assert "ISSUE COUNT: 3" in output
    assert "Run memory-prune" in output
