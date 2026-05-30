# Audible PDF Renamer 1.0.2
Released: 2026-05-30

## Summary
This patch release adds GuideCheck assistant-facing surfaces and follows up on
the residual-risk documentation from 1.0.1. It also makes oversized-PDF skips
more explicit for users and issue triage.

## Changes
- Added byte-identical `assistant-guide.txt` and `.well-known/assistant-guide.txt`.
- Added `llms.txt` with GuideCheck discovery and safety notes.
- Updated README, CONTRIBUTING, and issue templates with privacy and residual
  PDF-parser risk guidance.
- Changed oversized-PDF planning to return `skipped_resource_limit` with a
  specific user-visible reason.
- Bumped package and CLI version to 1.0.2.

## Verification
- `pytest -q`: 30 passed
- `python3 -m compileall audible_pdf_renamer.py`: passed
- `git diff --check`: passed
- `pyproject.toml` parsed with `tomllib`: passed
- GuideCheck byte-profile checks passed locally for both assistant-guide copies.

## Residual risk
GuideCheck conformance is form evidence, not a safety guarantee. PDF parsing and
OCR still rely on local third-party libraries and system tools. Users should run
`--dry-run --verbose` before renaming a new batch, avoid untrusted PDFs, and
redact private verbose output before posting issues.
