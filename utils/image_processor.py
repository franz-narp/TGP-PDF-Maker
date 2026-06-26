"""
Image Processor Module
Handles image auto-rotation based on EXIF data before PDF generation.
Optimized for low memory usage on older hardware.
"""

from PIL import Image, ExifTags, ImageEnhance, ImageFilter
import os


def preprocess_for_ocr(oriented_image_path):
    """
    Convert an oriented image to high-contrast grayscale to optimize OCR readability.
    
    Args:
        oriented_image_path (str): Path to the auto-rotated color image.
        
    Returns:
        str: Path to the temporary high-contrast grayscale image.
    """
    if not os.path.exists(oriented_image_path):
        raise FileNotFoundError(f"Image not found: {oriented_image_path}")

    img = Image.open(oriented_image_path)

    # Convert to grayscale
    ocr_img = img.convert("L")

    # Enhance contrast heavily (factor of 2.0 works best to isolate black text on white backgrounds)
    enhancer = ImageEnhance.Contrast(ocr_img)
    ocr_img = enhancer.enhance(2.0)

    # Apply sharpening
    ocr_img = ocr_img.filter(ImageFilter.SHARPEN)

    directory = os.path.dirname(oriented_image_path)
    filename = os.path.basename(oriented_image_path)
    name, ext = os.path.splitext(filename)
    ocr_path = os.path.join(directory, f"{name}_ocr{ext}")

    ocr_img.save(ocr_path, optimize=True)
    img.close()
    ocr_img.close()

    return ocr_path


def preprocess_image(image_path):
    """
    Ensure the image is correctly rotated based on EXIF data.
    
    Args:
        image_path (str): Path to the uploaded image file.
    
    Returns:
        str: Path to the processed image file (overwrites or saves a new one).
    
    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the file is not a valid image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        img = Image.open(image_path)
    except Exception:
        raise ValueError("Could not open file as an image. The file may be corrupt.")

    # Auto-rotate based on EXIF orientation
    rotated_img = _fix_orientation(img)

    # Save it back if it was rotated, to optimize PDF size and ensure correct rendering
    # If no rotation is needed, we still save to verify format and close handles
    directory = os.path.dirname(image_path)
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    processed_path = os.path.join(directory, f"{name}_oriented{ext}")

    rotated_img.save(processed_path, optimize=True)
    
    img.close()
    if rotated_img is not img:
        rotated_img.close()

    return processed_path


def _fix_orientation(img):
    """
    Rotate an image based on its EXIF orientation tag.
    
    Args:
        img (PIL.Image): The image to fix.
    
    Returns:
        PIL.Image: The correctly oriented image.
    """
    try:
        exif = img._getexif()
        if exif is None:
            return img

        orientation_key = None
        for key, val in ExifTags.TAGS.items():
            if val == "Orientation":
                orientation_key = key
                break

        if orientation_key is None or orientation_key not in exif:
            return img

        orientation = exif[orientation_key]

        if orientation == 2:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 4:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 6:
            img = img.rotate(-90, expand=True)
        elif orientation == 7:
            img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 8:
            img = img.rotate(90, expand=True)

    except (AttributeError, KeyError, IndexError):
        pass

    return img
