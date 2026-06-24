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


def test_graph_interrupt_demo_command_without_answer(
    monkeypatch,
    capsys,
):
    captured = {}
    fake_graph = object()

    def fake_build_interrupt_demo_graph(**kwargs):
        captured["build"] = kwargs
        return fake_graph

    def fake_start_interrupt_demo(**kwargs):
        captured["start"] = kwargs
        return {
            "topic": kwargs["topic"],
            "__interrupt__": [
                type(
                    "FakeInterrupt",
                    (),
                    {
                        "value": {
                            "type": "answer_required",
                            "question": "How is the system designed?",
                            "message": "Please answer.",
                        }
                    },
                )()
            ],
        }

    monkeypatch.setattr(
        cli,
        "build_interrupt_demo_graph",
        fake_build_interrupt_demo_graph,
    )
    monkeypatch.setattr(
        cli,
        "start_interrupt_demo",
        fake_start_interrupt_demo,
    )
    monkeypatch.setattr(
        cli,
        "get_interrupt_payload",
        lambda result: result["__interrupt__"][0].value,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-interrupt-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["build"]["top_k"] == 2
    assert captured["start"]["graph"] is fake_graph
    assert captured["start"]["topic"] == "system architecture"
    assert captured["start"]["thread_id"] == "thread-1"
    assert "LANGGRAPH INTERRUPT DEMO" in output
    assert "INTERRUPTED: True" in output
    assert "INTERRUPT TYPE: answer_required" in output
    assert "QUESTION: How is the system designed?" in output
    assert "RESUMED: False" in output


def test_graph_interrupt_demo_command_with_answer(
    monkeypatch,
    capsys,
):
    captured = {}
    fake_graph = object()

    def fake_build_interrupt_demo_graph(**kwargs):
        return fake_graph

    def fake_start_interrupt_demo(**kwargs):
        return {
            "topic": kwargs["topic"],
            "__interrupt__": [
                type(
                    "FakeInterrupt",
                    (),
                    {
                        "value": {
                            "type": "answer_required",
                            "question": "How is the system designed?",
                            "message": "Please answer.",
                        }
                    },
                )()
            ],
        }

    def fake_resume_interrupt_demo(**kwargs):
        captured.update(kwargs)
        return {
            "status": "answer_received",
            "current_node": "answer_interrupt",
            "answer": kwargs["answer"],
        }

    monkeypatch.setattr(
        cli,
        "build_interrupt_demo_graph",
        fake_build_interrupt_demo_graph,
    )
    monkeypatch.setattr(
        cli,
        "start_interrupt_demo",
        fake_start_interrupt_demo,
    )
    monkeypatch.setattr(
        cli,
        "resume_interrupt_demo",
        fake_resume_interrupt_demo,
    )
    monkeypatch.setattr(
        cli,
        "get_interrupt_payload",
        lambda result: result["__interrupt__"][0].value,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-interrupt-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--answer",
            "The system is modular.",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["graph"] is fake_graph
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] == "The system is modular."
    assert "RESUMED: True" in output
    assert "STATUS: answer_received" in output
    assert "CURRENT NODE: answer_interrupt" in output
    assert "ANSWER: The system is modular." in output


def test_graph_interrupt_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_build_interrupt_demo_graph(**kwargs):
        raise ValueError("topic cannot be empty")

    monkeypatch.setattr(
        cli,
        "build_interrupt_demo_graph",
        fake_build_interrupt_demo_graph,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-interrupt-demo",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert "LANGGRAPH INTERRUPT ERROR: topic cannot be empty" in output
