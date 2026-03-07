"""
Uninstaller for MUIOGO setup-created local state.
Reverses changes made by scripts/setup_dev.py, scripts/setup.sh, and scripts/setup.bat.

Usage:
    python scripts/uninstall_dev.py [--remove-solvers] [--dry-run] [--yes]
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VENV_DIR = Path.home() / ".venvs" / "muiogo"
ENV_FILE = REPO_ROOT / ".env"
DEMO_MARKER = REPO_ROOT / "WebApp" / "DataStorage" / ".demo_data_installed.json"
DEMO_DATA_DIR = REPO_ROOT / "WebApp" / "DataStorage" / "CLEWs Demo"

WINDOWS_SOLVER_DIRS = []
if platform.system() == "Windows":
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        WINDOWS_SOLVER_DIRS = [
            Path(local_app) / "glpk",
            Path(local_app) / "cbc",
        ]

# Env var keys that setup may have written to .env
SETUP_ENV_KEYS = [
    "MUIOGO_SECRET_KEY",
    "SOLVER_GLPK_PATH",
    "SOLVER_CBC_PATH",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class Style:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def info(msg):
    print(f"{Style.BLUE}[INFO]{Style.RESET}  {msg}")


def warn(msg):
    print(f"{Style.YELLOW}[WARN]{Style.RESET}  {msg}")


def success(msg):
    print(f"{Style.GREEN}[ OK ]{Style.RESET}  {msg}")


def error(msg):
    print(f"{Style.RED}[ERR ]{Style.RESET}  {msg}")


def confirm(prompt, auto_yes=False):
    if auto_yes:
        print(f"{prompt} [auto-yes]")
        return True
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def safe_rmtree(path, dry_run=False, label=None):
    """Remove a directory tree with safety checks."""
    label = label or str(path)
    if not path.exists():
        info(f"Already absent: {label}")
        return
    # Safety: refuse to delete if path is root, home, or very short
    resolved = path.resolve()
    if resolved == Path.home() or resolved == Path("/") or len(resolved.parts) <= 2:
        error(f"Refusing to delete unsafe path: {resolved}")
        return
    if dry_run:
        info(f"[DRY-RUN] Would remove directory: {resolved}")
        return
    try:
        shutil.rmtree(resolved)
        success(f"Removed: {label}")
    except Exception as e:
        error(f"Failed to remove {label}: {e}")


def safe_rm(path, dry_run=False, label=None):
    """Remove a single file."""
    label = label or str(path)
    if not path.exists():
        info(f"Already absent: {label}")
        return
    if dry_run:
        info(f"[DRY-RUN] Would remove file: {path}")
        return
    path.unlink()
    success(f"Removed: {label}")


# ---------------------------------------------------------------------------
# Uninstall steps
# ---------------------------------------------------------------------------
def get_venv_dir():
    """Determine the venv directory from env or default."""
    custom = os.environ.get("MUIOGO_VENV_DIR")
    if custom:
        return Path(custom)
    # Also check .env file
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("MUIOGO_VENV_DIR="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return Path(val)
    return DEFAULT_VENV_DIR


def remove_venv(dry_run=False):
    """Remove the MUIOGO virtual environment."""
    venv_dir = get_venv_dir()
    print(f"\n{Style.BOLD}1. Virtual Environment{Style.RESET}")
    info(f"Venv path: {venv_dir}")
    safe_rmtree(venv_dir, dry_run, label="MUIOGO virtual environment")


def remove_env_file(dry_run=False):
    """Remove setup-created .env entries or the entire .env if it's all setup content."""
    print(f"\n{Style.BOLD}2. Repository .env File{Style.RESET}")
    if not ENV_FILE.exists():
        info(".env file does not exist — nothing to do.")
        return

    lines = ENV_FILE.read_text().splitlines()
    remaining = []
    removed = []

    for line in lines:
        stripped = line.strip()
        # Keep blank lines and comments not from setup
        if stripped == "" or stripped.startswith("#"):
            remaining.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in SETUP_ENV_KEYS:
            removed.append(line)
        else:
            remaining.append(line)

    if removed:
        info("Removing setup-created .env entries:")
        for r in removed:
            info(f"  - {r.strip()}")

    # If nothing meaningful remains, remove the whole file
    meaningful = [l for l in remaining if l.strip() and not l.strip().startswith("#")]
    if not meaningful:
        safe_rm(ENV_FILE, dry_run, label=".env file (all entries were setup-created)")
    elif removed:
        if dry_run:
            info("[DRY-RUN] Would rewrite .env without setup entries.")
        else:
            ENV_FILE.write_text("\n".join(remaining) + "\n")
            success("Rewrote .env without setup entries.")
    else:
        info(".env has no setup-created entries — leaving as-is.")


def remove_demo_data(dry_run=False):
    """Remove demo data and its marker file."""
    print(f"\n{Style.BOLD}3. Demo Data{Style.RESET}")
    safe_rm(DEMO_MARKER, dry_run, label="Demo install marker")
    safe_rmtree(DEMO_DATA_DIR, dry_run, label="Demo data directory")


def remove_windows_solver_dirs(dry_run=False):
    """Remove manually installed solver directories on Windows."""
    print(f"\n{Style.BOLD}4. Windows Manual Solver Installs{Style.RESET}")
    if platform.system() != "Windows":
        info("Not Windows — skipping.")
        return
    for solver_dir in WINDOWS_SOLVER_DIRS:
        safe_rmtree(solver_dir, dry_run, label=f"Solver directory: {solver_dir.name}")


def remove_windows_env_vars(dry_run=False):
    """Remove Windows user environment variables and PATH entries created by setup."""
    print(f"\n{Style.BOLD}5. Windows User Environment Variables{Style.RESET}")
    if platform.system() != "Windows":
        info("Not Windows — skipping.")
        return

    try:
        import winreg
    except ImportError:
        warn("winreg not available — cannot modify Windows environment.")
        return

    env_key = r"Environment"
    vars_to_remove = ["GLPK_PATH", "CBC_PATH"]

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, env_key, 0, winreg.KEY_ALL_ACCESS
        ) as key:
            # Remove individual env vars
            for var_name in vars_to_remove:
                try:
                    winreg.QueryValueEx(key, var_name)
                    if dry_run:
                        info(f"[DRY-RUN] Would remove env var: {var_name}")
                    else:
                        winreg.DeleteValue(key, var_name)
                        success(f"Removed user env var: {var_name}")
                except FileNotFoundError:
                    info(f"Env var {var_name} not set — skipping.")

            # Clean PATH entries pointing to our solver dirs
            try:
                current_path, reg_type = winreg.QueryValueEx(key, "Path")
                path_parts = current_path.split(";")
                original_count = len(path_parts)

                cleaned_parts = []
                removed_parts = []
                for part in path_parts:
                    part_lower = part.strip().lower()
                    is_solver_path = any(
                        part_lower.startswith(str(sd).lower()) for sd in WINDOWS_SOLVER_DIRS
                    )
                    if is_solver_path:
                        removed_parts.append(part)
                    else:
                        cleaned_parts.append(part)

                if removed_parts:
                    info("Removing PATH entries:")
                    for rp in removed_parts:
                        info(f"  - {rp}")
                    if dry_run:
                        info("[DRY-RUN] Would update user PATH.")
                    else:
                        new_path = ";".join(cleaned_parts)
                        winreg.SetValueEx(key, "Path", 0, reg_type, new_path)
                        success("Updated user PATH.")
                else:
                    info("No solver-related PATH entries found.")
            except FileNotFoundError:
                info("No user PATH variable found.")

    except OSError as e:
        error(f"Failed to access Windows registry: {e}")

    # Broadcast environment change
    if not dry_run:
        try:
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0x0002, 5000, None
            )
            info("Broadcast environment change to Windows.")
        except Exception:
            warn("Could not broadcast env change — you may need to restart your shell.")


def remove_package_manager_solvers(dry_run=False, auto_yes=False):
    """Opt-in removal of solver packages installed via package managers."""
    print(f"\n{Style.BOLD}6. Package Manager Solver Packages (opt-in){Style.RESET}")
    warn("These packages may be shared with other software on your system.")
    warn("Removal is opt-in and requires explicit confirmation.\n")

    system = platform.system()

    if system == "Darwin":
        _uninstall_brew_packages(["glpk", "cbc"], dry_run, auto_yes)
    elif system == "Linux":
        _uninstall_linux_packages(dry_run, auto_yes)
    elif system == "Windows":
        _uninstall_choco_packages(["glpk", "cbc"], dry_run, auto_yes)
    else:
        info(f"Unsupported platform '{system}' — skipping package removal.")


def _uninstall_brew_packages(packages, dry_run, auto_yes):
    if not shutil.which("brew"):
        info("Homebrew not found — skipping.")
        return
    for pkg in packages:
        result = subprocess.run(
            ["brew", "list", pkg], capture_output=True, text=True
        )
        if result.returncode != 0:
            info(f"brew: {pkg} not installed.")
            continue
        if not confirm(f"Uninstall '{pkg}' via Homebrew?", auto_yes):
            info(f"Skipping {pkg}.")
            continue
        if dry_run:
            info(f"[DRY-RUN] Would run: brew uninstall {pkg}")
        else:
            subprocess.run(["brew", "uninstall", pkg], check=False)
            success(f"Uninstalled {pkg} via Homebrew.")


def _uninstall_linux_packages(dry_run, auto_yes):
    pkg_managers = {
        "apt": {
            "check": ["dpkg", "-s"],
            "remove": ["sudo", "apt", "remove", "-y"],
            "packages": ["glpk-utils", "coinor-cbc"],
        },
        "dnf": {
            "check": ["rpm", "-q"],
            "remove": ["sudo", "dnf", "remove", "-y"],
            "packages": ["glpk-utils", "coin-or-Cbc"],
        },
        "pacman": {
            "check": ["pacman", "-Q"],
            "remove": ["sudo", "pacman", "-Rns", "--noconfirm"],
            "packages": ["glpk", "coin-or-cbc"],
        },
    }

    for mgr_name, mgr in pkg_managers.items():
        if not shutil.which(mgr_name):
            continue
        info(f"Detected package manager: {mgr_name}")
        for pkg in mgr["packages"]:
            result = subprocess.run(
                mgr["check"] + [pkg], capture_output=True, text=True
            )
            if result.returncode != 0:
                info(f"{mgr_name}: {pkg} not installed.")
                continue
            if not confirm(f"Uninstall '{pkg}' via {mgr_name}?", auto_yes):
                info(f"Skipping {pkg}.")
                continue
            if dry_run:
                info(f"[DRY-RUN] Would run: {' '.join(mgr['remove'] + [pkg])}")
            else:
                subprocess.run(mgr["remove"] + [pkg], check=False)
                success(f"Uninstalled {pkg} via {mgr_name}.")
        break  # Use only the first detected package manager


def _uninstall_choco_packages(packages, dry_run, auto_yes):
    if not shutil.which("choco"):
        info("Chocolatey not found — skipping.")
        return
    for pkg in packages:
        result = subprocess.run(
            ["choco", "list", "--local-only", pkg],
            capture_output=True, text=True,
        )
        if pkg.lower() not in result.stdout.lower():
            info(f"choco: {pkg} not installed.")
            continue
        if not confirm(f"Uninstall '{pkg}' via Chocolatey?", auto_yes):
            info(f"Skipping {pkg}.")
            continue
        if dry_run:
            info(f"[DRY-RUN] Would run: choco uninstall {pkg} -y")
        else:
            subprocess.run(["choco", "uninstall", pkg, "-y"], check=False)
            success(f"Uninstalled {pkg} via Chocolatey.")


# ---------------------------------------------------------------------------
# Summary & Entrypoint
# ---------------------------------------------------------------------------
def print_summary():
    """Print what will be checked/removed before starting."""
    venv_dir = get_venv_dir()
    print(f"\n{Style.BOLD}{'='*60}{Style.RESET}")
    print(f"{Style.BOLD}  MUIOGO Uninstaller — Summary of Actions{Style.RESET}")
    print(f"{Style.BOLD}{'='*60}{Style.RESET}")
    print(f"""
The following setup-created state will be removed:

  1. Virtual environment   : {venv_dir}
  2. Repo .env entries     : {ENV_FILE}
  3. Demo data + marker    : {DEMO_DATA_DIR}
  4. Win solver dirs       : {', '.join(str(d) for d in WINDOWS_SOLVER_DIRS) or 'N/A'}
  5. Win env vars / PATH   : GLPK_PATH, CBC_PATH, PATH entries
  6. Pkg manager solvers   : opt-in only (--remove-solvers)
""")


def main():
    parser = argparse.ArgumentParser(
        description="Uninstall MUIOGO setup-created local state."
    )
    parser.add_argument(
        "--remove-solvers",
        action="store_true",
        help="Also attempt to remove solver packages installed via package managers.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually deleting anything.",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts (auto-yes).",
    )
    args = parser.parse_args()

    print_summary()

    if args.dry_run:
        print(f"{Style.YELLOW}  *** DRY-RUN MODE — nothing will be deleted ***{Style.RESET}\n")

    if not args.yes:
        if not confirm("Proceed with uninstall?"):
            print("Aborted.")
            sys.exit(0)

    # Default removals (always)
    remove_venv(args.dry_run)
    remove_env_file(args.dry_run)
    remove_demo_data(args.dry_run)
    remove_windows_solver_dirs(args.dry_run)
    remove_windows_env_vars(args.dry_run)

    # Opt-in solver package removal
    if args.remove_solvers:
        remove_package_manager_solvers(args.dry_run, args.yes)
    else:
        print(f"\n{Style.BOLD}6. Package Manager Solvers{Style.RESET}")
        info("Skipped. Use --remove-solvers to include.")

    print(f"\n{Style.BOLD}{'='*60}{Style.RESET}")
    if args.dry_run:
        print(f"{Style.YELLOW}  Dry run complete. No changes were made.{Style.RESET}")
    else:
        print(f"{Style.GREEN}  Uninstall complete!{Style.RESET}")
        print(f"  Run setup again for a fresh install.")
    print(f"{Style.BOLD}{'='*60}{Style.RESET}\n")


if __name__ == "__main__":
    sys.exit(main())