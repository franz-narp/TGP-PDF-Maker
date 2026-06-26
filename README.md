# 📄 Offline Document Compiler & PDF Generator

A lightweight desktop web application that compiles multiple photos or scans of printed document pages into a single, clean PDF file. It runs **completely offline** on Windows — no internet required.

**Designed for non-technical or elderly users:** large buttons, large fonts, high contrast, minimal navigation, and a single-page workflow.

---

## ✅ Features

- **Upload** multiple images at once (drag-and-drop or select).
- **Sequential upload processing** — ensures low RAM usage on older devices (e.g. 4GB RAM).
- **EXIF Auto-rotation** — rotates images automatically if taken from phones.
- **Review Gallery** — see thumbnails of all pages, showing page numbers and individual "Remove" buttons.
- **Page Re-ordering** — move pages back and forth to get the sequence perfect.
- **OCR Auto-fill metadata** — automatically extracts the **Branch Name**, **Project Type**, and **Reference Number** from budget liquidation forms using local Tesseract OCR, and automatically populates the text boxes in real-time.
- **Strict Naming Convention** — generates the safe output filename in the format: `BRANCH PROJECT REFERENCE.pdf`.
- **Page Orientation Select** — toggle between **Portrait (Upright)** and **Landscape (Wide)** layout.
- **Live PDF Preview** — view the output PDF instantly inside the app before downloading, with options to scroll, zoom, print, or download natively.
- Works completely **offline** after installation.

---

## 📋 Prerequisites

Before running this application, you need:

1. **Python 3.8 or newer**
   - Download from: https://www.python.org/downloads/
   - ⚠️ During installation, check **"Add Python to PATH"**

2. **Tesseract OCR**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to the default location: `C:\Program Files\Tesseract-OCR\`
   - ⚠️ During installation, make sure **English language data** is selected

---

## 🚀 Installation

Open **Command Prompt** (or PowerShell) and run:

```bash
# 1. Navigate to the project folder
cd path\to\TGP_PDF

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the Application

```bash
# Make sure you're in the project folder
cd path\to\TGP_PDF

# If using a virtual environment, activate it first
venv\Scripts\activate

# Start the application
python app.py
```

Then open your web browser and go to:

```
http://localhost:8000
```

---

## 📖 How to Use

1. **Upload** — Click the upload area (or drag and drop files) to select one or more photos.
2. **Auto-fill & Review** — The system will read the liquidation form and auto-fill the **Branch Name**, **Project Type**, and **Reference Number**. Look at the page thumbnails and use `◀` and `▶` buttons to arrange order. Click **✕** on a thumbnail to remove a page, or **Clear All** to start over.
3. **Configure** — Double check that the auto-filled names are correct (edit if needed), and select **Portrait** or **Landscape** orientation.
4. **Preview & Save** — Click **Preview PDF** to check the layout. Click **Download PDF** to save it to your computer.

---

## 🗂️ Project Structure

```
TGP_PDF/
├── app.py                  # Flask application (main entry point)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── static/
│   ├── css/
│   │   └── style.css       # Stylesheet
│   ├── js/
│   │   └── app.js          # Frontend JavaScript logic
│   └── uploads/            # Temporary oriented images
├── templates/
│   └── index.html          # UI template
├── utils/
│   ├── __init__.py
│   ├── image_processor.py  # Fixes EXIF rotations & makes high-contrast copy for OCR
│   ├── ocr.py              # OCR metadata extractor using Tesseract
│   └── pdf_generator.py    # Compiles images to PDF using ReportLab
└── exports/                # Temporary compiled PDF storage
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't start | Make sure Python is installed and added to PATH. |
| "Tesseract is not installed" error | Install Tesseract OCR from the link above and restart the app. |
| Port 8000 already in use | Close other apps using port 8000, or change the port in `app.py`. |
| File too large error | Ensure each individual image is under 10 MB. |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| Pillow | Image loading and rotation handling |
| pytesseract | Python wrapper for Tesseract OCR |
| reportlab | PDF compiler |
