from pathlib import Path
import zipfile
# Central data root (single source of truth)
DATA_ROOT = Path("WebAPP", "DataStorage").resolve()

def safe_join(base: Path, *paths: str) -> Path:
    base = base.resolve()
    target = (base / Path(*paths)).resolve()

    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal detected")

    return target


def safe_extract_zip(zip_path: Path, extract_to: Path) -> None:
    extract_to = extract_to.resolve()

    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            # Validate destination path BEFORE extraction
            safe_join(extract_to, member.filename)

        # Only extract after all paths are validated
        zf.extractall(extract_to)

def safe_case_path(case: str) -> Path:
    """
    Resolve a case path and ensure it stays inside DataStorage.
    """
    target = (DATA_ROOT / case).resolve()

    if not str(target).startswith(str(DATA_ROOT)):
        raise ValueError("Invalid path")

    return target