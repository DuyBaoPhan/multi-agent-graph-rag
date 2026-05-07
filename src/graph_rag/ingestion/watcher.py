"""
File Watcher
==============
Watch directories for new files and auto-ingest (Module B1.3).
"""

from pathlib import Path

from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class IngestionHandler(FileSystemEventHandler):
    """Handle new file events and trigger ingestion pipeline."""

    def __init__(self, ingest_callback):
        self.ingest_callback = ingest_callback

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        suffix = filepath.suffix.lower()

        if suffix in {".csv", ".pdf", ".docx"}:
            logger.info(f"New file detected: {filepath.name}")
            # TODO: Call ingest_callback async
            self.ingest_callback(filepath)


def start_watcher(watch_dir: str, ingest_callback) -> Observer:
    """
    Start watching a directory for new files.
    
    Args:
        watch_dir: Directory path to watch
        ingest_callback: Function to call when new file detected
        
    Returns:
        Observer instance (call .stop() to end)
    """
    observer = Observer()
    handler = IngestionHandler(ingest_callback)
    observer.schedule(handler, watch_dir, recursive=True)
    observer.start()
    logger.info(f"👀 Watching directory: {watch_dir}")
    return observer
