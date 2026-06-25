import json

from app import cli


def write_jsonl(path, records):
    path.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in records
        ),
        encoding="utf-8",
    )


def test_trace_feedback_to_validated_benchmark_draft_flow(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "agent_trace.jsonl"
    feedback_path = tmp_path / "feedback.jsonl"
    candidate_path = tmp_path / "candidates.json"
    draft_path = tmp_path / "draft.json"
    export_directory = tmp_path / "exports"
    write_jsonl(
        trace_path,
        [
            {
                "created_at": "2026-06-25T10:00:00",
                "user_message": "系统架构有哪些模块？",
                "result": {
                    "final_output": "",
                    "tool_traces": [
                        {
                            "tool_name": "wrong_tool",
                            "success": False,
                            "duration_ms": 10,
                        },
                    ],
                },
            },
        ],
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "trace-feedback",
            "--file",
            str(trace_path),
            "--source-type",
            "agent",
            "--source-id",
            "agent-trace-line-1",
            "--feedback-file",
            str(feedback_path),
        ],
    )
    cli.main()

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-feedback-candidates",
            "--feedback-file",
            str(feedback_path),
            "--output",
            str(candidate_path),
        ],
    )
    cli.main()

    candidate_report = json.loads(
        candidate_path.read_text(encoding="utf-8")
    )
    candidate_id = candidate_report["candidates"][0]["candidate_id"]

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "review-benchmark-candidate",
            "--file",
            str(candidate_path),
            "--candidate-id",
            candidate_id,
            "--status",
            "accepted",
            "--reviewer",
            "buan496",
            "--reason",
            "适合作为 Agent 路由回归样本",
        ],
    )
    cli.main()

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-benchmark-draft",
            "--candidate-file",
            str(candidate_path),
            "--output",
            str(draft_path),
        ],
    )
    cli.main()

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    draft["items"][0]["benchmark_type"] = "agent_routing"
    draft["items"][0]["draft_fields"] = {
        "user_message": "系统架构有哪些模块？",
        "expected_tools": ["search_thesis"],
        "expected_arguments": {
            "search_thesis": {
                "required_keys": ["query"],
                "contains": {
                    "query": "系统架构",
                },
            },
        },
        "expected_answer_contains": ["特征处理模块"],
    }
    draft_path.write_text(
        json.dumps(draft, ensure_ascii=False),
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
    cli.main()

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "export-validated-benchmark-draft",
            "--draft-file",
            str(draft_path),
            "--output-directory",
            str(export_directory),
        ],
    )
    cli.main()

    output = capsys.readouterr().out
    exported_benchmark = json.loads(
        (export_directory / "agent_routing_benchmark_draft.json").read_text(
            encoding="utf-8",
        )
    )

    assert "TRACE FEEDBACK RECORDED" in output
    assert "FEEDBACK CANDIDATES EXPORTED" in output
    assert "BENCHMARK CANDIDATE REVIEWED" in output
    assert "BENCHMARK DRAFT EXPORTED" in output
    assert "BENCHMARK DRAFT VALIDATION" in output
    assert "PASSED: True" in output
    assert "VALIDATED BENCHMARK DRAFT EXPORTED" in output
    assert exported_benchmark == [
        {
            "user_message": "系统架构有哪些模块？",
            "expected_tools": ["search_thesis"],
            "argument_rules": [
                {
                    "tool_name": "search_thesis",
                    "required_keys": ["query"],
                    "contains": {
                        "query": "系统架构",
                    },
                }
            ],
            "completion_rules": {
                "non_empty": True,
                "required_keywords": ["特征处理模块"],
            },
        }
    ]
