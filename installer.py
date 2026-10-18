"""Windows setup and local-launch helpers for Content Guard."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
VENV_PYTHONW = VENV_DIR / "Scripts" / "pythonw.exe"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"
EXTENSION_DIR = PROJECT_DIR / "extension"
INSTANCE_DIR = PROJECT_DIR / "instance"
LOG_PATH = INSTANCE_DIR / "content_guard.log"
PID_PATH = INSTANCE_DIR / "content_guard.pid"


def run_step(label, command):
    print(f"\n[+] {label}", flush=True)
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


def setup():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required.")
    if not REQUIREMENTS.is_file():
        raise FileNotFoundError(f"Requirements file not found: {REQUIREMENTS}")

    if not VENV_PYTHON.is_file():
        run_step(
            "Creating the project virtual environment",
            [sys.executable, "-m", "venv", str(VENV_DIR)],
        )
    else:
        print("[+] Reusing the existing .venv virtual environment.")

    run_step(
        "Installing application requirements",
        [str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
    )
    run_step(
        "Initializing the SQLite database",
        [str(VENV_PYTHON), "-m", "flask", "--app", "app", "init-db"],
    )
    print("\nSetup complete. Start Content Guard with start_content_guard.bat.")
    print("Open http://127.0.0.1:5000 in your browser.")


def find_browser(browser):
    if os.name != "nt":
        return None

    import winreg

    app_name = "chrome.exe" if browser == "chrome" else "msedge.exe"
    registry_paths = (
        (winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{app_name}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{app_name}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\{app_name}"),
    )
    for hive, key_path in registry_paths:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                executable = winreg.QueryValue(key, None)
            if executable and Path(executable).is_file():
                return executable
        except (FileNotFoundError, OSError):
            continue

    candidates = (
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ) if browser == "chrome" else (
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    )
    return next((str(path) for path in candidates if path.is_file()), None)


def configure_extension(browser):
    if not EXTENSION_DIR.is_dir() or not (EXTENSION_DIR / "manifest.json").is_file():
        raise FileNotFoundError(f"Browser extension not found: {EXTENSION_DIR}")
    if os.name != "nt":
        raise OSError("The browser setup helper is intended to run on Windows.")

    browsers = ("chrome", "edge") if browser == "both" else (browser,)
    opened = []
    for name in browsers:
        executable = find_browser(name)
        if not executable:
            print(f"[-] {name.title()} was not found; skipping it.")
            continue
        page = "chrome://extensions" if name == "chrome" else "edge://extensions"
        subprocess.Popen(
            [executable, page],
            cwd=PROJECT_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        opened.append(name.title())
        print(f"[+] Opened {name.title()} extension management.")

    if not opened:
        raise RuntimeError("Neither requested browser was found.")

    subprocess.Popen(["explorer.exe", str(EXTENSION_DIR)], cwd=PROJECT_DIR)
    print(f"\nExtension folder: {EXTENSION_DIR}")
    print("In the browser page, enable Developer mode, choose Load unpacked,")
    print("and select the opened extension folder.")
    print("Unpacked extensions are registered through the browser UI; this helper")
    print("does not write unsupported or machine-wide browser registry policies.")


def is_service_responding(host, port):
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen

    try:
        with urlopen(f"http://{host}:{port}/", timeout=1):
            return True
    except HTTPError:
        return True
    except URLError:
        return False
    except OSError:
        return False


def start_desktop():
    if not VENV_PYTHONW.is_file():
        raise FileNotFoundError(
            "The virtual environment is missing. Run setup.bat before starting Content Guard."
        )

    host = os.environ.get("CONTENT_GUARD_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTENT_GUARD_PORT", "5000"))
    window_only = is_service_responding(host, port)

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_PATH.open("a", encoding="utf-8")
    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        process = subprocess.Popen(
            [
                str(VENV_PYTHONW),
                str(PROJECT_DIR / "app.py"),
                *(["--window-only"] if window_only else []),
            ],
            cwd=PROJECT_DIR,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
            start_new_session=os.name != "nt",
        )
    finally:
        log_file.close()

    PID_PATH.write_text(str(process.pid), encoding="ascii")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            try:
                detail = LOG_PATH.read_text(encoding="utf-8", errors="replace")[-2000:]
            except OSError:
                detail = "No application log was available."
            raise RuntimeError(f"Content Guard failed to start. Recent log output:\n{detail}")
        if is_service_responding(host, port):
            print("Content Guard desktop window started.")
            print(f"Local service: http://{host}:{port}/")
            print(f"Application log: {LOG_PATH}")
            return
        time.sleep(0.25)

    raise RuntimeError(
        f"Content Guard is still starting but did not respond within 10 seconds. "
        f"Check {LOG_PATH}"
    )


def main():
    parser = argparse.ArgumentParser(description="Content Guard Windows setup helper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("setup", help="create the virtual environment and initialize the app")
    subparsers.add_parser("start", help="open the Content Guard desktop window")
    extension_parser = subparsers.add_parser(
        "extension", help="open the browser page and folder to load the local extension"
    )
    extension_parser.add_argument(
        "--browser", choices=("chrome", "edge", "both"), default="both"
    )
    args = parser.parse_args()

    try:
        if args.command == "setup":
            setup()
        elif args.command == "start":
            start_desktop()
        else:
            configure_extension(args.browser)
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        print(f"\nSetup error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
