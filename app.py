"""
Offline Document Compiler & PDF Generator
=========================================
A lightweight Flask web application that compiles multiple photos
of documents/images into a single PDF with a custom file name.

Runs entirely offline on Windows. Designed for low-spec hardware (4GB RAM).
"""

import os
import uuid
import re
from datetime import datetime
# pyrefly: ignore [missing-import]
from flask import (
    Flask, render_template, request, jsonify,
    send_file
)
from utils.image_processor import preprocess_image, preprocess_for_ocr
from utils.pdf_generator import generate_pdf_from_images
from utils.ocr import extract_metadata_from_image, configure_tesseract, is_tesseract_installed

# =============================================================================
# Configuration
# =============================================================================

app = Flask(__name__)

# Configure Tesseract OCR on startup
configure_tesseract(None)

# Maximum upload size: 10 MB per image
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Allowed image file extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)


# =============================================================================
# Helper Functions
# =============================================================================

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def cleanup_file(filepath):
    """Safely delete a file if it exists."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass


def sanitize_filename(filename):
    """Sanitize the user-provided PDF name to be safe for Windows filesystems."""
    # Remove characters that are illegal in Windows filenames: \ / : * ? " < > |
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Remove leading/trailing whitespaces/dots
    filename = filename.strip(" .")
    # Replace multiple spaces/underscores
    filename = re.sub(r'\s+', "_", filename)
    # Ensure there's a fallback if empty
    if not filename:
        filename = "compiled_document"
    return filename


# =============================================================================
# Routes
# =============================================================================

@app.route("/")
def index():
    """Serve the single-page UI."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_image():
    """
    Handle individual image uploads.
    
    Accepts: multipart/form-data with a file field named 'image'.
    Returns: JSON with the filename, preview URL, and metadata.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file was uploaded."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file was selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Invalid file type. Please upload a JPG, JPEG, or PNG image."
        }), 400

    # Save to temp filename
    ext = file.filename.rsplit(".", 1)[1].lower()
    temp_name = f"temp_{uuid.uuid4().hex}.{ext}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_name)

    try:
        file.save(temp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save uploaded file: {str(e)}"}), 500

    oriented_path = None
    try:
        # Auto-rotate image to make sure it displays correctly in browser and PDF
        oriented_path = preprocess_image(temp_path)
        oriented_filename = os.path.basename(oriented_path)

        # Cleanup original temp image
        cleanup_file(temp_path)

        # Extract metadata fields using OCR behind the scenes
        branch = ""
        project = ""
        reference = ""
        ocr_temp_path = None

        try:
            # Create a high-contrast copy optimized specifically for OCR readability
            ocr_temp_path = preprocess_for_ocr(oriented_path)
            # Run OCR and extract Branch, Project, and Ref Number using regular expressions
            metadata = extract_metadata_from_image(ocr_temp_path)
            branch = metadata.get("branch", "")
            project = metadata.get("project", "")
            reference = metadata.get("reference", "")
        except Exception as ocr_err:
            print(f"OCR metadata extraction failed: {str(ocr_err)}")
        finally:
            # Cleanup the high-contrast OCR image copy immediately
            cleanup_file(ocr_temp_path)

        preview_url = f"/static/uploads/{oriented_filename}"
        return jsonify({
            "filename": oriented_filename,
            "preview_url": preview_url,
            "original_name": file.filename,
            "branch": branch,
            "project": project,
            "reference": reference,
            "message": "Image uploaded successfully!"
        }), 200

    except Exception as e:
        cleanup_file(temp_path)
        cleanup_file(oriented_path)
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500


@app.route("/generate-pdf", methods=["POST"])
def create_pdf():
    """
    Compile multiple uploaded images into a single PDF.
    
    Accepts: JSON with:
      {
         "filenames": ["img1.jpg", "img2.png"],
         "pdf_name": "My Document Name",
         "orientation": "portrait" / "landscape"
      }
    Returns: PDF file stream.
    """
    data = request.get_json()

    if not data or "filenames" not in data or not data["filenames"]:
        return jsonify({"error": "No images provided to build PDF."}), 400

    filenames = data["filenames"]
    user_pdf_name = data.get("pdf_name", "compiled_document").strip()
    orientation = data.get("orientation", "portrait").strip().lower()
    
    if orientation not in {"portrait", "landscape"}:
        orientation = "portrait"

    # Sanitize PDF name
    safe_name = sanitize_filename(user_pdf_name)
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"

    # Full paths for images
    image_paths = []
    for fname in filenames:
        img_path = os.path.join(UPLOAD_FOLDER, fname)
        if os.path.exists(img_path):
            image_paths.append(img_path)
        else:
            return jsonify({"error": f"Uploaded file {fname} could not be found. Please re-upload."}), 400

    if not image_paths:
        return jsonify({"error": "None of the specified images exist on the server."}), 400

    # Output path for temporary PDF
    pdf_filename = f"{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(EXPORT_FOLDER, pdf_filename)

    try:
        # Generate the PDF with ReportLab
        generate_pdf_from_images(image_paths, pdf_path, title=user_pdf_name, orientation=orientation)

        # Send file back to client
        response = send_file(
            pdf_path,
            as_attachment=True,
            download_name=safe_name,
            mimetype="application/pdf"
        )

        # Hook to delete the PDF after transmission completes (images persist for previews)
        @response.call_on_close
        def cleanup():
            cleanup_file(pdf_path)

        return response

    except Exception as e:
        # Ensure temporary PDF gets deleted in case of failure
        cleanup_file(pdf_path)
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


@app.route("/delete-images", methods=["POST"])
def delete_images():
    """
    Delete specific uploaded images from the server to keep disk clean.
    
    Accepts: JSON with:
      {
         "filenames": ["img1.jpg", "img2.png"]
      }
    """
    data = request.get_json()
    if data and "filenames" in data:
        filenames = data["filenames"]
        for fname in filenames:
            # Prevent directory traversal attacks by securing filename
            fname_secure = os.path.basename(fname)
            cleanup_file(os.path.join(UPLOAD_FOLDER, fname_secure))
    return jsonify({"success": True}), 200


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "The file is too large. Maximum size per image is 10 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "The requested resource was not found."}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    import webbrowser
    import threading
    import time

    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000")

    print("=" * 50)
    print("  Document Compiler & PDF Generator")
    print("  Open http://localhost:8000 in your browser")
    print("=" * 50)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=8000, debug=False)
