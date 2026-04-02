import argparse
import sys
from pathlib import Path
import logging

from ..core.converter import ImageToPdfConverter


def setup_logging(verbose: bool):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main():
    parser = argparse.ArgumentParser(
        description="PDF Architect: Convert images to PDFs with batch processing and parallel conversion."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the folder containing images."
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory for PDFs (default: current directory)."
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["single", "batch"],
        default="single",
        help="Conversion mode: single PDF or batch PDFs (default: single)."
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=500,
        help="Number of images per PDF (batch mode only, default: 500)."
    )
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=5,
        help="Number of threads for parallel image conversion (default: 5)."
    )
    parser.add_argument(
        "--use-webp",
        action="store_true",
        help="Convert images to WEBP before PDF creation to save memory."
    )
    parser.add_argument(
        "--keep-webp",
        action="store_true",
        help="Keep intermediate WEBP files after PDF creation (only if --use-webp is set)."
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subfolders recursively (single mode only)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress logs."
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Validate input folder
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_dir():
        logging.error(f"Input folder does not exist: {args.input}")
        sys.exit(1)

    # Ensure output folder exists
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create converter
    converter = ImageToPdfConverter(
        input_folder=str(input_path),
        output_folder=str(output_path),
        batch_mode=(args.mode == "batch"),
        batch_size=args.batch_size,
        num_threads=args.threads,
        use_webp=args.use_webp,
        keep_webp=args.keep_webp,
        recursive=args.recursive,
        verbose=args.verbose
    )

    try:
        converter.run()
    except KeyboardInterrupt:
        logging.info("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()