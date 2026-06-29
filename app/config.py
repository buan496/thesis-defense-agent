import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL","deepseek-v4-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_INPUT_PRICE_PER_1M_TOKENS = float(
    os.getenv("LLM_INPUT_PRICE_PER_1M_TOKENS", "0")
)
LLM_OUTPUT_PRICE_PER_1M_TOKENS = float(
    os.getenv("LLM_OUTPUT_PRICE_PER_1M_TOKENS", "0")
)
LLM_PRICE_CURRENCY = os.getenv("LLM_PRICE_CURRENCY", "CNY")
TOOL_RESULT_MAX_CHARACTERS = int(
    os.getenv("TOOL_RESULT_MAX_CHARACTERS", "6000")
)
TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "2"))
TOOL_TIMEOUT_SECONDS = float(os.getenv("TOOL_TIMEOUT_SECONDS", "30"))
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")
DATABASE_URL = os.getenv("DATABASE_URL", "")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_BENCHMARK_PATH = os.getenv(
    "RAG_BENCHMARK_PATH",
    "data/rag_benchmark.json",
)
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
RAG_MIN_CHUNK_SIZE = int(os.getenv("RAG_MIN_CHUNK_SIZE", "30"))
RAG_VECTOR_STORE_PATH = os.getenv(
    "RAG_VECTOR_STORE_PATH", 
    "data/vector_store.json"
    )
RAG_VECTOR_STORE_META_PATH = os.getenv(
    "RAG_VECTOR_STORE_META_PATH",
    "data/vector_store_meta.json",
)
QUERY_EMBEDDING_CACHE_PATH = os.getenv(
    "QUERY_EMBEDDING_CACHE_PATH",
    "data/query_embedding_cache.json",
)
AGENT_TRACE_PATH = os.getenv(
    "AGENT_TRACE_PATH",
    "data/traces/agent_trace.jsonl",
)
SUB_AGENT_PLAN_TRACE_PATH = os.getenv(
    "SUB_AGENT_PLAN_TRACE_PATH",
    "data/traces/sub_agent_plan_trace.jsonl",
)
SUB_AGENT_EXECUTION_TRACE_PATH = os.getenv(
    "SUB_AGENT_EXECUTION_TRACE_PATH",
    "data/traces/sub_agent_execution_trace.jsonl",
)
LONG_TERM_MEMORY_PATH = os.getenv(
    "LONG_TERM_MEMORY_PATH",
    "data/long_term_memory.json",
)
AGENT_ROUTING_BENCHMARK_PATH = os.getenv(
    "AGENT_ROUTING_BENCHMARK_PATH",
    "data/agent_routing_benchmark.json",
)
FAITHFULNESS_BENCHMARK_PATH = os.getenv(
    "FAITHFULNESS_BENCHMARK_PATH",
    "data/faithfulness_benchmark.json",
)
FEEDBACK_STORE_PATH = os.getenv(
    "FEEDBACK_STORE_PATH",
    "data/feedback/feedback.jsonl",
)
BENCHMARK_CANDIDATE_DIRECTORY = os.getenv(
    "BENCHMARK_CANDIDATE_DIRECTORY",
    "data/benchmark_candidates",
)

if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is not set")
