---
name: Title Extraction Issue
about: Report a PDF where the title wasn't extracted correctly
title: '[EXTRACTION] '
labels: extraction
assignees: ''
---

## PDF Details
- **Publisher/Source**: [e.g., Audible, O'Reilly, Penguin]
- **Original filename**: [e.g., bk_adbl_123456.pdf]
- **Actual book title**: [What the title should be]
- **Extracted title**: [What the tool extracted, or "None" if it failed]

## Content Type
- [ ] Text-based (can select/copy text in PDF viewer)
- [ ] Image-based (text appears as images)
- [ ] Mixed

## Extraction Method Tried
Which methods did the tool attempt? (Run with `--verbose` to see)
- [ ] Metadata
- [ ] Text extraction
- [ ] OCR

## Verbose Output
Run with `--verbose` and paste the output:
```
python audible_pdf_renamer.py --verbose --dry-run

[Paste output here]
```

## PDF Structure
Describe what's on the first few pages:
- Page 1: [e.g., "Title page with book cover image"]
- Page 2: [e.g., "Copyright page"]
- Page 3: [e.g., "Table of contents"]

## Additional Context
Any other information that might help fix the extraction.

**Note**: Please don't upload copyrighted PDFs. The description above should be enough to diagnose the issue.
