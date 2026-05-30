from pathlib import Path

import audible_pdf_renamer as renamer


class FakePage:
    def __init__(self, text, width=612, height=792):
        self._text = text
        self.width = width
        self.height = height

    def extract_text(self):
        return self._text


class FakePDF:
    def __init__(self, pages):
        self.pages = [
            page if isinstance(page, FakePage) else FakePage(page)
            for page in pages
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePdfPlumber:
    def __init__(self, pages):
        self._pages = pages

    def open(self, _filepath):
        return FakePDF(self._pages)


class FakeReader:
    def __init__(self, _filepath):
        self.metadata = type("Meta", (), {"title": "Misbehaving"})()
        self.is_encrypted = False


class FakeEncryptedReader:
    def __init__(self, _filepath):
        self.metadata = type("Meta", (), {"title": "Encrypted Title"})()
        self.is_encrypted = True


def test_extract_from_metadata_uses_valid_title(monkeypatch):
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "PdfReader", FakeReader)

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_metadata(Path("dummy.pdf")) == "Misbehaving"


def test_extract_from_metadata_skips_encrypted_pdfs(monkeypatch):
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "PdfReader", FakeEncryptedReader)

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_metadata(Path("dummy.pdf")) is None


def test_extract_from_text_skips_boilerplate_and_author_lines(monkeypatch):
    pages = [
        "Pure Intellectual Stimulation\nreference material",
        "T H I N K I N G\nFast and Slow\nby Daniel Kahneman\ncopyright 2011",
    ]
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "pdfplumber", FakePdfPlumber(pages))

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_text(Path("dummy.pdf")) == "THINKING Fast and Slow"


def test_extract_from_text_skips_pdfs_over_page_limit(monkeypatch):
    pages = ["Useful Title"] * 3
    monkeypatch.setattr(renamer, "MAX_PDF_PAGES", 2)
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "pdfplumber", FakePdfPlumber(pages))

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_text(Path("dummy.pdf")) is None


def test_extract_from_text_skips_oversized_pages(monkeypatch):
    class ExplodingPage(FakePage):
        def extract_text(self):
            raise AssertionError("oversized page should not be extracted")

    pages = [ExplodingPage("Hidden Title", width=100, height=100)]
    monkeypatch.setattr(renamer, "MAX_PAGE_AREA", 1)
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "pdfplumber", FakePdfPlumber(pages))

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_text(Path("dummy.pdf")) is None


def test_extract_from_ocr_uses_second_page_when_first_is_boilerplate(monkeypatch):
    class FakeTesseract:
        @staticmethod
        def image_to_string(image, **_kwargs):
            return image

    monkeypatch.setattr(renamer, "OCR_AVAILABLE", True)
    monkeypatch.setattr(renamer, "ensure_ocr_packages", lambda: True)
    monkeypatch.setattr(renamer, "convert_from_path", lambda *args, **kwargs: [
        "Audiobook companion guide",
        "Leonardo\nda Vinci\nby Walter Isaacson",
    ])
    monkeypatch.setattr(renamer, "pytesseract", FakeTesseract)

    extractor = renamer.TitleExtractor(use_ocr=True)

    assert extractor.extract_from_ocr(Path("dummy.pdf")) == "Leonardo da Vinci"


def test_extract_from_ocr_loads_packages_after_extractor_creation(monkeypatch):
    class FakeTesseract:
        @staticmethod
        def image_to_string(image, **_kwargs):
            return image

    calls = []

    def fake_ensure_ocr_packages():
        calls.append("loaded")
        monkeypatch.setattr(renamer, "OCR_AVAILABLE", True)
        return True

    monkeypatch.setattr(renamer, "OCR_AVAILABLE", False)
    monkeypatch.setattr(renamer, "ensure_ocr_packages", fake_ensure_ocr_packages)
    monkeypatch.setattr(renamer, "convert_from_path", lambda *args, **kwargs: [
        "Title From OCR",
    ])
    monkeypatch.setattr(renamer, "pytesseract", FakeTesseract)

    extractor = renamer.TitleExtractor(use_ocr=True)

    assert extractor.extract_from_ocr(Path("dummy.pdf")) == "Title From OCR"
    assert calls == ["loaded"]


def test_extract_from_ocr_passes_timeout_to_renderer_and_tesseract(monkeypatch):
    observed = {}

    class FakeTesseract:
        @staticmethod
        def image_to_string(image, **kwargs):
            observed["tesseract_timeout"] = kwargs.get("timeout")
            return image

    def fake_convert_from_path(*_args, **kwargs):
        observed["render_timeout"] = kwargs.get("timeout")
        return ["Title From OCR"]

    monkeypatch.setattr(renamer, "OCR_AVAILABLE", True)
    monkeypatch.setattr(renamer, "OCR_TIMEOUT_SECONDS", 7)
    monkeypatch.setattr(renamer, "ensure_ocr_packages", lambda: True)
    monkeypatch.setattr(renamer, "convert_from_path", fake_convert_from_path)
    monkeypatch.setattr(renamer, "pytesseract", FakeTesseract)

    extractor = renamer.TitleExtractor(use_ocr=True)

    assert extractor.extract_from_ocr(Path("dummy.pdf")) == "Title From OCR"
    assert observed == {"render_timeout": 7, "tesseract_timeout": 7}


def test_extract_returns_none_when_all_strategies_fail(monkeypatch):
    extractor = renamer.TitleExtractor(use_ocr=True)
    monkeypatch.setattr(extractor, "extract_from_metadata", lambda _filepath: None)
    monkeypatch.setattr(extractor, "extract_from_text", lambda _filepath: None)
    monkeypatch.setattr(extractor, "extract_from_ocr", lambda _filepath: None)

    assert extractor.extract(Path("dummy.pdf")) == (None, None)
