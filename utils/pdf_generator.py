"""
PDF Generator Module
Compiles multiple images into a single PDF file using ReportLab.
Each image is placed on its own page, scaled proportionally to fit.
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, PageBreak
# pyrefly: ignore [missing-import]
from PIL import Image as PILImage
import os


def generate_pdf_from_images(image_paths, output_path, title="Compiled Document", orientation="portrait"):
    """
    Generate a PDF from a list of image paths.
    
    Each image is placed on a separate page, scaled to fit margins
    while maintaining its original aspect ratio.
    
    Args:
        image_paths (list): List of paths to the images.
        output_path (str): Path where the PDF should be saved.
        title (str): Metadata title for the PDF document.
        orientation (str): Page orientation ("portrait" or "landscape").
        
    Returns:
        str: Path to the generated PDF file.
        
    Raises:
        ValueError: If image_paths list is empty.
        IOError: If any image cannot be read or PDF build fails.
    """
    if not image_paths:
        raise ValueError("No images provided for PDF generation.")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        # Determine page size and printable bounds based on orientation
        if orientation == "landscape":
            pagesize = landscape(letter)
            # Default ReportLab landscape Frame for Letter: width 792 - margins, height 612 - margins
            # Safe dimensions fitting within the templates' frames
            avail_width = 680
            avail_height = 500
        else:
            pagesize = letter
            avail_width = 520
            avail_height = 680

        margin = 0.5 * inch
        doc = SimpleDocTemplate(
            output_path,
            pagesize=pagesize,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
            title=title,
            author="Document Compiler",
        )

        story = []

        for idx, img_path in enumerate(image_paths):
            if not os.path.exists(img_path):
                raise FileNotFoundError(f"Image not found: {img_path}")

            # Get dimensions using PIL to compute scaling
            with PILImage.open(img_path) as pil_img:
                img_width, img_height = pil_img.size

            # Scale to fit printable dimensions while preserving aspect ratio
            aspect = img_width / img_height

            # Determine best width/height to maximize page coverage without exceeding margins
            if (avail_width / aspect) <= avail_height:
                w = avail_width
                h = avail_width / aspect
            else:
                h = avail_height
                w = avail_height * aspect

            # Create ReportLab Image flowable
            story.append(RLImage(img_path, width=w, height=h))

            # Add page break if it is not the last page
            if idx < len(image_paths) - 1:
                story.append(PageBreak())

        # Build document
        doc.build(story)

    except Exception as e:
        raise IOError(f"Failed to generate PDF: {str(e)}")

    return output_path
