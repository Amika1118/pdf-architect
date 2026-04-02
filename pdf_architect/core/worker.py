import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from PIL import Image

from .utils import ensure_rgb_for_pdf


logger = logging.getLogger(__name__)


class ConversionWorker:
    """Handles parallel image conversion to WEBP."""

    def __init__(self, num_threads: int):
        self.num_threads = num_threads
        self.lock = threading.Lock()
        self._status = [{'id': i, 'current_file': None, 'status': 'idle', 'progress': 0}
                        for i in range(num_threads)]

    def update_status(self, thread_id: int, filename: Optional[str] = None,
                      status: str = 'idle', progress: int = 0):
        with self.lock:
            self._status[thread_id]['current_file'] = filename
            self._status[thread_id]['status'] = status
            self._status[thread_id]['progress'] = progress

    def convert_single(self, thread_id: int, src_path: Path, webp_path: Path, filename: str) -> Tuple[str, bool, str]:
        """Convert one image to WEBP. Returns (filename, success, webp_filename_or_error)."""
        self.update_status(thread_id, filename, 'processing', 0)
        try:
            # Step 1: Verify original
            self.update_status(thread_id, filename, 'processing', 25)
            with Image.open(src_path) as img:
                img.verify()

            # Step 2: Convert
            self.update_status(thread_id, filename, 'processing', 50)
            with Image.open(src_path) as img:
                # Convert to RGB or RGBA as needed
                if img.mode == 'P' and 'transparency' in img.info:
                    img = img.convert("RGBA")
                elif img.mode in ("RGBA", "LA"):
                    img = img.convert("RGBA")
                elif img.mode in ("P", "L", "1"):
                    img = img.convert("RGB")
                else:
                    img = img.convert("RGB")
                # Save as WEBP
                img.save(webp_path, "WEBP", quality=95, method=6)

            # Step 3: Verify WEBP
            self.update_status(thread_id, filename, 'processing', 75)
            with Image.open(webp_path) as img:
                img.verify()

            self.update_status(thread_id, filename, 'completed', 100)
            return filename, True, webp_path.name

        except Exception as e:
            logger.error(f"Failed to convert {filename}: {e}")
            self.update_status(thread_id, filename, 'failed', 0)
            if webp_path.exists():
                try:
                    webp_path.unlink()
                except:
                    pass
            return filename, False, str(e)

    def process_batch(self, image_files: list, output_folder: Path) -> Tuple[list, list]:
        """
        Convert images to WEBP in parallel.
        Returns (list of WEBP filenames, list of failed filenames).
        """
        tasks = []
        for src_path in image_files:
            webp_name = src_path.stem + ".webp"
            webp_path = output_folder / webp_name
            if webp_path.exists():
                logger.info(f"WEBP already exists for {src_path.name}, skipping conversion")
                continue
            tasks.append((src_path, webp_path, src_path.name))

        if not tasks:
            return [], []

        total = len(tasks)
        completed = 0
        successful = []
        failed = []

        # Reset status
        for i in range(self.num_threads):
            self.update_status(i, None, 'idle', 0)

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_task = {}
            task_index = 0
            # Submit initial tasks
            for thread_id in range(min(self.num_threads, total)):
                src, webp, name = tasks[task_index]
                future = executor.submit(self.convert_single, thread_id, src, webp, name)
                future_to_task[future] = (thread_id, src, webp, name)
                task_index += 1

            while completed < total:
                for future in as_completed(future_to_task):
                    thread_id, src, webp, name = future_to_task[future]
                    try:
                        fname, success, data = future.result()
                        completed += 1
                        if success:
                            successful.append(data)  # webp filename
                        else:
                            failed.append(fname)
                            logger.warning(f"Failed to convert {fname}: {data}")
                        # Submit next task if any
                        if task_index < total:
                            next_src, next_webp, next_name = tasks[task_index]
                            new_future = executor.submit(self.convert_single, thread_id, next_src, next_webp, next_name)
                            future_to_task[new_future] = (thread_id, next_src, next_webp, next_name)
                            task_index += 1
                        else:
                            self.update_status(thread_id, None, 'idle', 0)
                        del future_to_task[future]
                    except Exception as e:
                        logger.exception(f"Task error: {e}")
                        completed += 1
                        failed.append(name)
                        # Still try to submit next
                        if task_index < total:
                            next_src, next_webp, next_name = tasks[task_index]
                            new_future = executor.submit(self.convert_single, thread_id, next_src, next_webp, next_name)
                            future_to_task[new_future] = (thread_id, next_src, next_webp, next_name)
                            task_index += 1
                        del future_to_task[future]

        return successful, failed