#!/usr/bin/env python3
"""
Audible PDF Renamer
-------------------
Renames Audible book notes PDFs from cryptic codes (e.g., bk_adbl_022796.pdf)
to their actual book titles.

Uses a 3-tier fallback approach:
1. PDF metadata (title field)
2. Text extraction (pdfplumber)
3. OCR on rendered pages (pytesseract) - for image-based PDFs

Usage:
    python audible_pdf_renamer.py [folder_path] [options]

Options:
    --dry-run       Preview changes without renaming
    --verbose       Show detailed extraction info
    --no-ocr        Disable OCR fallback (faster but may miss some titles)
    --pattern PAT   Custom filename pattern to match (default: bk_*)

Examples:
    python audible_pdf_renamer.py ~/Downloads/Audible
    python audible_pdf_renamer.py . --dry-run
    python audible_pdf_renamer.py /path/to/pdfs --verbose --no-ocr
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

__version__ = "1.0.0"
__author__ = "Audible PDF Renamer Contributors"
__license__ = "MIT"

OCR_AVAILABLE = False
pdfplumber = None
PdfReader = None
pytesseract = None
convert_from_path = None

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def ensure_required_packages():
    """Import required PDF packages on demand."""
    global pdfplumber, PdfReader

    if pdfplumber is not None and PdfReader is not None:
        return

    try:
        import pdfplumber as pdfplumber_module
        from pypdf import PdfReader as pdf_reader
    except ImportError as e:
        raise RuntimeError(
            f"Required package not found: {e}. Install with: pip install pdfplumber pypdf"
        ) from e

    pdfplumber = pdfplumber_module
    PdfReader = pdf_reader


def ensure_ocr_packages():
    """Import optional OCR packages on demand."""
    global OCR_AVAILABLE, pytesseract, convert_from_path

    if OCR_AVAILABLE and pytesseract is not None and convert_from_path is not None:
        return True

    try:
        import pytesseract as pytesseract_module
        from pdf2image import convert_from_path as convert_from_path_func
    except ImportError:
        OCR_AVAILABLE = False
        return False

    pytesseract = pytesseract_module
    convert_from_path = convert_from_path_func
    OCR_AVAILABLE = True
    return True


class TitleExtractor:
    """Extracts book titles from PDFs using multiple strategies."""

    def __init__(self, use_ocr=True, verbose=False):
        self.use_ocr = use_ocr and OCR_AVAILABLE
        self.verbose = verbose

    def log(self, message):
        """Print verbose output if enabled."""
        if self.verbose:
            print(f"    {message}")

    def clean_spaced_text(self, text):
        """Convert spaced letters like 'T H I N K I N G' to 'THINKING'"""
        words = text.split()
        if len(words) > 1 and all(len(w) == 1 for w in words):
            return ''.join(words)
        return text

    def extract_from_metadata(self, filepath):
        """Strategy 1: Try PDF metadata."""
        try:
            ensure_required_packages()
            reader = PdfReader(filepath)
            meta = reader.metadata
            if meta and meta.title and len(str(meta.title)) > 3:
                title = str(meta.title)
                # Skip technical/placeholder titles
                skip_patterns = ['_wb_', '.indd', 'untitled', 'microsoft word',
                               'layout 1', 'powerpoint']
                if not any(x in title.lower() for x in skip_patterns):
                    self.log(f"Found in metadata: {title}")
                    return title
        except Exception as e:
            self.log(f"Metadata extraction failed: {e}")
        return None

    def extract_from_text(self, filepath):
        """Strategy 2: Extract from text content."""
        try:
            ensure_required_packages()
            with pdfplumber.open(filepath) as pdf:
                for page_num in range(min(5, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    text = page.extract_text()

                    if not text or not text.strip():
                        continue

                    lines = [l.strip() for l in text.split('\n') if l.strip()]

                    # Skip boilerplate pages
                    first_line = lines[0].lower() if lines else ""
                    skip_phrases = [
                        'pure intellectual stimulation',
                        'audiobook reference',
                        'audiobook published',
                        'table of contents',
                        'for personal use only'
                    ]
                    if any(x in first_line for x in skip_phrases):
                        self.log(f"Skipping boilerplate page {page_num + 1}")
                        continue

                    # Look for title pattern
                    title_parts = []
                    for line in lines[:15]:
                        line_lower = line.lower()

                        # Stop conditions
                        stop_phrases = [
                            'copyright', 'all rights reserved', 'printed in the',
                            'www.', '@', 'isbn', 'first edition', 'published by'
                        ]
                        if any(x in line_lower for x in stop_phrases):
                            break
                        if re.match(r'^by\s+[A-Z]', line) and len(line) < 50:
                            break
                        if re.match(r'^\d{4}$', line.strip()):
                            continue

                        # Clean spaced text
                        cleaned = self.clean_spaced_text(line)

                        # Skip non-title content
                        skip_patterns = [
                            r'^fig(ure)?\s*[\d\.]', r'^chapter\s*\d',
                            r'^page\s*\d', r'^topic\s+subtopic',
                            r'^contents$', r'^introduction$',
                            r'^appendix', r'^\d+$', r'^e\dc\d',
                            r'^\(cid:\d+\)'
                        ]
                        if any(re.match(p, cleaned.lower()) for p in skip_patterns):
                            continue

                        if cleaned and 3 < len(cleaned) < 80:
                            title_parts.append(cleaned)

                        if len(title_parts) >= 3:
                            break

                    if title_parts:
                        title = ' '.join(title_parts)
                        title = re.sub(r'\s+', ' ', title)
                        title = re.sub(r'\s+(by|BY)\s+[A-Z][a-zA-Z\s\.]+$', '', title)
                        self.log(f"Found in text (page {page_num + 1}): {title}")
                        return title

        except Exception as e:
            self.log(f"Text extraction failed: {e}")
        return None

    def extract_from_ocr(self, filepath):
        """Strategy 3: Use OCR on rendered PDF pages."""
        if not self.use_ocr:
            return None

        try:
            if not ensure_ocr_packages():
                return None
            self.log("Attempting OCR extraction...")
            images = convert_from_path(filepath, first_page=1, last_page=2, dpi=150)

            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)

                if not text or not text.strip():
                    continue

                lines = [l.strip() for l in text.split('\n') if l.strip()]

                # Skip boilerplate
                first_line = lines[0].lower() if lines else ""
                if any(x in first_line for x in ['audiobook', 'table of contents']):
                    continue

                title_parts = []
                for line in lines[:10]:
                    line_lower = line.lower()

                    if any(x in line_lower for x in ['copyright', 'all rights', 'www.']):
                        break

                    # Clean OCR artifacts
                    cleaned = re.sub(r'[|_~`®©™]', '', line)
                    cleaned = ' '.join(cleaned.split())

                    if cleaned and 3 < len(cleaned) < 80:
                        if re.match(r'^by\s+', cleaned.lower()):
                            continue
                        title_parts.append(cleaned)

                    if len(title_parts) >= 3:
                        break

                if title_parts:
                    title = ' '.join(title_parts)
                    self.log(f"Found via OCR (page {i + 1}): {title}")
                    return title

        except Exception as e:
            self.log(f"OCR extraction failed: {e}")

        return None

    def extract(self, filepath):
        """
        Extract book title using 3-tier fallback.
        Returns tuple of (title, method) or (None, None).
        """
        # Strategy 1: Metadata
        title = self.extract_from_metadata(filepath)
        if title:
            return title, "metadata"

        # Strategy 2: Text extraction
        title = self.extract_from_text(filepath)
        if title:
            return title, "text"

        # Strategy 3: OCR fallback
        title = self.extract_from_ocr(filepath)
        if title:
            return title, "ocr"

        return None, None


@dataclass
class RenamePlan:
    """Planned rename for a single PDF."""

    source: Path
    destination: Path | None
    title: str | None
    method: str | None
    status: str
    detail: str | None = None


@dataclass
class RenameResult:
    """Outcome of executing a rename plan."""

    source: Path
    destination: Path | None
    title: str | None
    method: str | None
    status: str
    detail: str | None = None


def safe_filename(title, max_length=100):
    """Create a safe filename from a title."""
    if not title:
        return None

    # Remove characters not allowed in filenames
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    # Normalize whitespace
    safe = ' '.join(safe.split())
    # Windows forbids trailing spaces and periods
    safe = safe.rstrip(' .')
    # Avoid Windows reserved device names
    if safe.upper() in WINDOWS_RESERVED_NAMES or safe in {".", ".."}:
        safe = f"{safe}_"
    if not safe:
        safe = "untitled"
    # Truncate if too long
    if len(safe) > max_length:
        safe = safe[:max_length].rsplit(' ', 1)[0]
        safe = safe.rstrip(' .') or "untitled"

    return safe.strip()


def find_pdfs(folder, pattern="bk_*"):
    """Find PDFs matching the given pattern."""
    folder = Path(folder)

    if pattern == "bk_*":
        # Default: Audible naming pattern
        return sorted([f for f in folder.iterdir()
                      if f.suffix.lower() == '.pdf' and f.name.startswith('bk_')])
    elif pattern == "*":
        # All PDFs
        return sorted([f for f in folder.iterdir()
                      if f.suffix.lower() == '.pdf'])
    else:
        # Custom pattern
        return sorted(
            f for f in folder.glob(pattern)
            if f.is_file() and f.suffix.lower() == '.pdf'
        )


def validate_folder(folder_path):
    """Validate and normalize the target folder."""
    folder = Path(folder_path)

    if not folder.exists():
        return None, f"Error: Folder not found: {folder}"

    if not folder.is_dir():
        return None, f"Error: Not a directory: {folder}"

    return folder, None


def resolve_destination(pdf_file, title):
    """Resolve a conflict-safe destination beside the source PDF."""
    base = safe_filename(title)
    new_name = f"{base}.pdf"
    new_path = pdf_file.with_name(new_name)

    if new_path.exists() and new_path != pdf_file:
        counter = 2
        while new_path.exists():
            new_name = f"{base} ({counter}).pdf"
            new_path = pdf_file.with_name(new_name)
            counter += 1

    return new_path


def build_rename_plan(pdf_file, extractor):
    """Build a pure rename plan from extraction output."""
    title, method = extractor.extract(pdf_file)

    if not title:
        return RenamePlan(
            source=pdf_file,
            destination=None,
            title=None,
            method=None,
            status="extract_failed",
            detail="Could not determine title",
        )

    destination = resolve_destination(pdf_file, title)
    detail = "already_named" if destination == pdf_file else None

    return RenamePlan(
        source=pdf_file,
        destination=destination,
        title=title,
        method=method,
        status="planned",
        detail=detail,
    )


def execute_rename_plan(plan, dry_run=False):
    """Execute one rename plan and return a structured result."""
    if plan.status != "planned":
        return RenameResult(
            source=plan.source,
            destination=plan.destination,
            title=plan.title,
            method=plan.method,
            status=plan.status,
            detail=plan.detail,
        )

    if dry_run:
        return RenameResult(
            source=plan.source,
            destination=plan.destination,
            title=plan.title,
            method=plan.method,
            status="dry_run",
            detail=plan.detail,
        )

    try:
        if plan.destination != plan.source:
            plan.source.rename(plan.destination)
        return RenameResult(
            source=plan.source,
            destination=plan.destination,
            title=plan.title,
            method=plan.method,
            status="renamed",
            detail=plan.detail,
        )
    except Exception as e:
        return RenameResult(
            source=plan.source,
            destination=plan.destination,
            title=plan.title,
            method=plan.method,
            status="rename_failed",
            detail=str(e),
        )


def rename_pdfs(folder_path, dry_run=False, verbose=False, use_ocr=True, pattern="bk_*"):
    """Main function to rename PDFs in a folder."""
    folder, error = validate_folder(folder_path)
    if error:
        print(error)
        return False

    pdf_files = find_pdfs(folder, pattern)

    if not pdf_files:
        print(f"No PDFs found matching pattern '{pattern}'")
        return False

    try:
        ensure_required_packages()
    except RuntimeError as e:
        print(f"Error: {e}")
        return False

    print(f"Found {len(pdf_files)} PDF(s) to process\n")
    print("=" * 70)

    extractor = TitleExtractor(use_ocr=use_ocr, verbose=verbose)

    successful = []
    failed = []

    for pdf_file in pdf_files:
        print(f"\n{pdf_file.name}")
        plan = build_rename_plan(pdf_file, extractor)
        result = execute_rename_plan(plan, dry_run=dry_run)

        if result.status == "extract_failed":
            print(f"  ✗ {result.detail}")
            failed.append(pdf_file.name)
            continue

        print(f"  → {result.destination.name}")
        print(f"    (extracted via {result.method})")

        if result.status == "dry_run":
            print("    [DRY RUN - not renamed]")
            successful.append((pdf_file.name, result.destination.name))
        elif result.status == "renamed":
            if result.detail == "already_named":
                print("  ✓ Already named correctly")
            else:
                print("  ✓ Renamed successfully")
            successful.append((pdf_file.name, result.destination.name))
        else:
            print(f"  ✗ Rename failed: {result.detail}")
            failed.append(pdf_file.name)

    # Summary
    print("\n" + "=" * 70)
    print(f"\nSummary:")
    print(f"  ✓ {'Would rename' if dry_run else 'Renamed'}: {len(successful)}")
    print(f"  ✗ Failed: {len(failed)}")

    if failed:
        print(f"\nFailed files:")
        for name in failed:
            print(f"  - {name}")

    return len(failed) == 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Rename Audible PDF book notes to their actual titles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/Downloads/Audible
  %(prog)s . --dry-run
  %(prog)s /path/to/pdfs --verbose
  %(prog)s . --pattern "*.pdf"
        """
    )

    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder containing PDFs (default: current directory)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without renaming files"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed extraction information"
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR fallback (faster but may miss some titles)"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="bk_*",
        help="Filename pattern to match (default: bk_*)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    if not args.no_ocr:
        ensure_ocr_packages()

    print(f"Audible PDF Renamer v{__version__}")
    print(f"Folder: {os.path.abspath(args.folder)}")
    print(f"OCR: {'Disabled' if args.no_ocr else ('Available' if OCR_AVAILABLE else 'Not installed')}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be changed)")
    print()

    success = rename_pdfs(
        args.folder,
        dry_run=args.dry_run,
        verbose=args.verbose,
        use_ocr=not args.no_ocr,
        pattern=args.pattern
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
