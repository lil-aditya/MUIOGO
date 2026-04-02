from __future__ import annotations

import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def resolve_git_dir(root: Path) -> Path | None:
    git_path = root / ".git"
    if git_path.is_dir():
        return git_path
    if not git_path.is_file():
        return None

    try:
        first_line = git_path.read_text(encoding="utf-8").splitlines()[0].strip()
    except (IndexError, OSError):
        return None

    prefix = "gitdir:"
    if not first_line.lower().startswith(prefix):
        return None

    git_dir = first_line[len(prefix) :].strip()
    candidate = Path(git_dir)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    return candidate


def iter_repo_files(root: Path, suffixes: set[str]) -> Iterable[Path]:
    git_list = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        capture_output=True,
        check=False,
    )
    if git_list.returncode == 0:
        for raw_path in git_list.stdout.split(b"\x00"):
            if not raw_path:
                continue
            path = root / raw_path.decode("utf-8", "surrogateescape")
            if path.suffix.lower() not in suffixes:
                continue
            # Apply skip filtering to paths *within the repo*, not absolute paths.
            rel_parts = path.relative_to(root).parts
            if any(part in SKIP_DIR_NAMES for part in rel_parts):
                continue
            yield path
        return

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix.lower() not in suffixes:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIR_NAMES for part in rel_parts):
            continue
        yield path


def check_unresolved_git_state(root: Path) -> list[str]:
    git_dir = resolve_git_dir(root)
    if git_dir is None:
        return ["Git metadata not found; cannot verify merge or rebase state."]

    issues: list[str] = []
    markers = (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "REBASE_HEAD",
    )
    for marker in markers:
        if (git_dir / marker).exists():
            issues.append(f"Git operation in progress: {git_dir / marker}")

    for rebase_dir in ("rebase-apply", "rebase-merge"):
        if (git_dir / rebase_dir).exists():
            issues.append(f"Git rebase in progress: {git_dir / rebase_dir}")

    return issues


def check_conflict_markers(root: Path) -> list[str]:
    hits: list[str] = []

    for path in iter_repo_files(root, TEXT_EXTENSIONS):
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                for line_number, line in enumerate(handle, start=1):
                    stripped = line.lstrip()
                    if stripped.startswith("<<<<<<<"):
                        hits.append(f"{path.relative_to(root)}:{line_number}")
                        break
        except OSError as exc:
            hits.append(f"{path.relative_to(root)}: unreadable ({exc})")

    return hits


def run_py_compile(root: Path) -> list[str]:
    failures: list[str] = []
    python_files = list(iter_repo_files(root, {".py"}))

    for path in python_files:
        file_descriptor, temp_path = tempfile.mkstemp(
            prefix="verify-clean-base-",
            suffix=".pyc",
        )
        os.close(file_descriptor)
        try:
            py_compile.compile(
                str(path),
                cfile=temp_path,
                doraise=True,
            )
        except (OSError, py_compile.PyCompileError) as exc:
            failures.append(f"{path.relative_to(root)}: {exc}")
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return failures


def run_smoke_tests(root: Path) -> int:
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests_smoke",
        "-p",
        "test_*.py",
    ]
    process = subprocess.run(command, cwd=root)
    return process.returncode


def main() -> int:
    # Do not allow any verification step to emit __pycache__ into the repo.
    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        print(f"[verify] repo root: {REPO_ROOT}")

        git_state = check_unresolved_git_state(REPO_ROOT)
        if git_state:
            print("[FAIL] unresolved git state detected:")
            for issue in git_state:
                print(f"  - {issue}")
            return 1
        print("[OK] git state: clean")

        conflicts = check_conflict_markers(REPO_ROOT)
        if conflicts:
            print("[FAIL] conflict markers found:")
            for conflict in conflicts:
                print(f"  - {conflict}")
            return 1
        print("[OK] no conflict markers found")

        compile_failures = run_py_compile(REPO_ROOT)
        if compile_failures:
            print("[FAIL] python compile step failed:")
            for failure in compile_failures:
                print(f"  - {failure}")
            return 1
        print("[OK] python compile step passed")

        smoke_status = run_smoke_tests(REPO_ROOT)
        if smoke_status != 0:
            print(f"[FAIL] smoke tests failed (rc={smoke_status})")
            return smoke_status
        print("[OK] smoke tests passed")

        print("[SUCCESS] clean-base verification passed")
        return 0
    finally:
        sys.dont_write_bytecode = old_dont_write


if __name__ == "__main__":
    raise SystemExit(main())
