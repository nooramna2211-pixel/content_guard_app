"""Create a source-only archive for the Content Guard Colab Android build."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dist" / "ContentGuard-Android-Source.zip"
INCLUDED_PATHS = (
    Path("app.py"),
    Path("main.py"),
    Path("buildozer.spec"),
    Path("README_ANDROID.md"),
    Path("android") / "extra_manifest_application_arguments.xml",
    Path("templates"),
    Path("static"),
)


def main():
    files = []
    for item in INCLUDED_PATHS:
        source = ROOT / item
        if not source.exists():
            raise FileNotFoundError(f"Android build source is missing: {source}")
        if source.is_file():
            files.append(source)
        else:
            files.extend(path for path in source.rglob("*") if path.is_file())

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for source in sorted(files):
            archive.write(source, source.relative_to(ROOT))

    print(f"Android source archive created: {OUTPUT}")
    print(f"Included {len(files)} files ({OUTPUT.stat().st_size:,} bytes).")
    print("Upload this ZIP to the Colab notebook; it contains no desktop build output.")


if __name__ == "__main__":
    main()
