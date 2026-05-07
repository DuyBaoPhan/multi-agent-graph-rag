# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

#### `GET /health`
System-wide health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "neo4j": "healthy",
    "redis": "healthy",
    "sglang_router": "healthy",
    "sglang_generator": "healthy",
    "tei": "healthy"
  }
}
```

#### `GET /health/{service}`
Individual service health check.

---

### Chat

#### `POST /api/v1/chat`
Send a chat message (non-streaming).

**Request:**
```json
{
  "message": "Cho tôi một ly Phin Sữa Đá size L",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "reply": "Vâng, 1 ly Phin Sữa Đá size L giá 39.000đ. Bạn muốn order luôn không?",
  "session_id": "uuid-session-id",
  "intent": "order",
  "agent": "order_agent",
  "cached": false
}
```

#### `POST /api/v1/chat/stream`
Send a chat message with SSE streaming response.

**Request:** Same as `/chat`

**Response:** Server-Sent Events stream
```
data: {"token": "Vâng"}
data: {"token": ", "}
data: {"token": "1 ly"}
...
data: [DONE]
```

---

### Ingestion

#### `POST /api/v1/ingest/menu`
Upload CSV menu file.

#### `POST /api/v1/ingest/faq`
Upload CSV FAQ file.

#### `POST /api/v1/ingest/document`
Upload PDF/DOCX document for semantic chunking.
