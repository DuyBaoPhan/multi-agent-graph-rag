"""
Model Export Script
=====================
Export fine-tuned models to AWQ and GGUF formats (Module A1.3).
"""

from loguru import logger


def export_awq(model_path: str, output_path: str):
    """Export model to AWQ format for SGLang serving."""
    # TODO: Use autoawq library for quantization
    logger.info(f"Exporting AWQ: {model_path} → {output_path}")


def export_gguf(model_path: str, output_path: str, quant_type: str = "Q4_K_M"):
    """Export model to GGUF format for edge deployment."""
    # TODO: Use llama.cpp convert script
    logger.info(f"Exporting GGUF ({quant_type}): {model_path} → {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python export_model.py <model_path> <output_path> [awq|gguf]")
        sys.exit(1)
