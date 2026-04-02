```markdown
# PDF Architect

A professional, multi-threaded tool to convert images to PDFs.  
Supports batch processing, WEBP intermediate conversion, and recursive folder scanning.

## Features
- Convert any image format (PNG, JPG, BMP, GIF, WEBP, etc.) to PDF.
- **Batch mode:** Split large sets of images into multiple PDFs of specified size.
- **Parallel conversion:** Convert images to WEBP using multiple threads for speed.
- **Single PDF mode:** Combine all images in a folder (and subfolders) into one PDF.
- **Smart sorting:** Natural numeric sorting (1, 2, 10, 11).
- **Memory efficient:** Handles large image collections without loading everything at once.
- **Cleanup:** Optionally delete temporary WEBP files after PDF creation.

## Installation

```bash
git clone https://github.com/yourusername/pdf_architect.git
cd pdf_architect
pip install -r requirements.txt
```

Optionally, install the package in editable mode to use the console script:
```bash
pip install -e .
```

## Usage

### Command Line Interface

```
python -m pdf_architect.cli.main --input <folder> [options]
```

#### Options

| Argument | Description |
|----------|-------------|
| `--input` | Path to the folder containing images (required). |
| `--output` | Output directory for PDFs (default: current directory). |
| `--mode` | `batch` (create multiple PDFs) or `single` (one PDF for all images). Default: `single`. |
| `--batch-size` | Number of images per PDF (only in batch mode). Default: 500. |
| `--threads` | Number of threads for image conversion. Default: 5. |
| `--use-webp` | Convert images to WEBP before PDF creation (saves memory). Default: false. |
| `--keep-webp` | Keep WEBP files after PDF creation (only if `--use-webp` is true). Default: false. |
| `--recursive` | Scan subfolders recursively (only in single mode). Default: false. |
| `--verbose` | Show detailed progress logs. |

#### Examples

1. **Single PDF from all images in folder**  
   ```bash
   python -m pdf_architect.cli.main --input "My Images" --output ./pdfs --mode single
   ```

2. **Batch mode with WEBP conversion and 10 threads**  
   ```bash
   python -m pdf_architect.cli.main --input "My Images" --mode batch --batch-size 200 --threads 10 --use-webp
   ```

3. **Recursive single PDF (include subfolders)**  
   ```bash
   python -m pdf_architect.cli.main --input "My Images" --mode single --recursive
   ```

### Python API

You can also use the library programmatically. Here's an example:

```python
from pdf_architect.core.converter import ImageToPdfConverter

converter = ImageToPdfConverter(
    input_folder="My Images",
    output_folder="./pdfs",
    batch_mode=True,
    batch_size=200,
    num_threads=10,
    use_webp=True,
    keep_webp=False,
    recursive=False
)
converter.run()
```

## Project Structure

```
pdf_architect/
├── README.md                    # This file
├── requirements.txt             # Dependencies (Pillow, tqdm)
├── LICENSE                      # MIT License
├── .gitignore                   # Standard Python ignores
├── setup.py                     # Package installation script
├── pdf_architect/               # Main package
│   ├── __init__.py              # Package metadata
│   ├── cli/                     # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py              # Argument parsing and entry point
│   ├── core/                    # Core conversion logic
│   │   ├── __init__.py
│   │   ├── converter.py         # Main class ImageToPdfConverter
│   │   ├── worker.py            # Parallel conversion worker
│   │   └── utils.py             # Helper functions (natural sort, RGB conversion, etc.)
│   └── ... (other modules)
├── tests/                       # Unit tests (to be added)
│   └── __init__.py
└── examples/                    # Sample images (optional)
    └── sample_images/
```

### Explanation of Key Files

- **`pdf_architect/cli/main.py`**  
  Handles command-line arguments using `argparse` and initializes the converter.

- **`pdf_architect/core/converter.py`**  
  Contains the `ImageToPdfConverter` class. It orchestrates the whole process: collecting images, converting to WEBP (if enabled), splitting into batches, and creating PDFs.

- **`pdf_architect/core/worker.py`**  
  Provides `ConversionWorker`, which manages a pool of threads to convert images to WEBP in parallel. It uses `ThreadPoolExecutor` for efficient parallel processing.

- **`pdf_architect/core/utils.py`**  
  Utility functions:  
  - `natural_sort_key()` – for proper numeric sorting.  
  - `get_image_files()` – yields image file paths from a folder (optionally recursive).  
  - `validate_image()` – checks if an image is valid (used for error handling).  
  - `ensure_rgb_for_pdf()` – converts any image mode (RGBA, P, L, etc.) to RGB, handling transparency with a white background.

- **`setup.py`**  
  Defines the package metadata and entry points, making it installable via `pip install -e .` and providing the console script `pdf-architect`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT License. See `LICENSE` file.

## Acknowledgements

Built with [Pillow](https://python-pillow.org/).
```