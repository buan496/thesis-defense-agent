from app import cli
from app.task_models import DefenseTask, TaskStep


def extract_value(
    output: str,
    prefix: str,
) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()

    raise AssertionError(f"没有找到输出字段：{prefix}")


def test_create_task_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "create-task",
            "--topic",
            "系统架构",
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "TASK CREATED" in output
    assert "TOPIC: 系统架构" in output
    assert "STATUS: created" in output

    task_id = extract_value(output, "TASK ID:")

    assert task_id
    assert (tmp_path / f"{task_id}.json").exists()


def test_task_cli_can_start_complete_and_show_task(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "create-task",
            "--topic",
            "系统架构",
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()
    create_output = capsys.readouterr().out
    task_id = extract_value(create_output, "TASK ID:")

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "start-task-step",
            "--task-id",
            task_id,
            "--input",
            '{"topic":"系统架构"}',
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()
    start_output = capsys.readouterr().out

    assert "TASK UPDATED" in start_output
    assert "STEP TYPE: retrieve_context" in start_output
    assert "STEP STATUS: pending" in start_output

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "complete-task-step",
            "--task-id",
            task_id,
            "--output",
            '{"context":"系统架构相关上下文"}',
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()
    complete_output = capsys.readouterr().out

    assert "TASK STEP COMPLETED" in complete_output
    assert "STEP TYPE: retrieve_context" in complete_output
    assert "STEP STATUS: completed" in complete_output

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "show-task",
            "--task-id",
            task_id,
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()
    show_output = capsys.readouterr().out

    assert "TASK" in show_output
    assert f"TASK ID: {task_id}" in show_output
    assert "TOPIC: 系统架构" in show_output
    assert "STATUS: running" in show_output
    assert "STEP COUNT: 1" in show_output
    assert "STEP TYPE: retrieve_context" in show_output
    assert "STEP STATUS: completed" in show_output


def test_start_task_step_command_blocks_when_current_step_pending(
    monkeypatch,
    capsys,
    tmp_path,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "create-task",
            "--topic",
            "系统架构",
            "--directory",
            str(tmp_path),
        ],
    )
    cli.main()
    task_id = extract_value(capsys.readouterr().out, "TASK ID:")

    for _ in range(2):
        monkeypatch.setattr(
            "sys.argv",
            [
                "app.cli",
                "start-task-step",
                "--task-id",
                task_id,
                "--directory",
                str(tmp_path),
            ],
        )
        cli.main()

    output = capsys.readouterr().out

    assert "STEP: None" in output
    assert "当前步骤尚未完成" in output


def test_start_task_step_rejects_invalid_json_input(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "start-task-step",
            "--task-id",
            "task-001",
            "--input",
            "not-json",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("非法 JSON 应该让 CLI 以状态码 2 退出")

    output = capsys.readouterr().out

    assert "ARGUMENT ERROR" in output
    assert "--input 必须是合法 JSON" in output


def test_complete_task_step_rejects_non_object_json_output(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "complete-task-step",
            "--task-id",
            "task-001",
            "--output",
            '["not", "object"]',
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("非对象 JSON 应该让 CLI 以状态码 2 退出")

    output = capsys.readouterr().out

    assert "ARGUMENT ERROR" in output
    assert "--output 必须是 JSON 对象" in output


def test_execute_task_step_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    task = DefenseTask(topic="系统架构", task_id="task-001")
    step = TaskStep(
        step_type="retrieve_context",
        input={
            "topic": "系统架构",
        },
    )
    step.mark_completed(
        output={
            "query": "系统架构",
            "context": "系统架构上下文",
            "sources": [
                {
                    "id": 0,
                    "source": "data/thesis.pdf",
                    "score": 0.9,
                },
            ],
        }
    )

    def fake_execute_current_task_step(
        task_id,
        directory,
    ):
        assert task_id == "task-001"
        assert directory == str(tmp_path)
        return task, step, tmp_path / "task-001.json"

    monkeypatch.setattr(
        cli,
        "execute_current_task_step",
        fake_execute_current_task_step,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "execute-task-step",
            "--task-id",
            "task-001",
            "--directory",
            str(tmp_path),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "TASK STEP EXECUTED" in output
    assert "TASK ID: task-001" in output
    assert "STEP TYPE: retrieve_context" in output
    assert "STEP STATUS: completed" in output
    assert "QUERY: 系统架构" in output
    assert "SOURCE COUNT: 1" in output


def test_execute_task_step_command_reports_task_error(
    monkeypatch,
    capsys,
):
    def fake_execute_current_task_step(
        task_id,
        directory,
    ):
        raise ValueError("当前任务没有可执行步骤")

    monkeypatch.setattr(
        cli,
        "execute_current_task_step",
        fake_execute_current_task_step,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "execute-task-step",
            "--task-id",
            "task-001",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("任务执行错误应该让 CLI 以状态码 1 退出")

    output = capsys.readouterr().out

    assert "TASK ERROR" in output
    assert "当前任务没有可执行步骤" in output
