# ☕ Highlands Coffee Multi-Agent Robot

> Production-ready Multi-Agent LLM System with Graph RAG for Highlands Coffee

## 🏗️ Architecture

```
User → FastAPI Gateway → Intent Router → Agent Dispatcher
                                              ├── Order Agent    → Neo4j Menu
                                              ├── FAQ Agent      → Graph RAG
                                              └── Consultant Agent → Both
```

## 📁 Project Structure

```
multi-agent-graph-rag/
├── src/
│   ├── gateway/           # FastAPI API gateway
│   │   ├── routes/        # API endpoints (chat, health, ingest)
│   │   └── middleware/    # Rate limiter, etc.
│   ├── router/            # A1: Intent classification (Qwen2.5-1.5B)
│   ├── agents/            # A2: Multi-agent framework
│   ├── graph_rag/         # B1: Graph RAG with Neo4j
│   │   └── ingestion/    # Data parsers (CSV, PDF, DOCX)
│   ├── llm_serving/       # B2: SGLang dual-model serving
│   │   └── cache/        # Multi-layer caching
│   ├── semantic_cache/    # C2: SLM intent extraction + cache
│   └── guardrails/        # C3: TTS, validation, fallback
├── scripts/               # Training & data generation scripts
├── data/                  # Training data, raw data, models
├── configs/               # Neo4j, SGLang, Redis configs
├── tests/                 # Unit & integration tests
├── docs/                  # Architecture & API docs
├── docker-compose.yml     # Full stack orchestration
├── Dockerfile             # FastAPI gateway container
├── requirements.txt       # Python dependencies
└── TODO.md                # Development todolist
```

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd multi-agent-graph-rag

# 2. Create environment
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your settings

# 4. Start services
docker compose up -d

# 5. Run gateway (development)
uvicorn src.gateway.main:app --reload --port 8000
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_router.py -v
pytest tests/test_graph_rag.py -v
pytest tests/test_agents.py -v
```

## 📊 Performance Targets

| Metric              | Target        |
|----------------------|---------------|
| Router accuracy      | ≥ 92%         |
| Router latency       | ≤ 200ms       |
| TTFT                 | ≤ 0.2s        |
| RAG top-5 precision  | ≥ 80%         |
| Cache hit response   | ≤ 100ms       |
| GPU VRAM budget      | ≤ 12GB        |

## 📋 Development Progress

See [TODO.md](TODO.md) for detailed development todolist.

## 📄 License

Private - Highlands Coffee AI Engineer Assessment
