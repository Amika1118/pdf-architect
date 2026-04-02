import re
from pathlib import Path
from typing import List, Iterator

def natural_sort_key(s: str) -> List:
    """
    Generate a key for natural sorting (e.g., 'image10.jpg' > 'image2.jpg').
    """
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', s)]


def get_image_files(folder: Path, recursive: bool = False) -> Iterator[Path]:
    """
    Yield Path objects of image files in folder (optionally recursive).
    Supported extensions: .png, .jpg, .jpeg, .bmp, .gif, .webp, .tiff
    """
    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff'}
    if recursive:
        for path in folder.rglob("*"):
            if path.suffix.lower() in extensions:
                yield path
    else:
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() in extensions:
                yield path


def validate_image(path: Path) -> bool:
    """Check if the image is valid and not corrupted."""
    from PIL import Image
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def ensure_rgb_for_pdf(image):
    """Convert any PIL Image to RGB mode suitable for PDF."""
    from PIL import Image
    if image.mode == 'RGBA':
        # Create a white background for transparency
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        return background
    elif image.mode == 'P' and 'transparency' in image.info:
        # Palette with transparency
        image = image.convert('RGBA')
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        return background
    elif image.mode != 'RGB':
        return image.convert('RGB')
    return image