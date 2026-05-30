# Changelog

## 1.0.1 - 2026-05-30
- Harden filename sanitization for control characters, leading-dot names, and Windows reserved device stems.
- Escape terminal control characters in verbose and rename output.
- Load OCR dependencies at extraction time for library callers, not only through the CLI startup path.
- Add resource limits for untrusted PDFs: 250 MiB maximum file size, 500 page maximum for text extraction, oversized-page skipping, and OCR timeouts.
- Add regression coverage for filename sanitization, terminal escaping, OCR initialization, and resource-limit behavior.
- Bound dependency ranges and add package metadata for reproducible release review.

## 1.0.0 - 2026-01-13
- Initial release.
