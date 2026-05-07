"""
PDF/DOCX Parser
=================
Parse PDF and DOCX documents for ingestion (Module B1.3).
"""

from pathlib import Path

from loguru import logger


def parse_pdf(filepath: str | Path) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        filepath: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    from pypdf import PdfReader

    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"PDF not found: {filepath}")
        return ""

    reader = PdfReader(str(filepath))
    text_parts = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            text_parts.append(text)

    full_text = "\n\n".join(text_parts)
    logger.info(f"Extracted {len(full_text)} chars from {filepath.name} ({len(reader.pages)} pages)")
    return full_text


def parse_docx(filepath: str | Path) -> str:
    """
    Extract text content from a DOCX file.
    
    Args:
        filepath: Path to the DOCX file
        
    Returns:
        Extracted text content
    """
    from docx import Document

    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"DOCX not found: {filepath}")
        return ""

    doc = Document(str(filepath))
    text_parts = [para.text for para in doc.paragraphs if para.text.strip()]

    full_text = "\n\n".join(text_parts)
    logger.info(f"Extracted {len(full_text)} chars from {filepath.name}")
    return full_text
