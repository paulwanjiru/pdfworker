# Document Studio Pro (DocuStudio)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52?logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Offline%20%2F%20Local-22c55e?logo=shield&logoColor=white)](#privacy--security)

**Document Studio Pro** is a modern, high-performance desktop suite for manipulating, converting, protecting, optimizing, and inspecting PDF and Office documents. Built with **PyQt5** and designed with a bespoke high-contrast blue/white/dark aesthetic, it provides 20 specialized tools in a single unified, responsive interface — completely local, offline, and private.

---

## 🌟 Key Highlights

- **100% Local & Private**: No cloud uploads, no third-party APIs, and no telemetry. All processing happens entirely on your machine.
- **20 Professional Tools**: From everyday splitting and merging to advanced legal Bates numbering, digital certificate signing, and booklet imposition.
- **Multithreaded Performance**: Heavy document crunching and thumbnail generation run on asynchronous background threads (`DocWorker` and `ThumbnailWorker`), keeping the UI fluid and responsive at all times.
- **Seamless Office & Imaging Integration**: Native support for PDF, Word (`.docx`), Excel (`.xlsx`), and common image formats (`PNG`, `JPEG`, `TIFF`, `WebP`, `BMP`).
- **Modern User Experience**: Full high-DPI scaling, smooth drag-and-drop zones, custom vector icon fonts, interactive thumbnail grids, and high-contrast Light/Dark mode switching.

---

## 🛠️ Complete Feature Matrix

The application organizes its 20 tools into 6 specialized workflows:

### 1. Document Operations
| Feature | Description |
| :--- | :--- |
| **Split PDF** | Split by single page, custom page ranges (e.g. `1-3, 5, 8-12`), fixed-page chunks (every *N* pages), or target file sizes. |
| **Merge PDF** | Combine multiple documents in any order with drag-and-drop reordering while preserving document metadata, outlines, and form fields. |
| **Convert Documents** | Convert bi-directionally between PDF, Word (`.docx`), Excel (`.xlsx`), text, and image formats. Uses Microsoft Office COM automation on Windows when available for pixel-perfect conversions. |

### 2. Protection & Archival
| Feature | Description |
| :--- | :--- |
| **PDF Security** | Encrypt files with 128-bit/256-bit passwords; configure user/owner permissions (allow/deny printing, text copying, annotations, form filling); decrypt password-protected PDFs. |
| **Watermarks & Page Numbers** | Stamp custom text watermarks (configurable opacity, rotation angle, and fonts), image watermarks, dynamic headers/footers, and page numbers across multiple placement positions. |
| **Organize & Rotate** | Batch-rotate pages (90°, 180°, 270°), extract page selections, reorder pages, or automatically detect and strip blank pages. |
| **Digital Signatures** | Cryptographically sign and validate PDF documents using PKCS#12 / PFX certificate files and X.509 keys powered by PyHanko. |
| **PDF/A Long-Term Archive** | Convert standard PDFs into compliant archival formats (PDF/A-1b and PDF/A-2b) utilizing integrated Ghostscript automation. |

### 3. Visual Editing & Print Layout
| Feature | Description |
| :--- | :--- |
| **Visual Organizer** | Visual grid of high-resolution page thumbnails. Drag and drop pages to rearrange, select multiple pages, rotate individual sheets, or delete pages visually. |
| **N-Up & Booklet Printing** | Multi-page sheet imposition (print 2, 4, or 8 pages per sheet) with custom borders and gutters; create saddle-stitch booklets arranged for front-and-back folding. |
| **Bates Numbering** | Legal-grade document indexing with custom alphanumeric prefixes, suffixes, leading-zero padding, starting offsets, and customizable corner placement. |

### 4. Optimization & Batch Workflows
| Feature | Description |
| :--- | :--- |
| **Optimize / Compress** | Shrink file sizes using customizable compression presets (*Lossless*, *Balanced*, *Aggressive*), stream deflating, image downsampling (custom DPI), and font subsetting. |
| **Batch Processing** | Apply operations (conversion, compression, watermarking, encryption) across entire folders of documents in a single automated queue. |

### 5. Automation & OCR
| Feature | Description |
| :--- | :--- |
| **OCR / Searchable PDF** | Optical Character Recognition powered by Tesseract OCR. Converts scanned images and non-selectable PDFs into searchable, selectable text PDFs. |
| **Mail Merge** | Generate personalized documents by merging Excel (`.xlsx`) or CSV datasets into Word templates (`.docx`) using Jinja2 syntax via `docxtpl`. |

### 6. Inspection & Quality Control
| Feature | Description |
| :--- | :--- |
| **Metadata & QR Generator** | View and edit internal PDF metadata (Title, Author, Subject, Keywords). Generate high-density QR codes and embed them directly onto document pages. |
| **PDF Comparison** | Perform text and layout diffs between two PDF revisions, generating a visual side-by-side HTML comparison report highlighting additions and deletions. |
| **Style & Markup Inspector** | Inspect embedded font families, color palettes, AcroForms, XML metadata (XMP), and internal object streams. |
| **Job History** | Local audit log tracking all completed operations, timestamps, output file paths, and quick "Open File" / "Open Directory" shortcuts. |

---

## 📂 Project Architecture

The application is structured into a clean, decoupled Python package:

```text
├── splitter.py            # Clean, lightweight application entry point (75 lines)
├── requirements.txt       # Core and optional third-party dependencies
├── Setup.bat              # One-click Windows setup launcher
├── Setup.ps1              # Automated WPF GUI installer & dependency provisioner
├── launcher.vbs           # Silent, windowless background launcher
├── splitter.spec          # PyInstaller standalone executable build recipe
├── hierarchy.ico          # Application branding icon
└── app/                   # Core application package
    ├── __init__.py        # Package exports
    ├── deps.py            # Centralized optional dependency loader & fallback shims
    ├── icons.py           # Vector glyph engine (Segoe Fluent / MDL2 / Symbol)
    ├── styles.py          # Design tokens, light palette, and high-contrast dark theme
    ├── config.py          # App settings, job history database, external binary finders
    ├── helpers.py         # UI utility functions, shadow effects, page range parsers
    ├── widgets.py         # Custom interactive UI components (DropZone, RotatingGear)
    ├── workers.py         # Asynchronous worker threads (DocWorker, ThumbnailWorker)
    └── main_window.py     # Main application window & 20 tool panel implementations
```

---

## 🚀 Getting Started

### Prerequisites

- **Windows 10 / 11** (64-bit recommended)
- **Python 3.10+** or **Python 3.11**
- *(Optional)* [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) for OCR text recognition.
- *(Optional)* [Ghostscript](https://ghostscript.com/) for PDF/A archival conversions.

### Quick Start (Automated Installer)

Run the included setup launcher from File Explorer or terminal:

```cmd
Setup.bat
```

This launches the automated installation wizard which checks the environment, installs missing requirements, and creates desktop and start menu shortcuts.

### Manual Installation

1. Clone or extract the repository:
   ```bash
   git clone https://github.com/paulwanjiru/pdfworker.git
   cd pdfworker
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch the application:
   ```bash
   python splitter.py
   ```

*(Alternatively, double-click `launcher.vbs` to launch silently without an attached console window).*

---

## 📦 Building Standalone Executable

To bundle the application into a standalone Windows executable (`.exe`) that doesn't require Python on the target machine:

```bash
pip install pyinstaller
py -m PyInstaller splitter.spec
```

The compiled portable application will be generated in the `dist/` directory.

---

## 🔒 Privacy & Security

Unlike online PDF services, **Document Studio Pro processes 100% of your data locally**:
- **No Cloud Uploads**: Your confidential agreements, tax documents, and financial records never leave your drive.
- **Air-Gapped Ready**: Operates with full capability on computers disconnected from the internet.
- **Zero Telemetry**: No user tracking, analytical beacons, or external phone-home requests.

---

## 📄 License & Credits

Developed by **Infrabit Systems** ([https://www.infrabitsystems.co.ke](https://www.infrabitsystems.co.ke)).  
All rights reserved.
