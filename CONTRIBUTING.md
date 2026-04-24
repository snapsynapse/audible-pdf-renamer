# Contributing to Audible PDF Renamer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Ways to Contribute

- **Report bugs**: Open an issue describing the problem
- **Suggest features**: Open an issue with your idea
- **Improve documentation**: Fix typos, clarify instructions, add examples
- **Submit code**: Fix bugs or implement new features

## Reporting Bugs

When reporting a bug, please include:

1. **Python version**: `python --version`
2. **Package versions**: `pip list | grep -E "pdfplumber|pypdf|pytesseract|pdf2image"`
3. **Operating system**: macOS, Windows, Linux distribution
4. **Steps to reproduce**: What commands did you run?
5. **Expected vs actual behavior**: What did you expect? What happened?
6. **Sample PDF info** (if applicable): Publisher, type of content (text/images), any identifying info

**Note**: Please don't upload copyrighted PDF files. Instead, describe the PDF's characteristics.

## Suggesting Features

Feature suggestions are welcome! Please:

1. Check existing issues first to avoid duplicates
2. Describe the use case: Why would this feature be helpful?
3. Provide examples if possible

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/yourusername/audible-pdf-renamer.git
   cd audible-pdf-renamer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies:
   ```bash
   pip install pytest black flake8
   ```

## Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://github.com/psf/black) for formatting: `black audible_pdf_renamer.py`
- Run linting before committing: `flake8 audible_pdf_renamer.py`

## Submitting Pull Requests

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Test your changes:
   ```bash
   # Run the automated eval suite
   pytest -q

   # Run with --dry-run on sample PDFs
   python audible_pdf_renamer.py /path/to/test/pdfs --dry-run --verbose
   ```

4. Format and lint:
   ```bash
   black audible_pdf_renamer.py
   flake8 audible_pdf_renamer.py
   ```

5. Commit with a clear message:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

6. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- Keep changes focused: One feature or fix per PR
- Update documentation if needed
- Add comments for complex logic
- Test with various PDF types if modifying extraction logic

## Areas for Contribution

Here are some areas where contributions would be especially welcome:

### Title Extraction Improvements
- Better handling of specific publishers' formats
- Improved OCR post-processing
- Support for non-English titles

### New Features
- GUI interface
- Batch processing with progress bar
- Configuration file support
- Undo/rollback functionality

### Documentation
- More usage examples
- Troubleshooting guides
- Translation to other languages

### Testing
- Unit tests for extraction methods
- Integration tests
- Test fixtures (mock PDFs)

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to make a useful tool better!
