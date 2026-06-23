from app import cli


def test_parse_weight_pairs():
    assert cli.parse_weight_pairs("1:0,0.7:0.3,0:1") == [
        (1.0, 0.0),
        (0.7, 0.3),
        (0.0, 1.0),
    ]


def test_evaluate_rag_command_accepts_retriever_options(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_evaluate_retrieval(**kwargs):
        captured.update(kwargs)
        return {
            "results": [
                {
                    "query": "系统架构",
                    "rewritten_query": "系统架构 特征处理",
                    "hit_count": 1,
                    "total": 1,
                    "missing": [],
                    "score": 1.0,
                }
            ],
            "top_k": kwargs["top_k"],
            "retriever": kwargs["retriever"],
            "vector_weight": kwargs["vector_weight"],
            "bm25_weight": kwargs["bm25_weight"],
            "use_reranker": kwargs["use_reranker"],
            "rerank_candidate_multiplier": (
                kwargs["rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "average_score": 1.0,
            "embedding_cache": {
                "hits": 0,
                "misses": 0,
            },
        }

    monkeypatch.setattr(
        cli,
        "evaluate_retrieval",
        fake_evaluate_retrieval,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "evaluate-rag",
            "--top-k",
            "5",
            "--retriever",
            "hybrid",
            "--vector-weight",
            "0.6",
            "--bm25-weight",
            "0.4",
            "--rerank",
            "--rerank-candidate-multiplier",
            "2",
            "--rewrite-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["retriever"] == "hybrid"
    assert captured["vector_weight"] == 0.6
    assert captured["bm25_weight"] == 0.4
    assert captured["use_reranker"] is True
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["use_query_rewrite"] is True
    assert "RETRIEVER: hybrid" in output
    assert "VECTOR WEIGHT: 0.6" in output
    assert "BM25 WEIGHT: 0.4" in output
    assert "USE RERANKER: True" in output
    assert "USE QUERY REWRITE: True" in output
    assert "REWRITTEN QUERY: 系统架构 特征处理" in output


def test_compare_retrievers_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    captured = {}
    output_path = tmp_path / "comparison.json"

    def fake_compare_retrievers(**kwargs):
        captured.update(kwargs)
        return {
            "top_k": kwargs["top_k"],
            "vector_weight": kwargs["vector_weight"],
            "bm25_weight": kwargs["bm25_weight"],
            "use_reranker": kwargs["use_reranker"],
            "rerank_candidate_multiplier": (
                kwargs["rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "best_retriever": "hybrid",
            "reports": [
                {
                    "retriever": "vector",
                    "average_score": 0.8,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "系统架构",
                            "rewritten_query": "系统架构 特征处理",
                            "score": 0.8,
                            "missing": ["训练模块"],
                        }
                    ],
                },
                {
                    "retriever": "hybrid",
                    "average_score": 1.0,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "系统架构",
                            "rewritten_query": "系统架构 特征处理",
                            "score": 1.0,
                            "missing": [],
                        }
                    ],
                },
            ],
        }

    monkeypatch.setattr(
        cli,
        "compare_retrievers",
        fake_compare_retrievers,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-retrievers",
            "--top-k",
            "5",
            "--vector-weight",
            "0.6",
            "--bm25-weight",
            "0.4",
            "--output",
            str(output_path),
            "--rerank",
            "--rerank-candidate-multiplier",
            "2",
            "--rewrite-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["vector_weight"] == 0.6
    assert captured["bm25_weight"] == 0.4
    assert captured["use_reranker"] is True
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["use_query_rewrite"] is True
    assert "RETRIEVER COMPARISON" in output
    assert "BEST RETRIEVER: hybrid" in output
    assert "USE RERANKER: True" in output
    assert "USE QUERY REWRITE: True" in output
    assert "RETRIEVER: vector" in output
    assert "RETRIEVER: hybrid" in output
    assert "REPORT SAVED:" in output
    assert output_path.exists()


def test_scan_hybrid_weights_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    captured = {}
    output_path = tmp_path / "scan.json"

    def fake_scan_hybrid_weights(**kwargs):
        captured.update(kwargs)
        return {
            "top_k": kwargs["top_k"],
            "best_vector_weight": 0.7,
            "best_bm25_weight": 0.3,
            "best_average_score": 1.0,
            "use_reranker": kwargs["use_reranker"],
            "rerank_candidate_multiplier": (
                kwargs["rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "reports": [
                {
                    "vector_weight": 1.0,
                    "bm25_weight": 0.0,
                    "average_score": 0.8,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                },
                {
                    "vector_weight": 0.7,
                    "bm25_weight": 0.3,
                    "average_score": 1.0,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                },
            ],
        }

    monkeypatch.setattr(
        cli,
        "scan_hybrid_weights",
        fake_scan_hybrid_weights,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "scan-hybrid-weights",
            "--top-k",
            "5",
            "--weights",
            "1:0,0.7:0.3",
            "--output",
            str(output_path),
            "--rerank",
            "--rerank-candidate-multiplier",
            "2",
            "--rewrite-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["weight_pairs"] == [(1.0, 0.0), (0.7, 0.3)]
    assert captured["use_reranker"] is True
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["use_query_rewrite"] is True
    assert "HYBRID WEIGHT SCAN" in output
    assert "USE RERANKER: True" in output
    assert "USE QUERY REWRITE: True" in output
    assert "BEST VECTOR WEIGHT: 0.7" in output
    assert "BEST BM25 WEIGHT: 0.3" in output
    assert "REPORT SAVED:" in output
    assert output_path.exists()
