# Audible PDF Renamer

Automatically rename Audible audiobook PDF companions from cryptic codes like `bk_adbl_022796.pdf` to their actual book titles like `Misbehaving.pdf`.

## The Problem

When you download PDF companions from Audible, they come with unhelpful filenames:

```
bk_adbl_022796.pdf
bk_rand_002806.pdf
bk_sans_007977.pdf
bk_harp_004529.pdf
```

Good luck remembering which book is which!

## The Solution

This tool automatically extracts the book title from each PDF and renames the files:

```
Misbehaving.pdf
Thinking Fast and Slow.pdf
Leonardo da Vinci.pdf
The Intelligent Investor.pdf
```

## Features

- **3-tier title extraction**: Tries multiple methods to find the title
  1. PDF metadata
  2. Text extraction from content
  3. OCR for image-based PDFs (optional)
- **Dry run mode**: Preview changes before committing
- **Safe renaming**: Handles filename conflicts and special characters
- **Verbose output**: See exactly how titles are being extracted

## Installation

### Basic Installation

```bash
pip install pdfplumber pypdf
```

### With OCR Support (Recommended)

OCR allows the tool to extract titles from image-based PDFs (like O'Reilly books):

```bash
# Install Python packages
pip install pdfplumber pypdf pytesseract pdf2image

# Install Tesseract OCR engine
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Also install poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

### From Source

```bash
git clone https://github.com/snapsynapse/audible-pdf-renamer.git
cd audible-pdf-renamer
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Rename PDFs in current directory
python audible_pdf_renamer.py

# Rename PDFs in a specific folder
python audible_pdf_renamer.py ~/Downloads/Audible

# Rename PDFs in a folder with spaces
python audible_pdf_renamer.py "/path/to/Audible Booknotes"
```

### Preview Changes (Dry Run)

See what would be renamed without actually changing anything:

```bash
python audible_pdf_renamer.py --dry-run
python audible_pdf_renamer.py ~/Downloads/Audible -n
```

### Verbose Output

See detailed information about how titles are extracted:

```bash
python audible_pdf_renamer.py --verbose
python audible_pdf_renamer.py ~/Downloads/Audible -v
```

### Disable OCR

Skip OCR extraction for faster processing (may miss some titles):

```bash
python audible_pdf_renamer.py --no-ocr
```

### Custom File Pattern

Process all PDFs, not just Audible-named ones:

```bash
python audible_pdf_renamer.py --pattern "*.pdf"
```

### Combined Options

```bash
python audible_pdf_renamer.py ~/Downloads/Audible --dry-run --verbose
```

## Development

Run the eval suite locally with:

```bash
pytest -q
```

GitHub Actions runs the same suite on macOS, Ubuntu, and Windows for pull requests and pushes to `main`.

## How It Works

The tool uses a 3-tier fallback approach to extract book titles:

### 1. PDF Metadata
Many PDFs have the title stored in their metadata properties. This is the fastest and most reliable method when available.

### 2. Text Extraction
If metadata isn't available, the tool extracts text from the first few pages and looks for title patterns. It intelligently skips boilerplate content like copyright notices and publisher information.

### 3. OCR (Optical Character Recognition)
Some PDFs (particularly from publishers like O'Reilly) have image-based content where text extraction doesn't work. The tool renders these pages as images and uses Tesseract OCR to read the title.

## Example Output

```
Audible PDF Renamer v1.0.0
Folder: /Users/you/Downloads/Audible Booknotes
OCR: Available

Found 51 PDF(s) to process

======================================================================

bk_rand_002806.pdf
  → Thinking Fast and Slow.pdf
    (extracted via text)
  ✓ Renamed successfully

bk_sans_007977.pdf
  → Leonardo da Vinci.pdf
    (extracted via text)
  ✓ Renamed successfully

bk_upfr_000065.pdf
  → Information Architecture for the Web and Beyond.pdf
    (extracted via ocr)
  ✓ Renamed successfully

======================================================================

Summary:
  ✓ Renamed: 51
  ✗ Failed: 0
```

## Troubleshooting

### "No PDFs found matching pattern"

By default, the tool only processes files starting with `bk_` (Audible's naming convention). If your files have different names, use the `--pattern` flag:

```bash
python audible_pdf_renamer.py --pattern "*.pdf"
```

### OCR not working

1. Make sure Tesseract is installed and in your PATH:
   ```bash
   tesseract --version
   ```

2. Make sure poppler-utils is installed (required by pdf2image):
   ```bash
   # Check if pdftoppm is available
   which pdftoppm
   ```

### Some titles aren't extracted correctly

The tool does its best to extract titles, but some PDFs may have unusual formatting. You can:

1. Use `--verbose` to see what's being extracted
2. Manually rename problematic files
3. Open an issue with details about the problematic PDF

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF text extraction
- Uses [pypdf](https://github.com/py-pdf/pypdf) for PDF metadata
- OCR powered by [Tesseract](https://github.com/tesseract-ocr/tesseract) via [pytesseract](https://github.com/madmaze/pytesseract)
