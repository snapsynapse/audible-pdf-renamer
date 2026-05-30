from pathlib import Path

import audible_pdf_renamer as renamer


def create_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n")


def test_rename_pdfs_renames_top_level_files(monkeypatch, tmp_path, capsys):
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(source)

    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(
        renamer.TitleExtractor,
        "extract",
        lambda self, filepath: ("Misbehaving", "metadata"),
    )

    assert renamer.rename_pdfs(tmp_path) is True
    assert not source.exists()
    assert (tmp_path / "Misbehaving.pdf").exists()

    out = capsys.readouterr().out
    assert "Renamed: 1" in out


def test_rename_pdfs_dry_run_does_not_mutate_files(monkeypatch, tmp_path):
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(source)

    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(
        renamer.TitleExtractor,
        "extract",
        lambda self, filepath: ("Thinking Fast and Slow", "text"),
    )

    assert renamer.rename_pdfs(tmp_path, dry_run=True) is True
    assert source.exists()
    assert not (tmp_path / "Thinking Fast and Slow.pdf").exists()


def test_rename_pdfs_adds_numeric_suffix_for_conflicts(monkeypatch, tmp_path):
    existing = tmp_path / "Misbehaving.pdf"
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(existing)
    create_pdf(source)

    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(
        renamer.TitleExtractor,
        "extract",
        lambda self, filepath: ("Misbehaving", "metadata"),
    )

    assert renamer.rename_pdfs(tmp_path) is True
    assert (tmp_path / "Misbehaving.pdf").exists()
    assert (tmp_path / "Misbehaving (2).pdf").exists()


def test_build_rename_plan_reports_extraction_failure(monkeypatch, tmp_path):
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(source)
    extractor = renamer.TitleExtractor()
    monkeypatch.setattr(extractor, "extract", lambda filepath: (None, None))

    plan = renamer.build_rename_plan(source, extractor)

    assert plan.status == "extract_failed"
    assert plan.destination is None
    assert plan.detail == "Could not determine title"


def test_build_rename_plan_marks_already_named_files(monkeypatch, tmp_path):
    source = tmp_path / "Deep Work.pdf"
    create_pdf(source)
    extractor = renamer.TitleExtractor()
    monkeypatch.setattr(extractor, "extract", lambda filepath: ("Deep Work", "text"))

    plan = renamer.build_rename_plan(source, extractor)

    assert plan.status == "planned"
    assert plan.destination == source
    assert plan.detail == "already_named"


def test_execute_rename_plan_returns_structured_dry_run(monkeypatch, tmp_path):
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(source)
    extractor = renamer.TitleExtractor()
    monkeypatch.setattr(extractor, "extract", lambda filepath: ("Deep Work", "text"))
    plan = renamer.build_rename_plan(source, extractor)

    result = renamer.execute_rename_plan(plan, dry_run=True)

    assert result.status == "dry_run"
    assert result.destination == tmp_path / "Deep Work.pdf"
    assert source.exists()


def test_recursive_patterns_preserve_source_directory(monkeypatch, tmp_path):
    nested = tmp_path / "subdir" / "book.pdf"
    create_pdf(nested)

    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(
        renamer.TitleExtractor,
        "extract",
        lambda self, filepath: ("Deep Work", "text"),
    )

    assert renamer.rename_pdfs(tmp_path, pattern="**/*.pdf") is True
    assert not nested.exists()
    assert (tmp_path / "subdir" / "Deep Work.pdf").exists()
    assert not (tmp_path / "Deep Work.pdf").exists()


def test_find_pdfs_custom_pattern_only_returns_pdf_files(tmp_path):
    create_pdf(tmp_path / "root.pdf")
    create_pdf(tmp_path / "nested" / "child.pdf")
    (tmp_path / "notes.txt").write_text("not a pdf")
    (tmp_path / "folder_only").mkdir()

    matches = renamer.find_pdfs(tmp_path, "**/*")

    assert [path.relative_to(tmp_path).as_posix() for path in matches] == [
        "nested/child.pdf",
        "root.pdf",
    ]


def test_safe_filename_handles_cross_platform_edge_cases():
    assert renamer.safe_filename('AUX<>:"/\\\\|?*') == "AUX_"
    assert renamer.safe_filename("Title. ") == "Title"
    assert renamer.safe_filename("..") == "untitled"
    assert renamer.safe_filename("CON.txt") == "CON.txt_"
    assert renamer.safe_filename("COM1.anything") == "COM1.anything_"
    assert renamer.safe_filename("\x1b[31mRed Title") == "[31mRed Title"
    assert renamer.safe_filename(".hidden") == "hidden"


def test_safe_filename_truncates_long_titles_deterministically():
    title = "A Very Long Book Title " * 10

    result = renamer.safe_filename(title, max_length=40)

    assert result == "A Very Long Book Title A Very Long Book"
    assert len(result) <= 40


def test_safe_filename_preserves_unicode_titles():
    assert renamer.safe_filename("Sapiens 中文 edición") == "Sapiens 中文 edición"
    assert renamer.safe_filename("The Con Artist") == "The Con Artist"
    assert renamer.safe_filename("Auxiliary Memory") == "Auxiliary Memory"


def test_validate_folder_distinguishes_missing_and_non_directory(tmp_path):
    missing_folder, missing_error = renamer.validate_folder(tmp_path / "missing")
    file_path = tmp_path / "not-a-dir.txt"
    file_path.write_text("x")
    non_dir_folder, non_dir_error = renamer.validate_folder(file_path)

    assert missing_folder is None
    assert "Folder not found" in missing_error
    assert non_dir_folder is None
    assert "Not a directory" in non_dir_error


def test_safe_display_escapes_terminal_control_sequences():
    assert renamer.safe_display("\x1b[31mRed Title") == "\\x1b[31mRed Title"
    assert renamer.safe_display("Zero\u200bWidth") == "Zero\\u200bWidth"


def test_resource_limit_rejects_oversized_pdf(monkeypatch, tmp_path):
    source = tmp_path / "bk_large.pdf"
    create_pdf(source)
    monkeypatch.setattr(renamer, "MAX_PDF_BYTES", 1)

    extractor = renamer.TitleExtractor(use_ocr=False)

    assert extractor.extract(source) == (None, None)


def test_build_rename_plan_reports_resource_limit(monkeypatch, tmp_path):
    source = tmp_path / "bk_large.pdf"
    create_pdf(source)
    monkeypatch.setattr(renamer, "MAX_PDF_BYTES", 1)
    extractor = renamer.TitleExtractor(use_ocr=False)

    plan = renamer.build_rename_plan(source, extractor)

    assert plan.status == "skipped_resource_limit"
    assert plan.destination is None
    assert plan.detail == "PDF exceeds 0 MiB resource limit"


def test_rename_output_escapes_control_characters(monkeypatch, tmp_path, capsys):
    source = tmp_path / "bk_alpha_001.pdf"
    create_pdf(source)

    monkeypatch.setattr(renamer, "ensure_required_packages", lambda: None)
    monkeypatch.setattr(
        renamer.TitleExtractor,
        "extract",
        lambda self, filepath: ("\x1b[31mRed Title", "metadata"),
    )

    assert renamer.rename_pdfs(tmp_path, dry_run=True) is True

    out = capsys.readouterr().out
    assert "[31mRed Title.pdf" in out
    assert "\x1b[31mRed Title.pdf" not in out
