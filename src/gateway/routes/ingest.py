"""
Ingestion Routes
==================
Endpoints for data ingestion into Graph RAG (Module B1.3).
"""

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/ingest/menu")
async def ingest_menu(file: UploadFile = File(...)):
    """Ingest CSV menu data into Neo4j."""
    # TODO: Parse CSV and create MenuItem nodes
    return {"status": "accepted", "filename": file.filename}


@router.post("/ingest/faq")
async def ingest_faq(file: UploadFile = File(...)):
    """Ingest CSV FAQ data into Neo4j."""
    # TODO: Parse CSV and create Chunk nodes with embeddings
    return {"status": "accepted", "filename": file.filename}


@router.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    """Ingest PDF/DOCX document with semantic chunking."""
    # TODO: Semantic chunking + entity extraction + graph insertion
    return {"status": "accepted", "filename": file.filename}
