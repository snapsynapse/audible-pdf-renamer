# Audible PDF Renamer 1.0.1
Released: 2026-05-30

## Summary
This hardening release treats PDF metadata, extracted text, OCR text, filenames, and terminal output as untrusted input. It adds structural filename sanitization, terminal-safe display escaping, local PDF resource limits, OCR timeouts, package metadata, bounded dependency ranges, and focused regression evals.

## Security hardening
- Strips unsafe Unicode control, format, and surrogate characters before deriving output filenames.
- Escapes terminal control characters when displaying untrusted PDF-derived or filesystem-derived text.
- Handles Windows reserved device stems such as `CON.txt` and `COM1.anything`.
- Avoids hidden/path-like output names by trimming leading dots.
- Rejects PDFs larger than 250 MiB before parser/OCR work.
- Skips text extraction for PDFs over 500 pages.
- Skips oversized first pages during text extraction.
- Applies OCR render and Tesseract timeouts.
- Skips encrypted PDFs during metadata extraction.
- Loads OCR dependencies at extraction time for library callers.

## Verification
- `pytest -q`: 29 passed
- `python3 -m compileall audible_pdf_renamer.py`: passed
- `git diff --check`: passed
- `pyproject.toml` parsed with `tomllib`: passed
- Targeted adversarial checks covered terminal-control titles, Windows device stems, hidden-dot names, zero-width display escaping, OCR lazy loading, oversized PDFs, oversized pages, encrypted metadata, and OCR timeout propagation.

## Residual risk
PDF parsing and OCR still rely on local third-party libraries and system tools. The tool now applies local resource boundaries, but users should continue to run `--dry-run --verbose` before renaming a new batch and avoid processing PDFs from sources they do not trust.
