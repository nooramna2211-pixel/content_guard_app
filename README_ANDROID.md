# Android APK development build

This is a developer packaging recipe, not a signed or production-ready Android
release. It embeds the Flask app in the APK, runs the Flask development server
on the Android device's loopback interface, and displays the dashboard in the
Android System WebView through a small Kivy/PyJNIus host.

## Project layout

```text
content_guard_app/
|-- app.py                 # Existing Flask application
|-- main.py                # Android/Kivy entry point and local WebView host
|-- buildozer.spec         # Buildozer APK configuration
|-- android/
|   `-- extra_manifest_application_arguments.xml
|-- templates/             # Flask UI templates
|-- static/                # Flask CSS and static assets
|-- index.html             # Product landing page (not the in-app dashboard)
|-- requirements.txt       # Desktop dependencies; Android uses buildozer.spec
`-- README_ANDROID.md
```

The Android wrapper keeps its SQLite database and Flask session secret in the
app's private data directory. It only binds the backend to `127.0.0.1`; it does
not expose Flask to the Wi-Fi network. The manifest allows cleartext traffic
because the local WebView talks to the loopback Flask server over HTTP. Do not
change the server bind address to `0.0.0.0`.

## Build on Linux

Buildozer and python-for-android are supported on Linux. Use a clean Linux
machine or a Linux VM/WSL2 environment with Java 17, Android SDK/NDK build
dependencies, and enough disk space for the first toolchain download. Windows
PowerShell is not a supported Buildozer build host.

### Build automatically with GitHub Actions

The workflow at `.github/workflows/build.yml` builds a debug APK on every
branch push and pull request, and can also be started manually from the
repository's **Actions** tab. After a successful run, download the
`content-guard-android-apk` artifact from that workflow run. The artifact is
retained for 14 days. The first build may take longer while Android SDK/NDK
components are downloaded; subsequent runs reuse the Buildozer cache.

### Build for free with Google Colab

The ready-to-run notebook is [`colab_build_android.ipynb`](./colab_build_android.ipynb).
It installs the Linux build dependencies, uploads the project sources, builds a
debug APK, and downloads the APK to your computer.

1. Run `prepare_android_source.bat` from the Windows project folder. It creates
   `dist/ContentGuard-Android-Source.zip` containing the Flask app, wrapper,
   templates, static files, and Buildozer settings, but not Windows binaries or
   virtual environments.
2. Open `colab_build_android.ipynb` in Google Colab. Choose the free CPU
   runtime; a GPU is not needed.
3. Run its cells in order and upload `dist/ContentGuard-Android-Source.zip`
   when prompted.
4. Wait for the Android SDK/NDK downloads and APK build. Use the final notebook
   cell to download `ContentGuard-Android-1.0.0-debug.apk`.

Colab provides temporary compute for free subject to Google's quotas,
availability, runtime limits, and disconnects. The first build can take a long
time and use several GB. If a session disconnects, reconnect and rerun the
cells, uploading the source ZIP again. Never put signing keys or secrets in a
notebook or uploaded source archive.

1. Install the system prerequisites documented by the
   [Buildozer installation guide](https://buildozer.readthedocs.io/en/latest/installation/).
   Use a Python version supported by the Buildozer release you install.
2. From the project root, create and activate a build virtual environment, then
   install Buildozer:

   ```bash
   python3 -m venv .buildozer-venv
   source .buildozer-venv/bin/activate
   python -m pip install --upgrade pip setuptools wheel buildozer
   ```

3. Build and optionally deploy to a connected Android device:

   ```bash
   buildozer android debug
   buildozer android debug deploy run
   ```

4. Find the generated debug APK in `bin/`. To publish the landing-page Android
   button, copy the tested APK to
   `bin/ContentGuard-Android-1.0.0.apk` or update that button to the final
   release filename.

Buildozer may require dependency pins or recipe changes as Android SDK,
python-for-android, Flask, Kivy, and PyJNIus versions evolve. The checked-in
spec is a starting point; verify each build on a device and confirm that the
device's Android System WebView is installed and enabled.

## Limitations and release checklist

- This embeds a Flask development server in one mobile process. It is intended
  for a local single-user dashboard, not a public or multi-user service.
- The existing desktop anti-VPN/platform inspection behavior is not a native
  Android network enforcement feature. This wrapper does not create a VPN,
  filter device-wide traffic, or replace an Android `VpnService`.
- The browser extension is not part of the APK.
- Debug APKs are not suitable for public distribution. Create a release build,
  protect and use your own Android signing key, test upgrades and data
  migration, review cleartext/network policy, and distribute only through a
  channel appropriate to your users.

See `index.html` for the responsive product landing page. Its download buttons
report when their corresponding release artifact has not yet been built.
