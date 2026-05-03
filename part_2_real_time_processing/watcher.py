"""
Real-time Folder Monitor — Part 2
Watches input_zone/ and triggers the pipeline the moment a supported file lands.

Run standalone:  python watcher.py
(The Airflow DAG polls on a schedule; this script reacts instantly via OS events.)

NOTE: Do not run this alongside the Airflow DAG simultaneously — both watch the
same input_zone/ and will race to process the same file.
"""
import os
import sys
import time
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from watchdog.observers import Observer  # type: ignore
from watchdog.events import FileSystemEventHandler  # type: ignore
from pipeline.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

_IN_FLIGHT: set[str] = set()
_WATCH_DIR = Config.INPUT_DIR


class PipelineTrigger(FileSystemEventHandler):
    """Fires the full pipeline when a supported file appears in input_zone/."""

    def on_created(self, event):
        if not event.is_directory:
            self._maybe_process(event.src_path)

    def on_moved(self, event):
        # Only handle files moved INTO input_zone/ (e.g. saved by some editors).
        # Ignore archive moves (Airflow moving files OUT to input_zone/archived/).
        if not event.is_directory:
            dest = Path(event.dest_path)
            if dest.parent.resolve() == _WATCH_DIR.resolve():
                self._maybe_process(event.dest_path)

    def _maybe_process(self, file_path: str) -> None:
        ext = Path(file_path).suffix.lower()
        if ext not in Config.SUPPORTED_EXTENSIONS:
            logging.info(f"Ignored (unsupported type): {Path(file_path).name}")
            return
        if file_path in _IN_FLIGHT:
            return

        _IN_FLIGHT.add(file_path)
        file_name = Path(file_path).name
        logging.info(f">>> NEW FILE DETECTED: {file_name} — starting pipeline <<<")

        # Small delay so the OS finishes writing before we read
        time.sleep(1)

        # Guard: file may have been archived by Airflow during the sleep
        if not Path(file_path).exists():
            logging.warning(
                f"File '{file_name}' is no longer in input_zone — "
                "it was likely processed and archived by the Airflow DAG. Skipping."
            )
            _IN_FLIGHT.discard(file_path)
            return

        try:
            from main import run_pipeline
            run_pipeline(file_name)
        except Exception as exc:
            logging.error(f"Pipeline FAILED for {file_name}: {exc}")
        finally:
            _IN_FLIGHT.discard(file_path)


if __name__ == "__main__":
    _WATCH_DIR.mkdir(parents=True, exist_ok=True)

    logging.info("=" * 55)
    logging.info("  REAL-TIME PIPELINE MONITOR STARTED")
    logging.info(f"  Watching: {_WATCH_DIR}")
    logging.info(f"  Supported types: {', '.join(Config.SUPPORTED_EXTENSIONS)}")
    logging.info("  Drop a file into the folder to trigger the pipeline.")
    logging.info("  Press Ctrl+C to stop.")
    logging.info("=" * 55 + "\n")

    handler = PipelineTrigger()
    observer = Observer()
    observer.schedule(handler, path=str(_WATCH_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Monitor stopped cleanly.")
    observer.join()
