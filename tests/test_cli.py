import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "audible_pdf_renamer.py"


def run_with_blocked_pdf_imports(*args):
    code = f"""
import builtins
import runpy
import sys

real_import = builtins.__import__
blocked = {{"pdfplumber", "pypdf"}}

def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in blocked:
        raise ImportError(f"No module named '{{name}}'")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = fake_import
sys.argv = { [str(SCRIPT), *args]!r }
runpy.run_path({str(SCRIPT)!r}, run_name="__main__")
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )


def test_help_works_without_pdf_dependencies():
    result = run_with_blocked_pdf_imports("--help")

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--dry-run" in result.stdout


def test_version_works_without_pdf_dependencies():
    result = run_with_blocked_pdf_imports("--version")

    assert result.returncode == 0
    assert "audible_pdf_renamer.py 1.0.0" in result.stdout


def test_missing_required_deps_fail_when_execution_needs_them(tmp_path):
    (tmp_path / "bk_alpha_001.pdf").write_bytes(b"%PDF-1.4\n")

    result = run_with_blocked_pdf_imports(str(tmp_path))

    assert result.returncode == 1
    assert "Required package not found" in result.stdout


def test_missing_folder_returns_nonzero_exit_code():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(REPO_ROOT / "does-not-exist")],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Folder not found" in result.stdout


def test_no_matching_files_returns_nonzero_exit_code(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "No PDFs found matching pattern" in result.stdout
