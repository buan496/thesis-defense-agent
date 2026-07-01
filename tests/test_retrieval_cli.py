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
                    "search_queries": ["系统架构", "特征处理"],
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
            "use_model_reranker": kwargs["use_model_reranker"],
            "model_rerank_candidate_multiplier": (
                kwargs["model_rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "use_llm_query_rewrite": kwargs["use_llm_query_rewrite"],
            "use_multi_query": kwargs["use_multi_query"],
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
            "--multi-query",
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
    assert captured["use_model_reranker"] is False
    assert captured["model_rerank_candidate_multiplier"] == 3
    assert captured["use_query_rewrite"] is True
    assert captured["use_llm_query_rewrite"] is False
    assert captured["use_multi_query"] is True
    assert "RETRIEVER: hybrid" in output
    assert "VECTOR WEIGHT: 0.6" in output
    assert "BM25 WEIGHT: 0.4" in output
    assert "USE RERANKER: True" in output
    assert "USE MODEL RERANKER: False" in output
    assert "USE QUERY REWRITE: True" in output
    assert "USE LLM QUERY REWRITE: False" in output
    assert "USE MULTI QUERY: True" in output
    assert "SEARCH QUERIES: ['系统架构', '特征处理']" in output
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
            "use_model_reranker": kwargs["use_model_reranker"],
            "model_rerank_candidate_multiplier": (
                kwargs["model_rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "use_llm_query_rewrite": kwargs["use_llm_query_rewrite"],
            "use_multi_query": kwargs["use_multi_query"],
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
                            "search_queries": ["系统架构", "特征处理"],
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
                            "search_queries": ["系统架构", "特征处理"],
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
            "--multi-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["vector_weight"] == 0.6
    assert captured["bm25_weight"] == 0.4
    assert captured["use_reranker"] is True
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["use_model_reranker"] is False
    assert captured["model_rerank_candidate_multiplier"] == 3
    assert captured["use_query_rewrite"] is True
    assert captured["use_llm_query_rewrite"] is False
    assert captured["use_multi_query"] is True
    assert "RETRIEVER COMPARISON" in output
    assert "BEST RETRIEVER: hybrid" in output
    assert "USE RERANKER: True" in output
    assert "USE MODEL RERANKER: False" in output
    assert "USE QUERY REWRITE: True" in output
    assert "USE LLM QUERY REWRITE: False" in output
    assert "USE MULTI QUERY: True" in output
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
            "use_model_reranker": kwargs["use_model_reranker"],
            "model_rerank_candidate_multiplier": (
                kwargs["model_rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "use_llm_query_rewrite": kwargs["use_llm_query_rewrite"],
            "use_multi_query": kwargs["use_multi_query"],
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
            "--multi-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["weight_pairs"] == [(1.0, 0.0), (0.7, 0.3)]
    assert captured["use_reranker"] is True
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["use_model_reranker"] is False
    assert captured["model_rerank_candidate_multiplier"] == 3
    assert captured["use_query_rewrite"] is True
    assert captured["use_llm_query_rewrite"] is False
    assert captured["use_multi_query"] is True
    assert "HYBRID WEIGHT SCAN" in output
    assert "USE RERANKER: True" in output
    assert "USE MODEL RERANKER: False" in output
    assert "USE QUERY REWRITE: True" in output
    assert "USE LLM QUERY REWRITE: False" in output
    assert "USE MULTI QUERY: True" in output
    assert "BEST VECTOR WEIGHT: 0.7" in output
    assert "BEST BM25 WEIGHT: 0.3" in output
    assert "REPORT SAVED:" in output
    assert output_path.exists()


def test_compare_retrieval_strategies_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    captured = {}
    output_path = tmp_path / "strategies.json"

    def fake_compare_retrieval_strategies(**kwargs):
        captured.update(kwargs)
        return {
            "top_k": kwargs["top_k"],
            "retriever": "hybrid",
            "vector_weight": kwargs["vector_weight"],
            "bm25_weight": kwargs["bm25_weight"],
            "include_expensive": kwargs["include_expensive"],
            "best_strategy": "hybrid+multi_query",
            "best_average_score": 1.0,
            "reports": [
                {
                    "strategy_name": "hybrid",
                    "average_score": 0.8,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "system modules",
                            "missing": ["training"],
                        }
                    ],
                },
                {
                    "strategy_name": "hybrid+multi_query",
                    "average_score": 1.0,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "system modules",
                            "missing": [],
                        }
                    ],
                },
            ],
        }

    monkeypatch.setattr(
        cli,
        "compare_retrieval_strategies",
        fake_compare_retrieval_strategies,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-retrieval-strategies",
            "--top-k",
            "5",
            "--vector-weight",
            "0.6",
            "--bm25-weight",
            "0.4",
            "--rerank-candidate-multiplier",
            "2",
            "--model-rerank-candidate-multiplier",
            "4",
            "--include-expensive",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["vector_weight"] == 0.6
    assert captured["bm25_weight"] == 0.4
    assert captured["rerank_candidate_multiplier"] == 2
    assert captured["model_rerank_candidate_multiplier"] == 4
    assert captured["include_expensive"] is True
    assert "RETRIEVAL STRATEGY COMPARISON" in output
    assert "BEST STRATEGY: hybrid+multi_query" in output
    assert "STRATEGY: hybrid" in output
    assert "STRATEGY: hybrid+multi_query" in output
    assert "MISSING SUMMARY:" in output
    assert "REPORT SAVED:" in output
    assert output_path.exists()


def test_compare_vector_store_backends_command(
    monkeypatch,
    capsys,
    tmp_path,
):
    captured = {}
    output_path = tmp_path / "backend-comparison.json"

    def fake_compare_vector_store_repositories(**kwargs):
        captured.update(kwargs)
        return {
            "top_k": kwargs["top_k"],
            "best_repository": "qdrant",
            "score_delta_qdrant_minus_json": 0.0,
            "duration_delta_ms_qdrant_minus_json": 12.5,
            "reports": [
                {
                    "repository": "json",
                    "average_score": 1.0,
                    "average_duration_ms": 1.2,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "system modules",
                            "score": 1.0,
                            "duration_ms": 1.2,
                            "missing": [],
                        }
                    ],
                },
                {
                    "repository": "qdrant",
                    "average_score": 1.0,
                    "average_duration_ms": 13.7,
                    "embedding_cache": {
                        "hits": 1,
                        "misses": 0,
                    },
                    "results": [
                        {
                            "query": "system modules",
                            "score": 1.0,
                            "duration_ms": 13.7,
                            "missing": [],
                        }
                    ],
                },
            ],
        }

    monkeypatch.setattr(
        cli,
        "compare_vector_store_repositories",
        fake_compare_vector_store_repositories,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-vector-store-backends",
            "--top-k",
            "5",
            "--source",
            "data/vector_store.json",
            "--url",
            "http://127.0.0.1:6333",
            "--collection",
            "test_chunks",
            "--vector-size",
            "1024",
            "--distance",
            "Cosine",
            "--api-key",
            "secret",
            "--include-milvus",
            "--milvus-uri",
            "http://127.0.0.1:19530",
            "--milvus-collection",
            "milvus_chunks",
            "--milvus-vector-size",
            "1024",
            "--milvus-metric-type",
            "COSINE",
            "--milvus-token",
            "milvus-secret",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["top_k"] == 5
    assert captured["vector_store_path"] == "data/vector_store.json"
    assert captured["qdrant_url"] == "http://127.0.0.1:6333"
    assert captured["qdrant_collection"] == "test_chunks"
    assert captured["qdrant_vector_size"] == 1024
    assert captured["qdrant_distance"] == "Cosine"
    assert captured["qdrant_api_key"] == "secret"
    assert captured["include_milvus"] is True
    assert captured["milvus_uri"] == "http://127.0.0.1:19530"
    assert captured["milvus_collection"] == "milvus_chunks"
    assert captured["milvus_vector_size"] == 1024
    assert captured["milvus_metric_type"] == "COSINE"
    assert captured["milvus_token"] == "milvus-secret"
    assert "VECTOR STORE BACKEND COMPARISON" in output
    assert "BEST REPOSITORY: qdrant" in output
    assert "REPOSITORY: json" in output
    assert "REPOSITORY: qdrant" in output
    assert "REPORT SAVED:" in output
    assert output_path.exists()


def test_evaluate_rag_command_accepts_model_reranker_options(
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
                    "rewritten_query": "系统架构",
                    "search_queries": ["系统架构"],
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
            "use_model_reranker": kwargs["use_model_reranker"],
            "model_rerank_candidate_multiplier": (
                kwargs["model_rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "use_llm_query_rewrite": kwargs["use_llm_query_rewrite"],
            "use_multi_query": kwargs["use_multi_query"],
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
            "--model-rerank",
            "--model-rerank-candidate-multiplier",
            "4",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["use_model_reranker"] is True
    assert captured["model_rerank_candidate_multiplier"] == 4
    assert captured["use_reranker"] is False
    assert "USE MODEL RERANKER: True" in output
    assert "MODEL RERANK CANDIDATE MULTIPLIER: 4" in output


def test_evaluate_rag_command_accepts_llm_query_rewrite_option(
    monkeypatch,
    capsys,
):
    captured = {}

    def fake_evaluate_retrieval(**kwargs):
        captured.update(kwargs)
        return {
            "results": [
                {
                    "query": "系统怎么设计？",
                    "rewritten_query": "系统架构 特征处理 模型 训练",
                    "search_queries": ["系统架构 特征处理 模型 训练"],
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
            "use_model_reranker": kwargs["use_model_reranker"],
            "model_rerank_candidate_multiplier": (
                kwargs["model_rerank_candidate_multiplier"]
            ),
            "use_query_rewrite": kwargs["use_query_rewrite"],
            "use_llm_query_rewrite": kwargs["use_llm_query_rewrite"],
            "use_multi_query": kwargs["use_multi_query"],
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
            "--llm-rewrite-query",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert captured["use_llm_query_rewrite"] is True
    assert captured["use_query_rewrite"] is False
    assert "USE LLM QUERY REWRITE: True" in output
    assert "REWRITTEN QUERY: 系统架构 特征处理 模型 训练" in output
