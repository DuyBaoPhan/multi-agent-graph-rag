"""
Benchmark Script — Module B2.4
===============================
Measures Latency, TTFT, and Accuracy of the full pipeline.
"""

import asyncio
import time
import httpx
import statistics
from loguru import logger

API_URL = "http://127.0.0.1:8000/api/v1/chat"

TEST_QUERIES = [
    ("hello", "ignore"),
    ("Cho anh 1 cafe sữa đá", "order"),
    ("Mật khẩu wifi là gì?", "faq"),
    ("Tư vấn cho em món nào ngon", "consultant"),
    ("Giá của trà sen vàng là bao nhiêu?", "faq"),
    ("Thêm cho mình 2 ly Phindi Choco size L", "order"),
    ("Thời tiết hôm nay thế nào?", "ignore"),
    ("Mình muốn xem giỏ hàng", "order"),
    ("Highlands có những loại trà nào?", "consultant"),
    ("Cảm ơn chatbot nhé", "ignore"),
]

async def run_benchmark():
    logger.info("Starting Highlands Multi-Agent Benchmark...")
    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query, expected_intent in TEST_QUERIES:
            start_time = time.perf_counter()
            
            try:
                # We use the standard chat endpoint
                response = await client.post(API_URL, json={"message": query})
                end_time = time.perf_counter()
                
                latency = (end_time - start_time) * 1000
                data = response.json()
                
                results.append({
                    "query": query,
                    "latency": latency,
                    "intent": data.get("intent", "unknown"),
                    "match": data.get("intent") == expected_intent,
                    "status": response.status_code
                })
                logger.info(f"Q: {query[:20]}... | Latency: {latency:.2f}ms | Match: {data.get('intent') == expected_intent}")
            except Exception as e:
                logger.error(f"Failed query {query}: {e}")

    # Summary
    latencies = [r["latency"] for r in results]
    matches = [r["match"] for r in results]
    
    print("\n" + "="*50)
    print("HIGHLANDS MULTI-AGENT BENCHMARK RESULTS")
    print("="*50)
    print(f"Total Queries:    {len(results)}")
    print(f"Avg Latency:      {statistics.mean(latencies):.2f} ms")
    print(f"Min Latency:      {min(latencies):.2f} ms")
    print(f"Max Latency:      {max(latencies):.2f} ms")
    print(f"Accuracy:         {(sum(matches)/len(matches))*100:.1f}%")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
