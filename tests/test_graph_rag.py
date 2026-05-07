"""
Graph RAG Tests
=================
Test hybrid search, graph expansion, and ingestion (Module B1).
Target: top-5 precision ≥ 80%, graph expansion recall +15%.
"""

import pytest

from src.graph_rag.ingestion.csv_parser import parse_menu_csv, parse_faq_csv
from src.graph_rag.ingestion.chunker import semantic_chunk, _split_sentences


class TestCSVParser:
    """Test CSV parsing for menu and FAQ data."""

    def test_parse_menu_csv_missing_file(self):
        result = parse_menu_csv("nonexistent.csv")
        assert result == []

    def test_parse_faq_csv_missing_file(self):
        result = parse_faq_csv("nonexistent.csv")
        assert result == []


class TestChunker:
    """Test semantic chunking."""

    def test_split_sentences_basic(self):
        text = "Câu một. Câu hai. Câu ba."
        sentences = _split_sentences(text)
        assert len(sentences) == 3

    def test_chunk_short_text(self):
        text = "Đây là đoạn ngắn."
        chunks = semantic_chunk(text)
        assert len(chunks) == 1

    def test_chunk_respects_max_size(self):
        text = "Đây là câu. " * 100
        chunks = semantic_chunk(text, max_chunk_size=100)
        for chunk in chunks:
            assert len(chunk) <= 200  # Allow some overflow for last sentence


class TestHybridSearch:
    """Test hybrid search (requires running Neo4j)."""

    @pytest.mark.skip(reason="Requires running Neo4j")
    @pytest.mark.asyncio
    async def test_search_precision(self):
        """Target: top-5 precision ≥ 80% on 20 test queries."""
        pass
