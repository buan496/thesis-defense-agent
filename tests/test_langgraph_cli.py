from app import cli


def test_graph_demo_task_command(monkeypatch, capsys):
    captured = {}

    def fake_run_demo_task(**kwargs):
        captured.update(kwargs)
        return {
            "topic": kwargs["topic"],
            "status": "waiting_for_answer",
            "current_node": "wait_for_answer",
            "needs_human_input": True,
            "query": kwargs["topic"],
            "sources": [
                {
                    "id": 1,
                    "source": "test",
                    "score": 0.9,
                }
            ],
            "question": "How is the system architecture designed?",
        }

    monkeypatch.setattr(cli, "run_demo_task", fake_run_demo_task)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-demo-task",
            "--topic",
            "system architecture",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["topic"] == "system architecture"
    assert captured["top_k"] == 2
    assert "LANGGRAPH DEMO TASK" in output
    assert "STATUS: waiting_for_answer" in output
    assert "CURRENT NODE: wait_for_answer" in output
    assert "NEEDS HUMAN INPUT: True" in output
    assert "SOURCE COUNT: 1" in output
    assert "QUESTION: How is the system architecture designed?" in output


def test_graph_demo_task_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_demo_task(**kwargs):
        raise ValueError("topic cannot be empty")

    monkeypatch.setattr(cli, "run_demo_task", fake_run_demo_task)
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-demo-task",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert "LANGGRAPH DEMO ERROR: topic cannot be empty" in output
