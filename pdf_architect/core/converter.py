import logging
import traceback
from pathlib import Path
from typing import List
from datetime import datetime
from tqdm import tqdm

from PIL import Image

from .utils import get_image_files, natural_sort_key, ensure_rgb_for_pdf
from .worker import ConversionWorker


logger = logging.getLogger(__name__)


class ImageToPdfConverter:
    """
    Main class for converting images to PDFs with optional WEBP intermediate.
    """

    def __init__(
        self,
        input_folder: str,
        output_folder: str = ".",
        batch_mode: bool = False,
        batch_size: int = 500,
        num_threads: int = 5,
        use_webp: bool = False,
        keep_webp: bool = False,
        recursive: bool = False,
        verbose: bool = False,
    ):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.batch_mode = batch_mode
        self.batch_size = batch_size
        self.num_threads = num_threads
        self.use_webp = use_webp
        self.keep_webp = keep_webp
        self.recursive = recursive
        self.verbose = verbose

        self.worker = ConversionWorker(num_threads) if use_webp else None
        self.webp_temp_folder = None

    def _setup_temp_folder(self):
        if self.use_webp and not self.webp_temp_folder:
            self.webp_temp_folder = self.output_folder / ".pdf_architect_temp"
            self.webp_temp_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Temporary WEBP folder: {self.webp_temp_folder}")

    def _cleanup_temp_folder(self):
        if self.webp_temp_folder and self.webp_temp_folder.exists() and not self.keep_webp:
            for f in self.webp_temp_folder.glob("*.webp"):
                try:
                    f.unlink()
                    logger.debug(f"Deleted {f.name}")
                except Exception as e:
                    logger.warning(f"Could not delete {f.name}: {e}")
            try:
                self.webp_temp_folder.rmdir()
            except:
                pass

    def _collect_images(self) -> List[Path]:
        images = sorted(
            get_image_files(self.input_folder, self.recursive),
            key=lambda p: natural_sort_key(p.name)
        )
        logger.info(f"Found {len(images)} images.")
        return images

    def _convert_to_webp(self, images: List[Path]) -> List[Path]:
        self._setup_temp_folder()
        successful, failed = self.worker.process_batch(images, self.webp_temp_folder)
        if failed:
            logger.warning(f"Failed to convert {len(failed)} images: {', '.join(failed[:5])}...")
        return [self.webp_temp_folder / fname for fname in successful]

    def _create_pdf_from_images(self, image_paths: List[Path], pdf_name: str) -> bool:
        if not image_paths:
            logger.error("No images to create PDF.")
            return False

        logger.info(f"Creating PDF {pdf_name} with {len(image_paths)} images...")
        images = []
        for img_path in tqdm(image_paths, desc="Loading images", disable=not self.verbose):
            try:
                with Image.open(img_path) as img:
                    img = ensure_rgb_for_pdf(img)
                    images.append(img)
            except Exception as e:
                logger.error(f"Failed to load {img_path.name}: {e}")

        if not images:
            logger.error("No valid images to create PDF.")
            return False

        # Debug: print image modes
        if self.verbose:
            for i, img in enumerate(images[:5]):
                logger.debug(f"Image {i}: mode={img.mode}, size={img.size}")

        pdf_path = self.output_folder / pdf_name
        try:
            # Try saving without metadata (most compatible)
            images[0].save(
                pdf_path,
                save_all=True,
                append_images=images[1:],
                optimize=True,
            )
            logger.info(f"PDF created: {pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            if self.verbose:
                traceback.print_exc()
            # Fallback: try saving without optimization
            try:
                logger.info("Retrying without optimization...")
                images[0].save(
                    pdf_path,
                    save_all=True,
                    append_images=images[1:],
                )
                logger.info(f"PDF created (fallback): {pdf_path}")
                return True
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                if self.verbose:
                    traceback.print_exc()
                return False
        finally:
            for img in images:
                try:
                    img.close()
                except:
                    pass

    def run(self):
        start_time = datetime.now()
        logger.info(f"PDF Architect started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Input folder: {self.input_folder}")
        logger.info(f"Output folder: {self.output_folder}")
        logger.info(f"Mode: {'batch' if self.batch_mode else 'single'}")
        if self.batch_mode:
            logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Use WEBP: {self.use_webp} (keep: {self.keep_webp})")
        logger.info(f"Recursive: {self.recursive}")
        logger.info(f"Threads: {self.num_threads}")

        images = self._collect_images()
        if not images:
            logger.error("No images found.")
            return

        if self.use_webp:
            logger.info(f"Converting {len(images)} images to WEBP using {self.num_threads} threads...")
            images = self._convert_to_webp(images)
            if not images:
                logger.error("No images successfully converted.")
                return

        if self.batch_mode:
            total_batches = (len(images) + self.batch_size - 1) // self.batch_size
            for i in range(total_batches):
                start = i * self.batch_size
                end = min(start + self.batch_size, len(images))
                batch = images[start:end]
                pdf_name = f"batch_{i+1:03d}.pdf"
                logger.info(f"Processing batch {i+1}/{total_batches} ({len(batch)} images)")
                self._create_pdf_from_images(batch, pdf_name)
        else:
            pdf_name = f"{self.input_folder.name}.pdf"
            self._create_pdf_from_images(images, pdf_name)

        if self.use_webp and not self.keep_webp:
            self._cleanup_temp_folder()

        elapsed = datetime.now() - start_time
        logger.info(f"Completed in {elapsed.total_seconds():.1f} seconds.")