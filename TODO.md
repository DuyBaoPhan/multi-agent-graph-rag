# 🚀 Highlands Coffee Multi-Agent Robot — Development Todolist

> **Tổng thời gian:** 20 ngày | **Target:** ≥ 75% điểm để pass AI Engineer
>
> **Thứ tự ưu tiên:** A1 Router → B1 Graph RAG → B2 LLM Serving → A2 Multi-Agent → C2 Semantic Cache → C1/C3

---

## Giai đoạn 0 — Chuẩn bị (Ngày 1)

> **⚠️ IMPORTANT:** Nền tảng cho toàn bộ hệ thống. Phải hoàn thành trước khi bắt đầu bất kỳ module nào.

- [ ] **Khởi tạo Git repo** với `.gitignore`, `README.md`, cấu trúc thư mục chuẩn
- [ ] **Tạo `docker-compose.yml`** với các services:
  - [ ] Neo4j (graph database)
  - [ ] Redis (session cache)
  - [ ] SGLang server (LLM serving)
  - [ ] FastAPI gateway (API endpoint)
- [ ] **Cấu hình networks & volumes** cho Docker Compose
- [ ] **Thiết lập environment variables** (`.env` file)
- [ ] **Tạo virtual environment** Python + `requirements.txt`

### ✅ Tiêu chí hoàn thành

```
docker compose up → Toàn bộ stack khởi động không lỗi
```

---

## Giai đoạn 1 — Data Generation & Router (Ngày 2–4) | Module A1 — 20% điểm

### Bước 1.1 — Data Pipeline (A1.2)

- [ ] Viết script gọi LLM API (Claude/GPT) sinh **4000 samples**
  - [ ] 1000 samples intent `order`
  - [ ] 1000 samples intent `faq`
  - [ ] 1000 samples intent `consultant`
  - [ ] 1000 samples intent `chitchat`
- [ ] Tạo **200–800 hard samples** (ví dụ: "Có gì vừa ngon vừa rẻ không?")
- [ ] Gán nhãn rõ ràng cho mọi sample
- [ ] Implement **checkpoint/resume** để tránh mất dữ liệu khi bị ngắt
- [ ] Chia dataset: train/val/test split
- [ ] Validate chất lượng data (kiểm tra label distribution, duplicate)

### Bước 1.2 — Fine-tune SFT (A1.3)

- [ ] Setup tài khoản **Modal/RunPod H100**
- [ ] Chuẩn bị training config cho **Qwen2.5-1.5B** với **LoRA/QLoRA**
- [ ] Train model, target **accuracy ≥ 92%** trên test set
- [ ] Evaluate: confusion matrix, per-class F1 score
- [ ] Export model **AWQ** (cho SGLang serving)
- [ ] Export model **GGUF Q4_K_M** (cho Edge bonus)

### Bước 1.3 — Serving Router (A1.1)

- [ ] Load model AWQ lên **SGLang** với:
  - [ ] `context-length=512`
  - [ ] VRAM budget **~1.1GB**
- [ ] Viết **prompt template** chặt chẽ → output JSON `{"action": "order"}`
- [ ] Xử lý edge cases: format sai, hallucination
- [ ] Tích hợp vào FastAPI endpoint

### ✅ Tiêu chí hoàn thành

```
20 câu test → Tất cả trả JSON đúng format, latency ≤ 200ms
```

---

## Giai đoạn 2 — Graph RAG (Ngày 5–8) | Module B1 — 25% điểm

> **⚠️ WARNING:** Phần phức tạp nhất về kiến trúc. Cần đầu tư thời gian kỹ lưỡng.

### Bước 2.1 — Neo4j Schema (B1.1)

- [ ] Tạo **3 node types:**
  - [ ] `MenuItem` (tên, giá, size, category)
  - [ ] `Chunk` (text đã chunk)
  - [ ] `Entity`
- [ ] Tạo **relationships:** `NEXT`, `MENTIONS`, `BELONGS_TO`
- [ ] Nhập **≥ 100 menu items** Highlands Coffee thực tế
- [ ] Viết Cypher queries test cho từng relationship

### Bước 2.2 — Vector Index + Hybrid Search (B1.2)

- [ ] Setup **TEI server** serve **Qwen3-Embedding-0.6B**
- [ ] Tạo **2 vector index** trong Neo4j
- [ ] Implement pipeline **3 bước:**
  - [ ] **Dual-Domain Search** (vector + keyword)
  - [ ] **Graph Expansion** (duyệt node NEXT/PREV)
  - [ ] **Late Reranking** với **BGE Reranker**
- [ ] Tune search parameters cho recall tối ưu

### Bước 2.3 — Ingestion Pipeline (B1.3)

- [ ] Viết **3 parser:**
  - [ ] CSV menu parser
  - [ ] CSV FAQ parser
  - [ ] PDF/DOCX parser
- [ ] Implement **semantic chunking** (gradient breakpoint ngữ nghĩa) cho PDF
- [ ] **Entity extraction** bằng LLM từ chunks
- [ ] Thêm **watch mode** auto-ingest file mới
- [ ] Error handling và logging cho pipeline

### ✅ Tiêu chí hoàn thành

```
20 câu hỏi test → top-5 precision ≥ 80%
Graph expansion tăng recall ≥ 15%
```

---

## Giai đoạn 3 — LLM Serving (Ngày 9–11) | Module B2 — 25% điểm

### Bước 3.1 — Dual-model SGLang (B2.1)

- [ ] Cấu hình SGLang chạy **2 model trên 1 GPU 12GB:**
  - [ ] Router AWQ **~1.1GB**
  - [ ] Generator Qwen2.5-7B AWQ **~4.8GB**
- [ ] Tune parameters:
  - [ ] `mem-fraction-static`
  - [ ] `chunked-prefill-size`
  - [ ] `max-running-requests`
- [ ] Đặt trong Docker Compose với **health check** + dependency order

### Bước 3.2 — SSE Streaming (B2.2)

- [ ] Implement FastAPI endpoint trả **SSE token-by-token**
- [ ] Xử lý `[DONE]` signal (KHÔNG `json.parse("[DONE]")`)
- [ ] (Optional) TTS: tách text tại `.?!;` gửi từng clause

### Bước 3.3 — Multi-layer Cache (B2.3)

- [ ] **Layer 1 — Disk:** model weights cache
- [ ] **Layer 2 — Neo4j:** embeddings sẵn
- [ ] **Layer 3 — VRAM:** KV cache (SGLang prefix sharing, `lpm` policy)
- [ ] **Layer 4 — Redis:** in-memory session cache
- [ ] (Bonus) **Semantic cache:** embedding similarity ≥ 0.95

### ✅ Tiêu chí hoàn thành

```
TTFT ≤ 0.2s
Query lần 2 nhanh hơn đáng kể (cache hit)
```

---

## Giai đoạn 4 — Multi-Agent Framework (Ngày 12–14) | Module A2 — 20% điểm

### Bước 4.1 — Agent Design (A2.1)

- [ ] Thiết kế **system prompt riêng** cho mỗi agent
- [ ] **Order Agent:** gọi Neo4j lấy menu, xử lý đặt hàng
- [ ] **FAQ Agent:** chạy Hybrid RAG pipeline (từ GĐ2)
- [ ] **Consultant Agent:** kết hợp Order + FAQ
- [ ] **Router dispatch:** nhận intent → dispatch đúng agent
- [ ] Viết **tool definitions** cho mỗi agent

### Bước 4.2 — SessionStore (A2.2)

- [ ] Implement Dict in-memory / Redis lưu history theo `session_id`
- [ ] Giữ **5 lượt gần nhất**
- [ ] Khi context vượt **70% window** → gọi LLM tóm tắt phần cũ
- [ ] **Cron job** mỗi 5 phút xóa session TTL > 30 phút

### Bước 4.3 — Request Queue (A2.3)

- [ ] `asyncio.Semaphore` giới hạn concurrent LLM calls (tránh OOM)
- [ ] **FIFO queue** với timeout 60s
- [ ] **Retry 3 lần** với exponential backoff cho external calls
- [ ] Error handling và graceful degradation

### ✅ Tiêu chí hoàn thành

```
5 turns liên tục → không mất context
3 requests đồng thời → không OOM
30 phút chạy liên tục → không deadlock
```

---

## Giai đoạn 5 — Semantic Cache & Guardrails (Ngày 15–17) | Module C — 25% điểm

> **💡 TIP:** Phần nhiều điểm nhất tính theo độ khó. Hoàn thành tốt sẽ tạo lợi thế lớn.

### Bước 5.1 — SLM Intent Extraction (C2.1)

- [ ] Tạo **dataset training** dạng structured output JSON
- [ ] Fine-tune **Qwen3-0.6B** tách câu thành 3 phần:
  - [ ] Chủ ngữ
  - [ ] Hành động (cache key)
  - [ ] Ngữ cảnh (gửi kèm agent)
- [ ] Target **accuracy ≥ 90%**

### Bước 5.2 — Cache Pipeline (C2.2)

- [ ] Extract hành động → embed
- [ ] Query **Qdrant/Redis** bằng cosine similarity **≥ 0.92**
- [ ] Nếu **HIT:** paraphrase template + ngữ cảnh → trả về **≤ 100ms** (không qua LLM)
- [ ] Nếu **MISS:** gửi agent → lưu vào cache
- [ ] Monitor cache hit rate

### Bước 5.3 — Guardrails (C3)

- [ ] **TTS preprocessing:** `49.000đ` → `"49k"`
- [ ] **Rate limiter** trên FastAPI
- [ ] **Fallback** khi generator quá tải
- [ ] **Health check endpoint** cho mỗi service
- [ ] Input validation và sanitization

### ✅ Tiêu chí hoàn thành

```
Cache hit → response ≤ 100ms không qua LLM
Guardrails chặn được input xấu
Health check trả đúng status cho mọi service
```

---

## Giai đoạn 6 — Benchmark & Nộp bài (Ngày 18–20)

### Benchmark (B2.4)

- [ ] Đo **TTFT thực tế** trên RTX 3060
- [ ] Đo **throughput** (tokens/s)
- [ ] Đo **total pipeline latency**
- [ ] Vẽ **confusion matrix** Router
- [ ] Tính **per-class F1** score
- [ ] Ghi kết quả vào **báo cáo PDF**

### Demo Video

- [ ] Quay video **≥ 60 giây**
- [ ] Thể hiện **≥ 3 agents** hoạt động
- [ ] Demo **multi-turn conversation:**
  - [ ] Hỏi FAQ → Đặt hàng → Hỏi tư vấn
- [ ] Show metrics (latency, accuracy)

### Edge Bonus (C1) — Nếu còn thời gian

- [ ] Export **GGUF** chạy trên Orange Pi
- [ ] Benchmark **Q4_0 vs Q4_K_M**
- [ ] Target **≤ 500ms** trên CPU ARM

---

## 📊 Tổng kết Module & Điểm số

| Module | Tên                 | Điểm | Giai đoạn | Ưu tiên          |
| ------ | ------------------- | ---- | --------- | ----------------- |
| A1     | Data Gen & Router   | 20%  | GĐ 1     | 🔴 Cao nhất      |
| B1     | Graph RAG           | 25%  | GĐ 2     | 🔴 Cao           |
| B2     | LLM Serving         | 25%  | GĐ 3     | 🟡 Trung bình    |
| A2     | Multi-Agent         | 20%  | GĐ 4     | 🟡 Trung bình    |
| C      | Cache & Guardrails  | 25%  | GĐ 5     | 🟢 Thấp hơn      |
| —      | Benchmark & Demo    | —    | GĐ 6     | 🔴 Bắt buộc      |

> **🚨 CAUTION:** Đường pass tối thiểu (75%): A1 + B1 + B2 + A2 = đủ điểm.
> Semantic Cache (C2) và Edge (C1) làm sau cùng nếu còn thời gian.
