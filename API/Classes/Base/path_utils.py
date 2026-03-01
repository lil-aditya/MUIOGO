from pathlib import Path
import zipfile
from Classes.Base import Config


def safe_join(base: Path, *paths: str) -> Path:
    base = base.resolve()
    target = (base / Path(*paths)).resolve()

    if not target.is_relative_to(base):
        raise ValueError("Path traversal detected")

    return target


def safe_extract_zip(zip_path: Path) -> None:
    # The ONLY allowed extraction root — never the project root
    base_dir = Path(Config.DATA_STORAGE).resolve()

    with zipfile.ZipFile(zip_path) as zf:
        # VALIDATION PASS — check all entries before extracting any
        for member in zf.infolist():
            member_path = Path(member.filename)

            # 1. Reject absolute paths
            if member_path.is_absolute():
                raise ValueError(f"Absolute path in ZIP: {member.filename}")

            # 2. Reject obvious traversal attempts in raw path
            if ".." in member_path.parts:
                raise ValueError(f"Path traversal in ZIP: {member.filename}")

            # 3. Resolve final target path and enforce containment
            target_path = (base_dir / member_path).resolve()
            if not target_path.is_relative_to(base_dir):
                raise ValueError(f"ZIP entry escapes DATA_STORAGE: {member.filename}")

        # EXTRACTION PASS — only after ALL entries validated
        zf.extractall(base_dir)


def safe_case_path(case: str) -> Path:
    base = Path(Config.DATA_STORAGE).resolve()
    target = (base / case).resolve()

    if not target.is_relative_to(base):
        raise ValueError(f"Invalid case path: {case}")

    return target