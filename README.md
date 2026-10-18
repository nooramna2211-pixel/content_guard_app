# Content Guard

A Flask web application starter for managing family-friendly browsing settings.
It provides a dashboard, saved safe-search preferences, a manually managed
domain blocklist, and a custom keyword dictionary for English, Roman Urdu, and
Urdu script.

The responsive product landing page is [index.html](./index.html). It includes
clearly marked screenshot placeholders and a direct link to
`dist/ContentGuard-Windows.zip`; `build_windows.bat` creates or refreshes this
archive from the packaged executable folder. The Android download remains
unavailable until an APK is built. To build one for free with Google Colab,
run `prepare_android_source.bat`, upload the resulting
`dist/ContentGuard-Android-Source.zip` in
[colab_build_android.ipynb](./colab_build_android.ipynb), and follow the steps
in [README_ANDROID.md](./README_ANDROID.md).

## Windows setup and launch

```powershell
.\setup.bat
.\start_content_guard.bat
```

`setup.bat` creates `.venv`, installs `requirements.txt`, and initializes the
SQLite database. `start_content_guard.bat` starts Content Guard in a native
desktop window using pywebview; the Flask service listens locally at
`http://127.0.0.1:5000`. Logs are written to `instance/content_guard.log`.
Closing the desktop window stops the local service it started.

To open Chrome or Edge's extension manager and the local extension folder, run
`.\.venv\Scripts\python.exe installer.py extension --browser both` (or select
`chrome` or `edge`). Enable Developer mode and choose **Load unpacked** in the
browser, then select the opened `extension` folder. Chromium does not support
registering an unpacked development extension through a normal registry entry;
the helper uses the supported browser UI rather than modifying browser policy.

For desktop development, activate `.venv` and run `python app.py`. To run only
the local Flask service for browser or extension testing, use
`python -m flask --app app run`. The SQLite database is created at
`instance/content_guard.sqlite3`; set
`CONTENT_GUARD_DATABASE` to change its location. `CONTENT_GUARD_HOST`,
`CONTENT_GUARD_PORT`, and `CONTENT_GUARD_DEBUG=1` can configure local
development. The native window uses the Windows WebView2 runtime when
available, with pywebview's compatibility renderer as fallback. For a modern
rendering engine, install the Microsoft Edge WebView2 Evergreen Runtime.
`CONTENT_GUARD_MONITOR_INTERVAL` sets the network scan period in seconds
(minimum 10; default 30). Do not enable Flask debug mode or use the development
server for a public deployment.

## Build a Windows installer

Install Python 3.10 or newer and Inno Setup 6, then add Inno Setup's `ISCC.exe`
to `PATH` and run `build_windows.bat`. The script installs the build
requirements, packages the Flask app and templates with PyInstaller, and
creates `dist/installer/ContentGuard-Setup-1.0.0.exe`. Without Inno Setup, it
still produces the packaged app folder at `dist/ContentGuard`.

The installer is per-user, creates Start Menu shortcuts, and offers an
unchecked, optional start-at-sign-in shortcut. Its normal Windows uninstaller
remains available, and user data is preserved on uninstall. Packaged database
files are stored under `%LOCALAPPDATA%\Content Guard`, outside the application
install folder. Templates, static files, and the extension are included in the
installed app.
The generated installer is unsigned; sign it with your organization's
Authenticode certificate before distributing it broadly.

The extension is not silently force-installed or managed by browser policy.
To use it, explicitly load the installed `extension` directory through
`chrome://extensions` or `edge://extensions` with Developer mode enabled.
The installer does not lock or password-protect Windows uninstall, install a
hidden service, or resist removal by the device owner; use documented Windows
enterprise deployment and device-management controls when administrator-owned
enforcement is required.

## Routes

- `/` — protection status and list summaries
- `/safe-search` — Google, Bing, Yahoo, DuckDuckGo, and YouTube preferences
- `/blocklist` — add and remove domain names
- `/keywords` — manage language-tagged custom keywords
- `/simulator` — test a phrase against custom keywords and blocked domains
- `/api/check` — read-only JSON decision for an extension URL or query
- `/api/check-keywords` — keyword-only JSON decision for Google/YouTube searches
- `/api/rules` — read-only JSON blocklist feed used by the browser extension
- `/settings` — verify the current master password and update it
- `/pin` — create the initial password or unlock protected controls

On first run, `/pin` asks you to create a master password with at least 12
characters, including a letter, a number, and a special character. To provision
it before startup, set `CONTENT_GUARD_INITIAL_PASSWORD` to a password meeting
the same requirements. Safe-search preferences, protection toggling, blocklist
management, and keyword management require the password to be verified.
Passwords are stored as Werkzeug password hashes; plaintext credentials are
not saved in the database or session. Use **Lock settings** in the navbar to
end the current browser session's unlocked state.

Three consecutive incorrect password attempts from the same client address
trigger a persisted five-minute lockout. The unlock and password settings pages
show the remaining lockout duration. For deployments behind a proxy, configure
the proxy and network boundary carefully; the app keys lockouts using the
direct peer address and does not trust forwarded IP headers.

Existing databases with the previous PIN format remain usable for migration:
enter the old PIN once at `/pin`, then set a new master password in Password
Settings. The legacy PIN hash is removed when the new password is saved.

## Anti-VPN and proxy enforcement

Enable **Anti-VPN enforcement** from Password Settings and confirm the master
password. The monitor starts on the first request in a non-testing Flask worker
and scans every 30 seconds. On Windows it inspects active network adapters and
connected Windows VPN profiles, reads the current user's Internet Settings
proxy/PAC/WPAD values, and checks the WinHTTP proxy configuration. On Linux and
macOS, it checks active interfaces for VPN-like adapter names and the Flask
process's proxy environment variables.

Any active VPN-like adapter or connection is considered unauthorized. Proxies
are unauthorized unless their hostname/IP is listed in **Authorized proxy
hosts**. Detection creates persistent security alerts and enables fail-closed
lock mode: the extension check API returns a blocked decision and protected
filter administration is suspended until the issue clears or an administrator
confirms the password and disables enforcement. Monitoring errors also fail
closed while enforcement is enabled. Known virtual adapters and proxy settings
can produce false positives; review alerts and allowlist only proxies you
control. Disabling enforcement clears the active lock but keeps alert history.
The app only changes its own filtering/API behavior; it does not alter Windows
adapter, VPN, or proxy configuration.

The Search Simulator applies case-insensitive Unicode substring matching: a
query is blocked whenever it contains any saved keyword or phrase anywhere in
the submitted text. It also searches for exact blocked domains or their
subdomains. A match reports the keyword language or blocklist entry.

Forms use CSRF protection. The starter keyword dictionary is pre-loaded with
common adult/explicit search terms, spelling variants, and phrases in English,
Roman Urdu, and Urdu script. New defaults are seeded once when the app upgrades
an existing database, without re-adding the original starter terms removed by
an administrator. Manage or remove entries in the Keyword Filter page.

## Browser extension

The Chromium Manifest V3 extension is in [`extension/`](./extension/). Load it
unpacked from `chrome://extensions` or `edge://extensions` while the Flask app
is running at `http://127.0.0.1:5000`. It checks Google and YouTube search
queries against `/api/check-keywords`, enforces Google SafeSearch on Google
searches, and leaves regular Google, YouTube, and Gemini pages accessible.
Custom domain rules continue to apply to other domains. See
[`extension/README.md`](./extension/README.md) for installation and supported
sites.

## Important limitation

This is a configuration dashboard, not a network filter. Its protection toggle
only saves a status setting; the safe-search options are preferences; the
blocklist and keyword dictionary are enforced only by the optional browser
extension, within its supported browser/sites, while the local Flask API is
available. Anti-VPN lock mode similarly blocks the extension API and protected
app controls; it does not disable adapters, terminate VPN connections, or
filter native apps or all device traffic. Deploy the web app behind a production
WSGI server with HTTPS, a stable secret key, and appropriate authentication
before exposing it to users.
