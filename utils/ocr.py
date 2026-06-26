"""
OCR Module
Extracts specific fields (Branch, Project, Reference Number) from preprocessed images
using Tesseract OCR and regular expressions.
"""

import pytesseract
import os
import re


def configure_tesseract(custom_path=None):
    """Configure the path to the Tesseract executable on Windows."""
    if custom_path and os.path.exists(custom_path):
        pytesseract.pytesseract.tesseract_cmd = custom_path
        return

    # Default Windows install locations
    default_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(
            os.getenv("USERNAME", "")
        ),
    ]

    for path in default_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return

    # Fallback to default command name (system path lookup)
    pytesseract.pytesseract.tesseract_cmd = "tesseract"


def is_tesseract_installed():
    """
    Check if the Tesseract OCR engine is installed and available.
    
    Returns:
        bool: True if installed, False otherwise.
    """
    cmd = pytesseract.pytesseract.tesseract_cmd
    if not cmd:
        return False
    if cmd == "tesseract":
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False
    return os.path.exists(cmd)


def extract_metadata_from_image(image_path):
    """
    Run Tesseract OCR on the image and extract Branch, Project, and Reference Number.
    
    Args:
        image_path (str): Path to the preprocessed image.
        
    Returns:
        dict: Extracted values {'branch': '...', 'project': '...', 'reference': '...'}
    """
    if not os.path.exists(image_path):
        return {"branch": "", "project": "", "reference": ""}

    try:
        # Document block layout psm 6 or general layouts psm 3
        # psm 3 is the default, which automatically fragments pages and performs layouts
        text = pytesseract.image_to_string(image_path, lang="eng", config="--oem 3 --psm 3")
    except Exception as e:
        # If Tesseract is not installed, fail silently or print error and return empty dict
        print(f"OCR Exception: {str(e)}")
        return {"branch": "", "project": "", "reference": ""}

    if not text:
        return {"branch": "", "project": "", "reference": ""}

    # Parse fields using regular expressions
    branch = ""
    project = ""
    reference = ""

    # Search for Branch (e.g. Branch: ILUSTRE)
    # Match standard patterns like "Branch: VALUE" or "Branch VALUE"
    branch_match = re.search(r'Branch\s*:?\s*([^\n]+)', text, re.IGNORECASE)
    if branch_match:
        val = branch_match.group(1).strip()
        # Clean up if it captures labels next to it
        val = re.sub(r'^(Name|Project|Date|Payee|Particulars):.*', '', val, flags=re.IGNORECASE).strip()
        # Clean special chars, preserve spaces
        val = re.sub(r'[^\w\s-]', '', val).strip()
        branch = val

    # Search for Project (e.g. Project: JUNE ELECTRIC BILL)
    project_match = re.search(r'Project\s*:?\s*([^\n]+)', text, re.IGNORECASE)
    if project_match:
        val = project_match.group(1).strip()
        val = re.sub(r'^(Name|Branch|Date|Payee|Particulars):.*', '', val, flags=re.IGNORECASE).strip()
        val = re.sub(r'[^\w\s-]', '', val).strip()
        project = val

    # Search for Fund Transfer Reference No / Reference Number (e.g. 061526-111314-38965896)
    # Pattern: 6 digits - 6 digits - 8 digits
    ref_pattern_match = re.search(r'(\d{6}-\d{6}-\d{8})', text)
    if ref_pattern_match:
        reference = ref_pattern_match.group(1).strip()
    else:
        # Fallback to search around label "Reference No." or "Reference No"
        ref_label_match = re.search(r'(?:Reference|Ref)(?:\s+No\.?|\s+No)?\s*:?\s*([\d-]+)', text, re.IGNORECASE)
        if ref_label_match:
            reference = ref_label_match.group(1).strip()

    return {
        "branch": branch,
        "project": project,
        "reference": reference
    }
