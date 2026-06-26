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


def test_graph_checkpointer_demo_command_without_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_checkpointer_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "checkpointer_type": "InMemorySaver",
            "interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system designed?",
            },
            "interrupted_checkpoint": {
                "checkpoint_id": "checkpoint-1",
                "next": ["answer_interrupt"],
                "has_pending_interrupt": True,
                "values": {
                    "topic": kwargs["topic"],
                    "question": "How is the system designed?",
                },
            },
            "resumed_result": None,
            "resumed_checkpoint": None,
        }

    monkeypatch.setattr(
        cli,
        "run_checkpointer_demo",
        fake_run_checkpointer_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-checkpointer-demo",
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

    assert captured["topic"] == "system architecture"
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] is None
    assert captured["top_k"] == 2
    assert "LANGGRAPH CHECKPOINTER DEMO" in output
    assert "CHECKPOINTER TYPE: InMemorySaver" in output
    assert "INTERRUPTED CHECKPOINT ID: checkpoint-1" in output
    assert "INTERRUPTED NEXT: ['answer_interrupt']" in output
    assert "INTERRUPTED HAS PENDING INTERRUPT: True" in output
    assert "RESUMED: False" in output


def test_graph_checkpointer_demo_command_with_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_checkpointer_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "checkpointer_type": "InMemorySaver",
            "interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system designed?",
            },
            "interrupted_checkpoint": {
                "checkpoint_id": "checkpoint-1",
                "next": ["answer_interrupt"],
                "has_pending_interrupt": True,
                "values": {
                    "topic": kwargs["topic"],
                    "question": "How is the system designed?",
                },
            },
            "resumed_result": {
                "answer": kwargs["answer"],
            },
            "resumed_checkpoint": {
                "checkpoint_id": "checkpoint-2",
                "next": [],
                "has_pending_interrupt": False,
                "values": {
                    "topic": kwargs["topic"],
                    "question": "How is the system designed?",
                    "answer": kwargs["answer"],
                },
            },
        }

    monkeypatch.setattr(
        cli,
        "run_checkpointer_demo",
        fake_run_checkpointer_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-checkpointer-demo",
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

    assert captured["answer"] == "The system is modular."
    assert "RESUMED: True" in output
    assert "RESUMED CHECKPOINT ID: checkpoint-2" in output
    assert "RESUMED NEXT: []" in output
    assert "RESUMED HAS PENDING INTERRUPT: False" in output
    assert "ANSWER: The system is modular." in output


def test_graph_checkpointer_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_checkpointer_demo(**kwargs):
        raise ValueError("thread_id cannot be empty")

    monkeypatch.setattr(
        cli,
        "run_checkpointer_demo",
        fake_run_checkpointer_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-checkpointer-demo",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert "LANGGRAPH CHECKPOINTER ERROR: thread_id cannot be empty" in output


def test_graph_persistent_checkpoint_demo_command(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_persistent_checkpoint_demo(**kwargs):
        captured.update(kwargs)
        return {
            "snapshot_path": kwargs["output_path"],
            "summary": {
                "thread_id": kwargs["thread_id"],
                "checkpointer_type": "InMemorySaver",
                "interrupted_next": ["answer_interrupt"],
                "interrupted_has_pending_interrupt": True,
                "interrupted_value_keys": [
                    "context",
                    "question",
                    "topic",
                ],
                "has_resumed": True,
                "resumed_next": [],
                "resumed_has_pending_interrupt": False,
                "resumed_value_keys": [
                    "answer",
                    "context",
                    "question",
                    "topic",
                ],
            },
        }

    monkeypatch.setattr(
        cli,
        "run_persistent_checkpoint_demo",
        fake_run_persistent_checkpoint_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-persistent-checkpoint-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--answer",
            "The system is modular.",
            "--output",
            "data/langgraph_checkpoints/thread-1.json",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["topic"] == "system architecture"
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] == "The system is modular."
    assert captured["output_path"] == (
        "data/langgraph_checkpoints/thread-1.json"
    )
    assert captured["top_k"] == 2
    assert "LANGGRAPH PERSISTENT CHECKPOINT DEMO" in output
    assert "SNAPSHOT PATH: data/langgraph_checkpoints/thread-1.json" in output
    assert "HAS RESUMED: True" in output
    assert "RESUMED NEXT: []" in output


def test_graph_persistent_checkpoint_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_persistent_checkpoint_demo(**kwargs):
        raise ValueError("thread_id cannot be empty")

    monkeypatch.setattr(
        cli,
        "run_persistent_checkpoint_demo",
        fake_run_persistent_checkpoint_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-persistent-checkpoint-demo",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert (
        "LANGGRAPH PERSISTENT CHECKPOINT ERROR: thread_id cannot be empty"
    ) in output


def test_graph_conditional_demo_command_with_existing_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_conditional_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "route": "finalize",
            "first_result": {
                "status": "completed",
                "current_node": "finalize",
                "question": "How is the system designed?",
            },
            "interrupt_payload": None,
            "resumed_result": None,
        }

    monkeypatch.setattr(
        cli,
        "run_conditional_demo",
        fake_run_conditional_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-conditional-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--answer",
            "The system is modular.",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["topic"] == "system architecture"
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] == "The system is modular."
    assert captured["resume_answer"] is None
    assert captured["top_k"] == 2
    assert "LANGGRAPH CONDITIONAL DEMO" in output
    assert "ROUTE: finalize" in output
    assert "INTERRUPTED: False" in output
    assert "RESUMED: False" in output


def test_graph_conditional_demo_command_with_resume_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_conditional_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "route": "answer_interrupt",
            "first_result": {
                "status": None,
                "current_node": None,
                "question": "How is the system designed?",
            },
            "interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system designed?",
            },
            "resumed_result": {
                "status": "completed",
                "current_node": "finalize",
                "answer": kwargs["resume_answer"],
            },
        }

    monkeypatch.setattr(
        cli,
        "run_conditional_demo",
        fake_run_conditional_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-conditional-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--resume-answer",
            "The system is modular.",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["answer"] is None
    assert captured["resume_answer"] == "The system is modular."
    assert "ROUTE: answer_interrupt" in output
    assert "INTERRUPTED: True" in output
    assert "INTERRUPT TYPE: answer_required" in output
    assert "RESUMED: True" in output
    assert "RESUMED STATUS: completed" in output
    assert "ANSWER: The system is modular." in output


def test_graph_conditional_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_conditional_demo(**kwargs):
        raise ValueError("answer cannot be empty")

    monkeypatch.setattr(
        cli,
        "run_conditional_demo",
        fake_run_conditional_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-conditional-demo",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert "LANGGRAPH CONDITIONAL ERROR: answer cannot be empty" in output


def test_graph_evaluate_rewrite_demo_command_with_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_evaluate_rewrite_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "interrupted_result": {
                "question": "How is the system architecture designed?",
            },
            "interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system architecture designed?",
            },
            "resumed_result": {
                "status": "answer_rewritten",
                "current_node": "rewrite_answer",
                "answer": kwargs["answer"],
                "evaluation": "Answer is too brief.",
                "rewritten_answer": (
                    "The architecture separates modules by responsibility."
                ),
            },
        }

    monkeypatch.setattr(
        cli,
        "run_evaluate_rewrite_demo",
        fake_run_evaluate_rewrite_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-evaluate-rewrite-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--answer",
            "It is modular.",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["topic"] == "system architecture"
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] == "It is modular."
    assert captured["top_k"] == 2
    assert "LANGGRAPH EVALUATE REWRITE DEMO" in output
    assert "INTERRUPTED: True" in output
    assert "RESUMED: True" in output
    assert "STATUS: answer_rewritten" in output
    assert "CURRENT NODE: rewrite_answer" in output
    assert "EVALUATION: Answer is too brief." in output
    assert (
        "REWRITTEN ANSWER: The architecture separates modules by responsibility."
    ) in output


def test_graph_evaluate_rewrite_demo_command_without_answer(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_evaluate_rewrite_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "interrupted_result": {
                "question": "How is the system architecture designed?",
            },
            "interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system architecture designed?",
            },
            "resumed_result": None,
        }

    monkeypatch.setattr(
        cli,
        "run_evaluate_rewrite_demo",
        fake_run_evaluate_rewrite_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-evaluate-rewrite-demo",
            "--topic",
            "system architecture",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["answer"] is None
    assert "LANGGRAPH EVALUATE REWRITE DEMO" in output
    assert "INTERRUPT TYPE: answer_required" in output
    assert "RESUMED: False" in output


def test_graph_evaluate_rewrite_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_evaluate_rewrite_demo(**kwargs):
        raise ValueError("topic cannot be empty")

    monkeypatch.setattr(
        cli,
        "run_evaluate_rewrite_demo",
        fake_run_evaluate_rewrite_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-evaluate-rewrite-demo",
            "--topic",
            "system architecture",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert "LANGGRAPH EVALUATE REWRITE ERROR: topic cannot be empty" in output


def test_graph_follow_up_demo_command_with_both_answers(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_follow_up_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "answer_interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system designed?",
            },
            "answer_result": {
                "answer": kwargs["answer"],
                "evaluation": "Answer is too brief.",
                "rewritten_answer": "The system separates modules.",
                "follow_up_question": "How are module boundaries defined?",
            },
            "follow_up_interrupt_payload": {
                "type": "follow_up_answer_required",
                "question": "How are module boundaries defined?",
            },
            "final_result": {
                "status": "follow_up_answer_evaluated",
                "current_node": "evaluate_follow_up_answer",
                "follow_up_answer": kwargs["follow_up_answer"],
                "follow_up_evaluation": "Follow-up answer is acceptable.",
            },
        }

    monkeypatch.setattr(
        cli,
        "run_follow_up_demo",
        fake_run_follow_up_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-follow-up-demo",
            "--topic",
            "system architecture",
            "--thread-id",
            "thread-1",
            "--answer",
            "It is modular.",
            "--follow-up-answer",
            "By responsibility.",
            "--top-k",
            "2",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["topic"] == "system architecture"
    assert captured["thread_id"] == "thread-1"
    assert captured["answer"] == "It is modular."
    assert captured["follow_up_answer"] == "By responsibility."
    assert captured["top_k"] == 2
    assert "LANGGRAPH FOLLOW UP DEMO" in output
    assert "ANSWER INTERRUPTED: True" in output
    assert "ANSWER RESUMED: True" in output
    assert "FOLLOW UP INTERRUPTED: True" in output
    assert "FOLLOW UP RESUMED: True" in output
    assert "CURRENT NODE: evaluate_follow_up_answer" in output
    assert "FOLLOW UP EVALUATION: Follow-up answer is acceptable." in output


def test_graph_follow_up_demo_command_without_answers(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_run_follow_up_demo(**kwargs):
        captured.update(kwargs)
        return {
            "thread_id": kwargs["thread_id"],
            "answer_interrupt_payload": {
                "type": "answer_required",
                "question": "How is the system designed?",
            },
            "answer_result": None,
            "follow_up_interrupt_payload": None,
            "final_result": None,
        }

    monkeypatch.setattr(
        cli,
        "run_follow_up_demo",
        fake_run_follow_up_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-follow-up-demo",
            "--topic",
            "system architecture",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["answer"] is None
    assert captured["follow_up_answer"] is None
    assert "ANSWER INTERRUPTED: True" in output
    assert "ANSWER RESUMED: False" in output
    assert "FOLLOW UP INTERRUPTED: False" in output
    assert "FOLLOW UP RESUMED: False" in output


def test_graph_follow_up_demo_command_reports_value_error(
    monkeypatch,
    capsys,
):
    def fake_run_follow_up_demo(**kwargs):
        raise ValueError("answer is required before follow_up_answer")

    monkeypatch.setattr(
        cli,
        "run_follow_up_demo",
        fake_run_follow_up_demo,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "graph-follow-up-demo",
            "--topic",
            "system architecture",
            "--follow-up-answer",
            "By responsibility.",
        ],
    )

    try:
        cli.main()
    except SystemExit as error:
        assert error.code == 1

    output = capsys.readouterr().out

    assert (
        "LANGGRAPH FOLLOW UP ERROR: answer is required before follow_up_answer"
    ) in output
