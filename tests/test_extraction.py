from pathlib import Path

import audible_pdf_renamer as renamer


class FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class FakePDF:
    def __init__(self, pages):
        self.pages = [FakePage(text) for text in pages]

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


def test_extract_from_metadata_uses_valid_title(monkeypatch):
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "PdfReader", FakeReader)

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_metadata(Path("dummy.pdf")) == "Misbehaving"


def test_extract_from_text_skips_boilerplate_and_author_lines(monkeypatch):
    pages = [
        "Pure Intellectual Stimulation\nreference material",
        "T H I N K I N G\nFast and Slow\nby Daniel Kahneman\ncopyright 2011",
    ]
    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(renamer, "pdfplumber", FakePdfPlumber(pages))

    extractor = renamer.TitleExtractor()

    assert extractor.extract_from_text(Path("dummy.pdf")) == "THINKING Fast and Slow"


def test_extract_from_ocr_uses_second_page_when_first_is_boilerplate(monkeypatch):
    class FakeTesseract:
        @staticmethod
        def image_to_string(image):
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


def test_extract_returns_none_when_all_strategies_fail(monkeypatch):
    extractor = renamer.TitleExtractor(use_ocr=True)
    monkeypatch.setattr(extractor, "extract_from_metadata", lambda _filepath: None)
    monkeypatch.setattr(extractor, "extract_from_text", lambda _filepath: None)
    monkeypatch.setattr(extractor, "extract_from_ocr", lambda _filepath: None)

    assert extractor.extract(Path("dummy.pdf")) == (None, None)
