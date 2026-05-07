"""
Knowledge Store
==================
In-memory knowledge base loaded from CSV files.
Provides search for menu items and FAQ — used by all agents.
Works as standalone replacement for Neo4j in dev mode.
"""

import csv
import re
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class FAQEntry:
    question: str
    answer: str
    category: str
    embedding: np.ndarray | None = None


@dataclass
class MenuItem:
    name: str
    price: int
    size: str
    category: str
    description: str
    embedding: np.ndarray | None = None


class KnowledgeStore:
    """In-memory knowledge base for menu and FAQ data."""

    def __init__(self):
        self.menu_items: list[MenuItem] = []
        self.faq_entries: list[FAQEntry] = []
        self._menu_by_name: dict[str, list[MenuItem]] = {}
        self._menu_by_category: dict[str, list[MenuItem]] = {}
        self._embedder = None

    def load_from_csv(
        self,
        menu_path: str = "data/raw/menu/highlands_menu.csv",
        faq_path: str = "data/raw/faq/highlands_faq.csv",
    ):
        """Load menu and FAQ data from CSV files."""
        # Load menu
        mp = Path(menu_path)
        if mp.exists():
            with open(mp, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item = MenuItem(
                        name=row.get("name", "").strip(),
                        price=int(row.get("price", 0)),
                        size=row.get("size", "").strip(),
                        category=row.get("category", "").strip(),
                        description=row.get("description", "").strip(),
                    )
                    self.menu_items.append(item)

                    # Index by name
                    key = item.name.lower()
                    self._menu_by_name.setdefault(key, []).append(item)
                    # Index by category
                    self._menu_by_category.setdefault(item.category, []).append(item)

            logger.info(f"Loaded {len(self.menu_items)} menu items from {mp.name}")
        else:
            logger.warning(f"Menu file not found: {mp}")

        # Load FAQ
        fp = Path(faq_path)
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = FAQEntry(
                        question=row.get("question", "").strip(),
                        answer=row.get("answer", "").strip(),
                        category=row.get("category", "").strip(),
                    )
                    self.faq_entries.append(entry)
            logger.info(f"Loaded {len(self.faq_entries)} FAQ entries from {fp.name}")
        else:
            logger.warning(f"FAQ file not found: {fp}")

        # Initialize embedder and generate embeddings
        self._init_embeddings()

    def _init_embeddings(self):
        """Initialize SentenceTransformer and encode knowledge."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing SentenceTransformer (all-MiniLM-L6-v2)...")
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Encode Menu
            menu_texts = [f"{item.name} {item.category} {item.description}" for item in self.menu_items]
            if menu_texts:
                embeddings = self._embedder.encode(menu_texts, show_progress_bar=False)
                for item, emb in zip(self.menu_items, embeddings):
                    item.embedding = emb
            
            # Encode FAQ
            faq_texts = [f"{entry.question} {entry.answer}" for entry in self.faq_entries]
            if faq_texts:
                embeddings = self._embedder.encode(faq_texts, show_progress_bar=False)
                for entry, emb in zip(self.faq_entries, embeddings):
                    entry.embedding = emb
            
            logger.info("✅ Knowledge embeddings generated successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings: {e}. Falling back to keyword search only.")
            self._embedder = None

    # ── Menu Search ──────────────────────────────────────────

    def get_item_by_name(self, name: str) -> MenuItem | None:
        """Find a menu item by exact name (case-insensitive)."""
        name_lower = name.lower()
        for item in self.menu_items:
            if item.name.lower() == name_lower:
                return item
        return None

    def search_menu(self, query: str, top_k: int = 5) -> list[MenuItem]:
        """Search menu items by keyword matching."""
        query_lower = query.lower()
        scored: list[tuple[int, MenuItem]] = []

        for item in self.menu_items:
            score = 0
            name_lower = item.name.lower()
            desc_lower = item.description.lower()
            cat_lower = item.category.lower()

            # Exact name match
            if name_lower in query_lower or query_lower in name_lower:
                score += 10
            # Word-level match
            for word in query_lower.split():
                if len(word) < 2:
                    continue
                if word in name_lower:
                    score += 5
                if word in desc_lower:
                    score += 2
                if word in cat_lower:
                    score += 3

            # Price queries
            if re.search(r"(rẻ|giá|tiền|bao nhiêu)", query_lower):
                score += 1
            if re.search(r"(rẻ|rẻ nhất|dưới)", query_lower) and item.price <= 35000:
                score += 3

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def get_menu_by_category(self, category: str) -> list[MenuItem]:
        """Get all items in a category."""
        return self._menu_by_category.get(category, [])

    def get_all_categories(self) -> list[str]:
        """Get all menu categories."""
        return list(self._menu_by_category.keys())

    def get_cheapest(self, n: int = 5) -> list[MenuItem]:
        """Get cheapest menu items."""
        unique = {}
        for item in self.menu_items:
            if item.name not in unique or item.price < unique[item.name].price:
                unique[item.name] = item
        return sorted(unique.values(), key=lambda x: x.price)[:n]

    def format_menu_items(self, items: list[MenuItem]) -> str:
        """Format menu items as readable text for LLM context."""
        if not items:
            return "Không tìm thấy món phù hợp."
        lines = []
        seen = set()
        for item in items:
            key = f"{item.name}-{item.size}"
            if key in seen:
                continue
            seen.add(key)
            size_str = f" size {item.size}" if item.size else ""
            lines.append(f"- {item.name}{size_str}: {item.price:,}đ — {item.description}")
        return "\n".join(lines)

    # ── FAQ Search ───────────────────────────────────────────

    def search_faq(self, query: str, top_k: int = 3) -> list[FAQEntry]:
        """Search FAQ entries by keyword matching."""
        query_lower = query.lower()
        scored: list[tuple[int, FAQEntry]] = []

        for entry in self.faq_entries:
            score = 0
            q_lower = entry.question.lower()
            a_lower = entry.answer.lower()

            for word in query_lower.split():
                if len(word) < 2:
                    continue
                if word in q_lower:
                    score += 5
                if word in a_lower:
                    score += 2

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def format_faq_entries(self, entries: list[FAQEntry]) -> str:
        """Format FAQ entries as readable text for LLM context."""
        if not entries:
            return "Không tìm thấy thông tin liên quan."
        lines = []
        for entry in entries:
            lines.append(f"Q: {entry.question}\nA: {entry.answer}")
        return "\n\n".join(lines)

    # ── Hybrid Search ──────────────────────────────────────────

    def search_hybrid(self, query: str, domain: str = "faq", top_k: int = 5) -> list:
        """
        Hybrid search combining Keyword and Vector similarity.
        Implements Dual-Domain Search and Late Reranking (lite version).
        """
        if domain == "menu":
            candidates = self.menu_items
            kw_search = self.search_menu
        else:
            candidates = self.faq_entries
            kw_search = self.search_faq

        # 1. Keyword Search
        kw_results = kw_search(query, top_k=top_k * 2)
        kw_map = {id(item): (len(kw_results) - i) / len(kw_results) for i, item in enumerate(kw_results)}

        # 2. Vector Search (if available)
        vec_map = {}
        if self._embedder and candidates:
            query_emb = self._embedder.encode(query, show_progress_bar=False)
            
            vec_scores = []
            for item in candidates:
                if item.embedding is not None:
                    # Cosine similarity
                    score = np.dot(query_emb, item.embedding) / (np.linalg.norm(query_emb) * np.linalg.norm(item.embedding))
                    vec_scores.append((score, item))
            
            vec_scores.sort(key=lambda x: x[0], reverse=True)
            top_vec = vec_scores[:top_k * 2]
            vec_map = {id(item): score for score, item in top_vec}

        # 3. Reciprocal Rank Fusion / Weighted Sum
        final_scored = []
        all_candidate_items = {id(item): item for item in candidates}
        unique_ids = set(kw_map.keys()) | set(vec_map.keys())

        for uid in unique_ids:
            score = (kw_map.get(uid, 0) * 0.4) + (vec_map.get(uid, 0) * 0.6)
            final_scored.append((score, all_candidate_items[uid]))

        # 4. Late Reranking (lite: boost exact matches)
        query_lower = query.lower()
        reranked = []
        for score, item in final_scored:
            text = (item.name if hasattr(item, "name") else item.question).lower()
            if query_lower in text:
                score += 0.2  # Exact match boost
            reranked.append((score, item))

        reranked.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in reranked[:top_k]]

    def expand_graph(self, items: list) -> list:
        """
        Lite Graph Expansion: Add items from same category or linked entities.
        """
        if not items: return []
        
        expanded = list(items)
        categories = set()
        for item in items:
            categories.add(item.category)
        
        # Add 1-2 more items from the same categories if not already present
        for cat in categories:
            cat_items = self.get_menu_by_category(cat)
            count = 0
            for ci in cat_items:
                if ci not in expanded:
                    expanded.append(ci)
                    count += 1
                if count >= 2: break
                
        return expanded


# Singleton
_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    """Get or create the global KnowledgeStore singleton."""
    global _store
    if _store is None:
        _store = KnowledgeStore()
        _store.load_from_csv()
    return _store
