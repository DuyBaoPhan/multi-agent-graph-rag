# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                       │
│   /chat  /chat/stream  /ingest  /health                 │
│   [Rate Limiter] [Input Validator] [Fallback]           │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Intent Router     │
              │  (Qwen2.5-1.5B AWQ) │
              │   SGLang ~1.1GB     │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌─────▼─────┐   ┌─────▼──────┐
    │  Order  │    │    FAQ    │   │ Consultant │
    │  Agent  │    │   Agent   │   │   Agent    │
    └────┬────┘    └─────┬─────┘   └─────┬──────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────▼──────────┐
              │   Graph RAG (B1)    │
              │   Hybrid Search     │
              │   Graph Expansion   │
              │   BGE Reranker      │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌─────▼─────┐   ┌─────▼──────┐
    │  Neo4j  │    │    TEI    │   │   SGLang   │
    │  Graph  │    │ Embedding │   │ Generator  │
    │   DB    │    │  Server   │   │  ~4.8GB    │
    └─────────┘    └───────────┘   └────────────┘
```

## Data Flow

1. User sends query → FastAPI Gateway
2. Gateway validates input → Router classifies intent
3. Router dispatches to correct Agent
4. Agent queries Neo4j via Graph RAG pipeline
5. Context + query sent to Generator LLM
6. Response streamed back via SSE

## VRAM Budget (RTX 3060 12GB)

| Component          | VRAM   |
|--------------------|--------|
| Router AWQ         | ~1.1GB |
| Generator AWQ      | ~4.8GB |
| KV Cache           | ~3.0GB |
| TEI Embedding      | ~1.0GB |
| Overhead           | ~2.1GB |
| **Total**          | **12GB** |
