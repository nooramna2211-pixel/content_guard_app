import ipaddress
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import sqlite3
import subprocess
import sys
import time
import threading
import unicodedata
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_KEYWORDS = {
    "English": (
        "adult",
        "adult content",
        "adult videos",
        "adult website",
        "adult movies",
        "explicit",
        "explicit content",
        "explicit videos",
        "nsfw",
        "not safe for work",
        "porn",
        "porno",
        "pornography",
        "pornographic",
        "porn video",
        "porn videos",
        "xxx",
        "x-rated",
        "sex",
        "sexual",
        "sexual content",
        "sex video",
        "sex videos",
        "erotic",
        "erotica",
        "nude",
        "nudes",
        "naked",
        "nudity",
        "sexy",
        "hot girls",
        "hot women",
        "adult chat",
        "sex chat",
        "cam girl",
        "webcam sex",
        "live cam",
        "escort",
        "escorts",
        "hookup",
        "fetish",
        "bdsm",
        "hentai",
        "onlyfans",
        "deepfake porn",
        "leaked nudes",
        "uncensored",
        "hardcore",
        "softcore",
        "milf",
        "threesome",
        "orgasm",
        "masturbation",
        "sexual pictures",
        "adult images",
        "xxx videos",
        "free porn",
        "free sex videos",
        "porn site",
        "adult site",
        "erotic stories",
        "sexual stories",
        "adult manga",
    ),
    "Roman Urdu": (
        "fahash",
        "fahashi",
        "fuhash",
        "fuhashi",
        "behaya",
        "be haya",
        "gandi",
        "ganda",
        "gandagi",
        "gandi video",
        "gandi videos",
        "gandi film",
        "gandi tasveer",
        "gandi tasveeren",
        "gandi kahani",
        "gandi baatein",
        "gandi website",
        "gandi site",
        "nangi",
        "nanga",
        "nangay",
        "nangi tasveer",
        "nangi tasveeren",
        "nangi larki",
        "nangi larkiyan",
        "nangi aurat",
        "nangi auratein",
        "adult video",
        "adult videos",
        "adult film",
        "adult website",
        "adult site",
        "porn video",
        "porn videos",
        "porn film",
        "porn site",
        "xxx video",
        "xxx videos",
        "sex video",
        "sex videos",
        "sex film",
        "sex chat",
        "hot larki",
        "hot larkiyan",
        "hot aurat",
        "sexy larki",
        "sexy aurat",
        "fahash video",
        "fahash videos",
        "fahash film",
        "fahash tasveer",
        "fahash kahani",
        "sharmnak video",
        "sharmnaak video",
        "behuda video",
        "behuda tasveer",
        "jinsi video",
        "jinsi tasveer",
        "jinsi kahani",
        "jinsi maloomat",
        "raazdaar sex",
        "free porn",
        "free adult videos",
    ),
    "Urdu": (
        "گندی",
        "گندا",
        "گندے",
        "گندی ویڈیو",
        "گندی ویڈیوز",
        "گندی تصاویر",
        "گندا مواد",
        "فحش",
        "فحاش",
        "فحاشی",
        "فحشی",
        "عریاں",
        "برہنہ",
        "ننگا",
        "ننگی",
        "ننگے",
        "بالغ",
        "بالغ مواد",
        "بالغوں کا مواد",
        "غیر اخلاقی",
        "غیر اخلاقی مواد",
        "جنسی",
        "جنسی مواد",
        "جنسی ویڈیو",
        "جنسی ویڈیوز",
        "جنسی تصاویر",
        "جنسی کہانیاں",
        "جنسی فلم",
        "جنسی فلمیں",
        "فحش ویڈیو",
        "فحش ویڈیوز",
        "فحش فلم",
        "فحش فلمیں",
        "فحش تصاویر",
        "فحش تصویر",
        "فحش کہانی",
        "فحش کہانیاں",
        "فحش ویب سائٹ",
        "فحش سائٹ",
        "عریاں ویڈیو",
        "عریاں تصاویر",
        "عریاں عورت",
        "ننگی عورت",
        "ننگی لڑکی",
        "ننگی لڑکیاں",
        "بالغ ویڈیو",
        "بالغ ویڈیوز",
        "بالغ فلم",
        "بالغ ویب سائٹ",
        "جنسی چیٹ",
        "سیکس",
        "سیکسی",
        "سیکس ویڈیو",
        "سیکس ویڈیوز",
        "سیکس فلم",
        "سیکس چیٹ",
        "ایکس ریٹیڈ",
        "پورن",
        "پورنوگرافی",
        "ایکس ایکس ایکس",
        "فحش مواد",
        "غیر مناسب جنسی مواد",
        "شرمناک ویڈیو",
        "بیہودہ ویڈیو",
        "بیہودہ مواد",
    ),
}
LEGACY_DEFAULT_KEYWORDS = {
    "English": {"adult", "explicit", "porn", "xxx"},
    "Roman Urdu": {"fahash", "gandi"},
    "Urdu": {"فحاش", "فحشی", "فحش"},
}
DEFAULT_KEYWORDS_VERSION = "2"
DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
LANGUAGES = ("English", "Roman Urdu", "Urdu")
SEARCH_PROVIDERS = ("Google", "Bing", "Yahoo", "DuckDuckGo")
MAX_QUERY_LENGTH = 500
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 256
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_SECONDS = 300
LEGACY_PIN_ITERATIONS = 310_000
DEFAULT_MONITOR_INTERVAL = 30
MAX_ALERTS_TO_DISPLAY = 25
VPN_ADAPTER_PATTERN = re.compile(
    r"\b(vpn|wireguard|wintun|openvpn|protonvpn|nordvpn|proton|nord|warp|cloudflare|"
    r"tap(?:[-\s]|$)|tun(?:[-\s]|$)|tailscale|zerotier|anyconnect|"
    r"globalprotect|forti(?:client|net)?|pulse secure|mullvad|expressvpn|"
    r"surfshark|private internet access|pia)\b",
    re.IGNORECASE,
)


def create_app(test_config=None):
    application = Flask(__name__, instance_relative_config=True)
    default_database = Path(application.instance_path) / "content_guard.sqlite3"
    if getattr(sys, "frozen", False) and os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            default_database = (
                Path(local_app_data)
                / "Content Guard"
                / "content_guard.sqlite3"
            )
    application.config.from_mapping(
        SECRET_KEY=os.environ.get("CONTENT_GUARD_SECRET") or os.urandom(32),
        INITIAL_MASTER_PASSWORD=os.environ.get("CONTENT_GUARD_INITIAL_PASSWORD"),
        DATABASE=os.environ.get(
            "CONTENT_GUARD_DATABASE",
            str(default_database),
        ),
        NETWORK_MONITOR_INTERVAL=int(
            os.environ.get("CONTENT_GUARD_MONITOR_INTERVAL", DEFAULT_MONITOR_INTERVAL)
        ),
    )
    if test_config:
        application.config.update(test_config)
    configured_password = application.config.pop("INITIAL_MASTER_PASSWORD")
    if configured_password and password_policy_error(configured_password):
        raise ValueError(
            "CONTENT_GUARD_INITIAL_PASSWORD must be at least 12 characters "
            "and include a letter, a number, and a special character."
        )
    application.config["INITIAL_MASTER_PASSWORD_HASH"] = (
        password_hash(configured_password) if configured_password else None
    )

    csrf = CSRFProtect(application)
    Path(application.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def get_db():
        if "db" not in g:
            database_path = Path(application.config["DATABASE"])
            database_path.parent.mkdir(parents=True, exist_ok=True)
            g.db = sqlite3.connect(database_path, timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @application.teardown_appcontext
    def close_db(_error=None):
        database = g.pop("db", None)
        if database is not None:
            database.close()

    def initialize_database():
        database = get_db()
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                normalized TEXT NOT NULL,
                language TEXT NOT NULL CHECK(language IN ('English', 'Roman Urdu', 'Urdu')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(normalized, language)
            );
            CREATE TABLE IF NOT EXISTS auth_lockouts (
                identity TEXT PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS security_alerts_active_unique
            ON security_alerts(category, detail)
            WHERE resolved_at IS NULL;
            """
        )
        database.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            [
                ("protection_enabled", "0"),
                ("safe_search_google", "1"),
                ("safe_search_bing", "1"),
                ("safe_search_yahoo", "1"),
                ("safe_search_duckduckgo", "1"),
                ("youtube_restricted", "1"),
                ("anti_vpn_enabled", "0"),
                ("anti_vpn_lock_active", "0"),
                ("anti_vpn_lock_reason", ""),
                ("authorized_proxy_hosts", ""),
                ("anti_vpn_last_scan", ""),
                ("anti_vpn_last_status", "Disabled"),
            ],
        )
        if (
            application.config["INITIAL_MASTER_PASSWORD_HASH"]
            and database.execute(
                "SELECT 1 FROM settings WHERE key = 'master_password_hash'"
            ).fetchone()
            is None
            and database.execute(
                "SELECT 1 FROM settings WHERE key = 'pin_hash'"
            ).fetchone()
            is None
        ):
            database.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (
                    "master_password_hash",
                    application.config["INITIAL_MASTER_PASSWORD_HASH"],
                ),
            )
        seeded = database.execute(
            "SELECT value FROM settings WHERE key = 'default_keywords_seeded'"
        ).fetchone()
        if seeded is None:
            default_words = DEFAULT_KEYWORDS
        elif seeded["value"] != DEFAULT_KEYWORDS_VERSION:
            default_words = {
                language: tuple(
                    word
                    for word in words
                    if normalize_keyword(word).casefold()
                    not in {
                        normalize_keyword(old_word).casefold()
                        for old_word in LEGACY_DEFAULT_KEYWORDS.get(language, set())
                    }
                )
                for language, words in DEFAULT_KEYWORDS.items()
            }
        else:
            default_words = {}
        for language, words in default_words.items():
            database.executemany(
                "INSERT OR IGNORE INTO keywords (keyword, normalized, language) "
                "VALUES (?, ?, ?)",
                [
                    (word, normalize_keyword(word), language)
                    for word in words
                ],
            )
        database.execute(
            "INSERT INTO settings (key, value) VALUES ('default_keywords_seeded', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (DEFAULT_KEYWORDS_VERSION,),
        )
        database.commit()

    @application.cli.command("init-db")
    def initialize_database_command():
        with application.app_context():
            initialize_database()
        print(f"Content Guard database is ready: {application.config['DATABASE']}")

    monitor_start_lock = threading.Lock()
    network_monitor_lock = threading.RLock()
    monitor_started = False

    def run_monitor_iteration():
        with application.app_context():
            if setting("anti_vpn_enabled") != "1":
                save_setting("anti_vpn_last_status", "Disabled")
                return
            try:
                observations = inspect_network_security()
                authorized_hosts = parse_authorized_proxy_hosts(
                    setting("authorized_proxy_hosts") or ""
                )
                threats = []
                for observation in observations:
                    if observation["category"] in {"vpn_adapter", "vpn_connection"}:
                        threats.append(observation)
                    elif observation["category"] == "proxy":
                        host = observation.get("host")
                        if not host or not is_host_authorized(host, authorized_hosts):
                            threats.append(observation)
                threats = list(
                    {
                        (item["category"], item["detail"]): item
                        for item in threats
                    }.values()
                )

                save_setting(
                    "anti_vpn_last_scan",
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                )
                if threats:
                    reason = "; ".join(
                        f"{item['category']}: {item['detail']}" for item in threats
                    )
                    for threat in threats:
                        record_security_alert(
                            threat["category"], threat["detail"]
                        )
                    save_setting("anti_vpn_lock_active", "1")
                    save_setting("anti_vpn_lock_reason", reason[:1000])
                    save_setting(
                        "anti_vpn_last_status",
                        f"Locked: {len(threats)} unauthorized network setting(s) detected",
                    )
                else:
                    resolve_active_security_alerts()
                    save_setting("anti_vpn_lock_active", "0")
                    save_setting("anti_vpn_lock_reason", "")
                    save_setting("anti_vpn_last_status", "No VPN or unauthorized proxy detected")
            except Exception as error:
                application.logger.exception("Network security inspection failed.")
                detail = f"Inspection failed: {type(error).__name__}: {error}"[:1000]
                record_security_alert("monitor_error", detail)
                save_setting("anti_vpn_lock_active", "1")
                save_setting(
                    "anti_vpn_last_scan",
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                )
                save_setting(
                    "anti_vpn_lock_reason",
                    "Network inspection failed; enforcement is fail-closed.",
                )
                save_setting("anti_vpn_last_status", "Locked: network inspection failed")

    def monitor_iteration():
        with network_monitor_lock:
            run_monitor_iteration()

    def monitor_loop():
        interval = max(
            10,
            int(application.config.get("NETWORK_MONITOR_INTERVAL", DEFAULT_MONITOR_INTERVAL)),
        )
        while True:
            try:
                monitor_iteration()
            except Exception:
                application.logger.exception("Network monitor iteration failed.")
            time.sleep(interval)

    def start_monitor_if_needed():
        nonlocal monitor_started
        if application.testing or not application.config.get("START_NETWORK_MONITOR", True):
            return
        with monitor_start_lock:
            if monitor_started:
                return
            monitor_started = True
            threading.Thread(
                target=monitor_loop,
                name="content-guard-network-monitor",
                daemon=True,
            ).start()

    @application.before_request
    def ensure_database():
        initialize_database()
        start_monitor_if_needed()

    def add_extension_cors(response):
        response.headers["Cache-Control"] = "no-store"
        origin = request.headers.get("Origin", "")
        try:
            origin_scheme = urlsplit(origin).scheme
        except ValueError:
            origin_scheme = ""
        if origin and origin_scheme in {
            "chrome-extension",
            "moz-extension",
            "edge-extension",
        }:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            if request.headers.get("Access-Control-Request-Private-Network") == "true":
                response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    @application.route("/api/check", methods=["GET", "POST", "OPTIONS"])
    @csrf.exempt
    def check_extension_request():
        if request.method == "OPTIONS":
            return add_extension_cors(application.response_class(status=204))
        if setting("anti_vpn_lock_active") == "1":
            return add_extension_cors(
                jsonify(
                    {
                        "blocked": True,
                        "reason": setting("anti_vpn_lock_reason")
                        or "Content Guard is in fail-closed network security lock mode.",
                    }
                )
            )
        if request.method == "POST":
            payload = request.get_json(silent=True)
            value = (
                payload.get("url") or payload.get("query")
                if isinstance(payload, dict)
                else None
            )
        else:
            value = request.args.get("url") or request.args.get("query")
        if not isinstance(value, str) or not value:
            response = jsonify(
                {"blocked": False, "reason": "Provide a url or query parameter."}
            )
            response.status_code = 400
            return add_extension_cors(response)
        if len(value) > 8192:
            response = jsonify(
                {"blocked": False, "reason": "Input exceeds the 8192 character limit."}
            )
            response.status_code = 413
            return add_extension_cors(response)
        blocked, reason = inspect_filter_input(get_db(), value)
        return add_extension_cors(jsonify({"blocked": blocked, "reason": reason or ""}))

    @application.route(
        "/api/check-keywords", methods=["GET", "POST", "OPTIONS"]
    )
    @csrf.exempt
    def check_extension_keywords():
        if request.method == "OPTIONS":
            return add_extension_cors(application.response_class(status=204))
        if request.method == "POST":
            payload = request.get_json(silent=True)
            value = (
                payload.get("query")
                if isinstance(payload, dict)
                else None
            )
        else:
            value = request.args.get("query")
        if not isinstance(value, str) or not value:
            response = jsonify(
                {"blocked": False, "reason": "Provide a query parameter."}
            )
            response.status_code = 400
            return add_extension_cors(response)
        if len(value) > 8192:
            response = jsonify(
                {"blocked": False, "reason": "Query exceeds the 8192 character limit."}
            )
            response.status_code = 413
            return add_extension_cors(response)
        matches = find_keyword_matches(get_db(), value)
        first_match = matches[0] if matches else None
        reason = (
            f"Matched {first_match['detail']} keyword: {first_match['value']}"
            if first_match
            else ""
        )
        return add_extension_cors(
            jsonify({"blocked": first_match is not None, "reason": reason})
        )

    @application.route("/api/rules", methods=["GET", "OPTIONS"])
    @csrf.exempt
    def extension_rules():
        if request.method == "OPTIONS":
            return add_extension_cors(application.response_class(status=204))
        domains = [
            row["domain"]
            for row in get_db().execute("SELECT domain FROM domains ORDER BY domain")
        ]
        return add_extension_cors(jsonify({"domains": domains}))

    def setting(key):
        row = get_db().execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def save_setting(key, value):
        get_db().execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        get_db().commit()

    def legacy_pin_is_valid(password):
        if not re.fullmatch(r"\d{4}", password or ""):
            return False
        salt_row = get_db().execute(
            "SELECT value FROM settings WHERE key = 'pin_salt'"
        ).fetchone()
        hash_row = get_db().execute(
            "SELECT value FROM settings WHERE key = 'pin_hash'"
        ).fetchone()
        if salt_row is None or hash_row is None:
            return False
        try:
            expected = bytes.fromhex(hash_row["value"])
            salt = bytes.fromhex(salt_row["value"])
        except ValueError:
            application.logger.error("Stored legacy PIN credentials are malformed.")
            return False
        return hmac.compare_digest(expected, hash_pin(password, salt))

    def verify_stored_password(password):
        stored_hash = setting("master_password_hash")
        if stored_hash:
            try:
                return check_password_hash(stored_hash, password), False
            except (ValueError, TypeError):
                application.logger.exception("Stored master-password hash is invalid.")
                return False, False
        if setting("pin_hash"):
            return legacy_pin_is_valid(password), True
        return False, False

    def client_identity():
        remote_address = request.remote_addr or "unknown"
        secret = application.config["SECRET_KEY"]
        key = secret.encode("utf-8") if isinstance(secret, str) else secret
        return hmac.new(
            key, remote_address.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def lockout_remaining(identity=None):
        identity = identity or client_identity()
        row = get_db().execute(
            "SELECT locked_until FROM auth_lockouts WHERE identity = ?",
            (identity,),
        ).fetchone()
        if row is None:
            return 0
        return max(0, int(row["locked_until"] - time.time() + 0.999))

    def check_password_with_lockout(password):
        identity = client_identity()
        remaining = lockout_remaining(identity)
        if remaining:
            return False, False, remaining

        if not isinstance(password, str) or len(password) > MAX_PASSWORD_LENGTH:
            valid, is_legacy = False, False
        else:
            valid, is_legacy = verify_stored_password(password)
        database = get_db()
        if valid:
            database.execute(
                "DELETE FROM auth_lockouts WHERE identity = ?", (identity,)
            )
            database.commit()
            return True, is_legacy, 0

        row = database.execute(
            "SELECT failed_attempts FROM auth_lockouts WHERE identity = ?",
            (identity,),
        ).fetchone()
        attempts = (row["failed_attempts"] if row else 0) + 1
        locked_until = time.time() + LOCKOUT_SECONDS if attempts >= MAX_FAILED_ATTEMPTS else 0
        database.execute(
            "INSERT INTO auth_lockouts (identity, failed_attempts, locked_until) "
            "VALUES (?, ?, ?) ON CONFLICT(identity) DO UPDATE SET "
            "failed_attempts = excluded.failed_attempts, "
            "locked_until = excluded.locked_until",
            (
                identity,
                0 if locked_until else attempts,
                locked_until,
            ),
        )
        database.commit()
        if locked_until:
            return False, False, LOCKOUT_SECONDS
        return False, False, 0

    def format_lockout(seconds):
        minutes, remaining_seconds = divmod(seconds, 60)
        return f"{minutes}m {remaining_seconds}s" if minutes else f"{remaining_seconds}s"

    def password_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            stored_hash = setting("master_password_hash")
            session_hash = session.get("password_hash_snapshot")
            if (
                not stored_hash
                or not isinstance(session_hash, str)
                or not hmac.compare_digest(session_hash, stored_hash)
            ):
                session.pop("password_hash_snapshot", None)
                flash("Enter your master password to access protected controls.", "warning")
                post_destinations = {
                    "toggle_protection": url_for("dashboard"),
                    "delete_domain": url_for("blocklist"),
                    "delete_keyword": url_for("keywords"),
                }
                next_url = (
                    post_destinations.get(
                        request.endpoint, request.path
                    )
                    if request.method == "POST"
                    else request.full_path.rstrip("?")
                )
                return redirect(url_for("unlock", next=next_url))
            if setting("anti_vpn_lock_active") == "1":
                flash(
                    "Protected filtering controls are locked by Anti-VPN enforcement. "
                    "Review Network Security in Password Settings.",
                    "danger",
                )
                return redirect(url_for("settings"))
            return view(*args, **kwargs)

        return wrapped

    @application.get("/")
    def dashboard():
        database = get_db()
        return render_template(
            "dashboard.html",
            protection_enabled=setting("protection_enabled") == "1",
            anti_vpn_enabled=setting("anti_vpn_enabled") == "1",
            anti_vpn_lock_active=setting("anti_vpn_lock_active") == "1",
            anti_vpn_lock_reason=setting("anti_vpn_lock_reason") or "",
            domain_count=database.execute(
                "SELECT COUNT(*) FROM domains"
            ).fetchone()[0],
            keyword_count=database.execute(
                "SELECT COUNT(*) FROM keywords"
            ).fetchone()[0],
        )

    @application.post("/protection")
    @password_required
    def toggle_protection():
        if setting("anti_vpn_lock_active") == "1":
            flash(
                "Protection cannot be changed while Anti-VPN enforcement is in lock mode.",
                "danger",
            )
            return redirect(url_for("dashboard"))
        current = setting("protection_enabled") == "1"
        save_setting("protection_enabled", "0" if current else "1")
        flash(
            "Protection is now ON." if not current else "Protection is now OFF.",
            "success" if not current else "warning",
        )
        return redirect(url_for("dashboard"))

    @application.route("/safe-search", methods=["GET", "POST"])
    @password_required
    def safe_search():
        if request.method == "POST":
            for provider in SEARCH_PROVIDERS:
                key = f"safe_search_{provider.lower()}"
                save_setting(key, "1" if request.form.get(key) == "on" else "0")
            save_setting(
                "youtube_restricted",
                "1" if request.form.get("youtube_restricted") == "on" else "0",
            )
            flash("Safe-search preferences saved.", "success")
            return redirect(url_for("safe_search"))
        preferences = {
            f"safe_search_{provider.lower()}": setting(
                f"safe_search_{provider.lower()}"
            )
            == "1"
            for provider in SEARCH_PROVIDERS
        }
        preferences["youtube_restricted"] = (
            setting("youtube_restricted") == "1"
        )
        return render_template("safe_search.html", preferences=preferences)

    @application.route("/blocklist", methods=["GET", "POST"])
    @password_required
    def blocklist():
        database = get_db()
        if request.method == "POST":
            domain = normalize_domain(request.form.get("domain", ""))
            if domain is None:
                flash("Enter a valid domain name, such as example.com.", "danger")
            else:
                try:
                    database.execute(
                        "INSERT INTO domains (domain) VALUES (?)", (domain,)
                    )
                    database.commit()
                    flash(f"{domain} added to the domain blocklist.", "success")
                except sqlite3.IntegrityError:
                    flash(f"{domain} is already on the blocklist.", "info")
            return redirect(url_for("blocklist"))
        domains = database.execute(
            "SELECT id, domain, created_at FROM domains ORDER BY domain"
        ).fetchall()
        return render_template("blocklist.html", domains=domains)

    @application.post("/blocklist/<int:domain_id>/delete")
    @password_required
    def delete_domain(domain_id):
        cursor = get_db().execute("DELETE FROM domains WHERE id = ?", (domain_id,))
        get_db().commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Domain removed from the blocklist.", "success")
        return redirect(url_for("blocklist"))

    @application.route("/keywords", methods=["GET", "POST"])
    @password_required
    def keywords():
        database = get_db()
        if request.method == "POST":
            keyword = normalize_keyword(request.form.get("keyword", ""))
            language = request.form.get("language", "")
            if not keyword or len(keyword) > 80:
                flash("Enter a keyword between 1 and 80 characters.", "danger")
            elif language not in LANGUAGES:
                flash("Choose a supported keyword language.", "danger")
            else:
                normalized = normalize_keyword(keyword)
                try:
                    database.execute(
                        "INSERT INTO keywords (keyword, normalized, language) "
                        "VALUES (?, ?, ?)",
                        (keyword, normalized, language),
                    )
                    database.commit()
                    flash(f"Keyword added to the {language} filter.", "success")
                except sqlite3.IntegrityError:
                    flash("That keyword is already in this language list.", "info")
            return redirect(url_for("keywords"))
        entries = database.execute(
            "SELECT id, keyword, language FROM keywords "
            "ORDER BY language, normalized"
        ).fetchall()
        return render_template(
            "keywords.html", entries=entries, languages=LANGUAGES
        )

    @application.post("/keywords/<int:keyword_id>/delete")
    @password_required
    def delete_keyword(keyword_id):
        cursor = get_db().execute(
            "DELETE FROM keywords WHERE id = ?", (keyword_id,)
        )
        get_db().commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Keyword removed from the filter.", "success")
        return redirect(url_for("keywords"))

    @application.route("/pin", methods=["GET", "POST"])
    def unlock():
        next_url = safe_next_url(request.args.get("next", ""))
        is_setup = not setting("master_password_hash") and not setting("pin_hash")
        if request.method == "POST":
            next_url = safe_next_url(request.form.get("next", ""))
            if is_setup:
                password = request.form.get("password", "")
                confirmation = request.form.get("confirm_password", "")
                policy_error = password_policy_error(password)
                if policy_error:
                    flash(policy_error, "danger")
                elif password != confirmation:
                    flash("The password entries do not match.", "danger")
                else:
                    cursor = get_db().execute(
                        "INSERT OR IGNORE INTO settings (key, value) "
                        "VALUES ('master_password_hash', ?)",
                        (password_hash(password),),
                    )
                    get_db().commit()
                    if cursor.rowcount == 0:
                        flash(
                            "Password setup has already been completed. Sign in instead.",
                            "warning",
                        )
                        is_setup = False
                    else:
                        session["password_hash_snapshot"] = setting(
                            "master_password_hash"
                        )
                        flash("Master password created. Protected controls are unlocked.", "success")
                        return redirect(next_url or url_for("dashboard"))
            else:
                valid, is_legacy, remaining = check_password_with_lockout(
                    request.form.get("password", "")
                )
                if remaining:
                    flash(
                        f"Too many failed attempts. Try again in {format_lockout(remaining)}.",
                        "danger",
                    )
                elif valid and is_legacy:
                    session.pop("password_hash_snapshot", None)
                    flash(
                        "Your old PIN was accepted. Set a strong master password to finish upgrading.",
                        "warning",
                    )
                    return redirect(url_for("settings"))
                elif valid:
                    session["password_hash_snapshot"] = setting(
                        "master_password_hash"
                    )
                    flash("Password verified. Protected controls are unlocked.", "success")
                    return redirect(next_url or url_for("dashboard"))
                else:
                    flash("Incorrect password. Please try again.", "danger")
        return render_template(
            "pin.html",
            next_url=next_url,
            is_setup=is_setup,
            lockout_seconds=lockout_remaining(),
            legacy_password=bool(setting("pin_hash")) and not setting("master_password_hash"),
        )

    @application.route("/settings", methods=["GET", "POST"])
    def settings():
        if not setting("master_password_hash") and not setting("pin_hash"):
            return redirect(url_for("unlock", next=url_for("settings")))
        if request.method == "POST":
            current_password = request.form.get("current_password", "")
            valid, _is_legacy, remaining = check_password_with_lockout(current_password)
            if remaining:
                flash(
                    f"Too many failed attempts. Try again in {format_lockout(remaining)}.",
                    "danger",
                )
            elif not valid:
                flash("Current password is incorrect.", "danger")
            else:
                action = request.form.get("action", "change_password")
                if action == "toggle_anti_vpn":
                    with network_monitor_lock:
                        enabled = request.form.get("anti_vpn_enabled") == "1"
                        save_setting("anti_vpn_enabled", "1" if enabled else "0")
                        record_completed_security_event(
                            get_db(),
                            "enforcement_setting",
                            f"Anti-VPN enforcement {'enabled' if enabled else 'disabled'} by administrator.",
                        )
                        if enabled:
                            monitor_iteration()
                            flash("Anti-VPN enforcement enabled; a network scan was run.", "success")
                        else:
                            resolve_active_security_alerts(get_db())
                            save_setting("anti_vpn_lock_active", "0")
                            save_setting("anti_vpn_lock_reason", "")
                            save_setting("anti_vpn_last_status", "Disabled")
                            flash(
                                "Anti-VPN enforcement disabled and the security lock cleared.",
                                "warning",
                            )
                elif action == "save_proxy_allowlist":
                    allowlist = request.form.get("authorized_proxy_hosts", "")
                    normalized = normalize_proxy_allowlist(allowlist)
                    if normalized is None:
                        flash(
                            "Enter proxy hostnames or IP addresses separated by commas.",
                            "danger",
                        )
                    else:
                        with network_monitor_lock:
                            save_setting("authorized_proxy_hosts", ", ".join(normalized))
                            flash("Authorized proxy list saved.", "success")
                            if setting("anti_vpn_enabled") == "1":
                                monitor_iteration()
                elif action == "change_password":
                    new_password = request.form.get("new_password", "")
                    confirmation = request.form.get("confirm_password", "")
                    policy_error = password_policy_error(new_password)
                    if policy_error:
                        flash(policy_error, "danger")
                    elif new_password != confirmation:
                        flash("The new password entries do not match.", "danger")
                    elif hmac.compare_digest(new_password, current_password):
                        flash("Choose a password different from your current password.", "warning")
                    else:
                        database = get_db()
                        database.execute(
                            "INSERT INTO settings (key, value) VALUES "
                            "('master_password_hash', ?) ON CONFLICT(key) "
                            "DO UPDATE SET value = excluded.value",
                            (password_hash(new_password),),
                        )
                        database.execute(
                            "DELETE FROM settings WHERE key IN ('pin_salt', 'pin_hash')"
                        )
                        database.commit()
                        session["password_hash_snapshot"] = setting(
                            "master_password_hash"
                        )
                        flash("Your master password has been updated.", "success")
                        return redirect(url_for("settings"))
                else:
                    abort(400)
        alerts = get_db().execute(
            "SELECT category, detail, created_at, resolved_at "
            "FROM security_alerts ORDER BY id DESC LIMIT ?",
            (MAX_ALERTS_TO_DISPLAY,),
        ).fetchall()
        return render_template(
            "settings.html",
            lockout_seconds=lockout_remaining(),
            legacy_password=bool(setting("pin_hash")) and not setting("master_password_hash"),
            anti_vpn_enabled=setting("anti_vpn_enabled") == "1",
            anti_vpn_lock_active=setting("anti_vpn_lock_active") == "1",
            anti_vpn_lock_reason=setting("anti_vpn_lock_reason") or "",
            anti_vpn_last_scan=setting("anti_vpn_last_scan") or "",
            anti_vpn_last_status=setting("anti_vpn_last_status") or "Not scanned",
            authorized_proxy_hosts=setting("authorized_proxy_hosts") or "",
            security_alerts=alerts,
        )

    @application.post("/lock")
    def lock():
        session.pop("password_hash_snapshot", None)
        flash("Protected controls are locked.", "info")
        return redirect(url_for("dashboard"))

    @application.route("/simulator", methods=["GET", "POST"])
    def simulator():
        query = ""
        matches = []
        tested = False
        if request.method == "POST":
            query = normalize_keyword(request.form.get("query", ""))
            if not query:
                flash("Enter a search phrase to test.", "warning")
            elif len(query) > MAX_QUERY_LENGTH:
                flash(
                    f"Search phrases must be {MAX_QUERY_LENGTH} characters or fewer.",
                    "danger",
                )
            else:
                tested = True
                matches = find_filter_matches(get_db(), query)
        return render_template(
            "simulator.html",
            query=query,
            matches=matches,
            tested=tested,
        )

    return application


def record_security_alert(category, detail):
    database = g.get("db")
    if database is None:
        raise RuntimeError("Security alerts can only be recorded inside an app context.")
    database.execute(
        "INSERT OR IGNORE INTO security_alerts (category, detail) VALUES (?, ?)",
        (category[:80], detail[:1000]),
    )
    database.commit()


def record_completed_security_event(database, category, detail):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    database.execute(
        "INSERT INTO security_alerts (category, detail, created_at, resolved_at) "
        "VALUES (?, ?, ?, ?)",
        (category[:80], detail[:1000], timestamp, timestamp),
    )
    database.commit()


def resolve_active_security_alerts(database=None):
    database = database or g.get("db")
    if database is None:
        raise RuntimeError("Security alerts can only be resolved inside an app context.")
    database.execute(
        "UPDATE security_alerts SET resolved_at = ? WHERE resolved_at IS NULL",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"),),
    )
    database.commit()


def normalize_proxy_host(value):
    value = (value or "").strip()
    if not value or len(value) > 512:
        return None
    try:
        parsed = urlsplit(value if "://" in value else f"//{value}")
        if parsed.username or parsed.password:
            return None
        hostname = parsed.hostname
        if not hostname:
            return None
        try:
            return str(ipaddress.ip_address(hostname))
        except ValueError:
            encoded = hostname.encode("idna").decode("ascii").lower().rstrip(".")
    except (UnicodeError, ValueError):
        return None
    labels = encoded.split(".")
    if any(not DOMAIN_LABEL.fullmatch(label) for label in labels):
        return None
    return encoded


def normalize_proxy_allowlist(value):
    if not isinstance(value, str) or len(value) > 4096:
        return None
    hosts = []
    for entry in re.split(r"[,;\r\n]+", value):
        entry = entry.strip()
        if not entry:
            continue
        host = normalize_proxy_host(entry)
        if host is None:
            return None
        if host not in hosts:
            hosts.append(host)
        if len(hosts) > 100:
            return None
    return hosts


def parse_authorized_proxy_hosts(value):
    hosts = normalize_proxy_allowlist(value)
    if hosts is None:
        raise ValueError("Stored authorized proxy list is invalid.")
    return set(hosts)


def is_host_authorized(host, authorized_hosts):
    normalized = normalize_proxy_host(host)
    return bool(
        normalized
        and any(
            normalized == authorized
            or normalized.endswith(f".{authorized}")
            for authorized in authorized_hosts
        )
    )


def proxy_hosts_from_value(value):
    hosts = []
    unknown_proxy = False
    for item in re.split(r"[;,\s]+", value or ""):
        item = item.strip()
        if not item or item.upper() in {"DIRECT", "<LOCAL>"}:
            continue
        if "=" in item:
            item = item.rsplit("=", 1)[1]
        if not item or item.upper() in {"DIRECT", "<LOCAL>"}:
            continue
        host = normalize_proxy_host(item)
        if host:
            if host not in hosts:
                hosts.append(host)
        else:
            unknown_proxy = True
    return hosts, unknown_proxy


def run_windows_powershell(script):
    executable = os.environ.get("SYSTEMROOT", r"C:\Windows") + r"\System32\WindowsPowerShell\v1.0\powershell.exe"
    completed = subprocess.run(
        [
            executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Windows adapter query failed: {completed.stderr.strip() or completed.returncode}"
        )
    try:
        return json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError as error:
        raise RuntimeError("Windows adapter query returned invalid JSON.") from error


def detect_windows_adapters():
    script = r"""
$adapters = @(Get-NetAdapter -ErrorAction Stop | Select-Object `
  @{Name='name';Expression={$_.Name}}, `
  @{Name='description';Expression={$_.InterfaceDescription}}, `
  @{Name='status';Expression={$_.Status.ToString()}})
$connections = @()
if (Get-Command Get-VpnConnection -ErrorAction SilentlyContinue) {
  $connections += @(Get-VpnConnection -ErrorAction SilentlyContinue |
    Where-Object {$_.ConnectionStatus -eq 'Connected'} |
    Select-Object @{Name='name';Expression={$_.Name}},
      @{Name='status';Expression={$_.ConnectionStatus}})
  $connections += @(Get-VpnConnection -AllUserConnection -ErrorAction SilentlyContinue |
    Where-Object {$_.ConnectionStatus -eq 'Connected'} |
    Select-Object @{Name='name';Expression={$_.Name}},
      @{Name='status';Expression={$_.ConnectionStatus}})
}
[pscustomobject]@{adapters=$adapters; vpnConnections=$connections} |
  ConvertTo-Json -Compress -Depth 4
"""
    result = run_windows_powershell(script)
    adapters = result.get("adapters", []) if isinstance(result, dict) else []
    connections = result.get("vpnConnections", []) if isinstance(result, dict) else []
    if isinstance(adapters, dict):
        adapters = [adapters]
    if isinstance(connections, dict):
        connections = [connections]
    return adapters, connections


def detect_windows_proxy_settings():
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            values = {}
            for name in ("ProxyEnable", "ProxyServer", "AutoConfigURL", "AutoDetect"):
                try:
                    values[name] = winreg.QueryValueEx(key, name)[0]
                except FileNotFoundError:
                    values[name] = 0 if name in {"ProxyEnable", "AutoDetect"} else ""
    except FileNotFoundError:
        values = {}

    observations = []
    if values.get("ProxyEnable") == 1:
        proxy_value = str(values.get("ProxyServer", "")).strip()
        hosts, unknown = proxy_hosts_from_value(proxy_value)
        if not proxy_value or unknown or not hosts:
            observations.append(
                {"category": "proxy", "detail": "Windows user proxy enabled (host could not be identified)", "host": None}
            )
        for host in hosts:
            observations.append(
                {"category": "proxy", "detail": f"Windows user proxy: {host}", "host": host}
            )

    pac_url = str(values.get("AutoConfigURL", "")).strip()
    if pac_url:
        host = normalize_proxy_host(pac_url)
        observations.append(
            {
                "category": "proxy",
                "detail": (
                    "Windows automatic proxy configuration: "
                    f"{host}" if host else "Windows automatic proxy configuration is active"
                ),
                "host": host,
            }
        )

    if values.get("AutoDetect") == 1:
        observations.append(
            {
                "category": "proxy",
                "detail": "Windows automatic proxy (WPAD) detection is enabled",
                "host": None,
            }
        )

    executable = os.environ.get("SYSTEMROOT", r"C:\Windows") + r"\System32\netsh.exe"
    completed = subprocess.run(
        [executable, "winhttp", "show", "proxy"],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"WinHTTP proxy query failed: {completed.stderr.strip() or completed.returncode}"
        )
    winhttp_output = completed.stdout.strip()
    if winhttp_output and not re.search(
        r"direct access\s*\(no proxy server\)", winhttp_output, re.IGNORECASE
    ):
        match = re.search(
            r"Proxy Server(?:\(s\))?\s*:\s*(.+)",
            winhttp_output,
            re.IGNORECASE,
        )
        proxy_value = match.group(1).splitlines()[0].strip() if match else ""
        hosts, unknown = proxy_hosts_from_value(proxy_value)
        if not proxy_value or unknown or not hosts:
            observations.append(
                {
                    "category": "proxy",
                    "detail": "WinHTTP proxy is configured (host could not be identified)",
                    "host": None,
                }
            )
        for host in hosts:
            observations.append(
                {"category": "proxy", "detail": f"WinHTTP proxy: {host}", "host": host}
            )
    return observations


def detect_non_windows_adapters():
    if platform.system() == "Linux":
        completed = subprocess.run(
            ["ip", "-j", "link", "show"],
            capture_output=True,
            text=True,
            timeout=8,
            check=True,
        )
        try:
            adapters = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError("Network adapter query returned invalid JSON.") from error
        return [
            (item.get("ifname", ""), " ".join(item.get("altname", [])), "UP" in item.get("flags", []))
            for item in adapters
        ]
    if platform.system() == "Darwin":
        completed = subprocess.run(
            ["ifconfig", "-a"],
            capture_output=True,
            text=True,
            timeout=8,
            check=True,
        )
        adapters = []
        current_name = ""
        current_text = ""
        for line in completed.stdout.splitlines():
            if line and not line[0].isspace() and ":" in line:
                if current_name:
                    adapters.append((current_name, current_text, "UP" in current_text))
                current_name = line.split(":", 1)[0]
                current_text = line
            else:
                current_text += " " + line
        if current_name:
            adapters.append((current_name, current_text, "UP" in current_text))
        return adapters
    raise RuntimeError(f"Adapter monitoring is unsupported on {platform.system()}.")


def inspect_network_security():
    observations = []
    if os.name == "nt":
        adapters, connections = detect_windows_adapters()
        for adapter in adapters:
            name = str(adapter.get("name", ""))
            description = str(adapter.get("description", ""))
            status = str(adapter.get("status", ""))
            label = f"{name} ({description})".strip()
            if status.casefold() in {"up", "connected"} and VPN_ADAPTER_PATTERN.search(label):
                observations.append(
                    {
                        "category": "vpn_adapter",
                        "detail": f"Active VPN adapter: {label}",
                        "host": None,
                    }
                )
        for connection in connections:
            observations.append(
                {
                    "category": "vpn_connection",
                    "detail": f"Windows VPN connection is active: {connection.get('name', 'unknown')}",
                    "host": None,
                }
            )
        observations.extend(detect_windows_proxy_settings())
    else:
        adapters = detect_non_windows_adapters()
        for name, description, is_up in adapters:
            label = f"{name} {description}"
            if is_up and VPN_ADAPTER_PATTERN.search(label):
                observations.append(
                    {
                        "category": "vpn_adapter",
                        "detail": f"Active VPN adapter: {label[:300]}",
                        "host": None,
                    }
                )
        for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            value = os.environ.get(variable, "").strip()
            if value:
                host = normalize_proxy_host(value)
                observations.append(
                    {
                        "category": "proxy",
                        "detail": f"Process proxy setting {variable} is active",
                        "host": host,
                    }
                )
    return observations


def hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, LEGACY_PIN_ITERATIONS
    )


def password_policy_error(password):
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be no longer than {MAX_PASSWORD_LENGTH} characters."
    if not any(character.isalpha() for character in password):
        return "Password must include at least one letter."
    if not any(character.isdigit() for character in password):
        return "Password must include at least one number."
    if not any(not character.isalnum() and not character.isspace() for character in password):
        return "Password must include at least one special character."
    return None


def password_hash(password):
    return generate_password_hash(password, method="scrypt")


def safe_next_url(value):
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return ""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return ""
    return parts.path + (f"?{parts.query}" if parts.query else "")


def normalize_keyword(value):
    return unicodedata.normalize("NFKC", value or "").strip()


def normalize_domain(value):
    value = (value or "").strip().rstrip(".")
    if not value or len(value) > 253 or any(character.isspace() for character in value):
        return None
    try:
        domain = value.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None
    try:
        ipaddress.ip_address(domain)
        return None
    except ValueError:
        pass
    labels = domain.split(".")
    if len(labels) < 2 or any(not DOMAIN_LABEL.fullmatch(label) for label in labels):
        return None
    return domain


def find_filter_matches(database, value):
    normalized_value = normalize_keyword(value).casefold()
    candidates = [normalized_value]
    host = ""
    try:
        parsed = urlsplit(value if "://" in value else "")
        hostname = parsed.hostname or ""
    except ValueError:
        parsed = urlsplit("")
        hostname = ""
    if parsed.scheme and parsed.netloc:
        host = (normalize_domain(hostname) or "").casefold()
        candidates.extend(
            normalize_keyword(part).casefold()
            for _key, part in parse_qsl(parsed.query, keep_blank_values=True)
        )

    matches = []
    for entry in database.execute("SELECT domain FROM domains ORDER BY domain"):
        domain = entry["domain"].casefold()
        host_matches = host == domain or host.endswith(f".{domain}")
        text_matches = any(
            re.search(
                rf"(?<![\w.-])(?:[\w-]+\.)*{re.escape(domain)}(?![\w.-])",
                candidate,
                flags=re.UNICODE,
            )
            for candidate in candidates
        )
        if host_matches or text_matches:
            matches.append(
                {
                    "type": "Blocked domain",
                    "value": entry["domain"],
                    "detail": "Domain blocklist",
                }
            )

    matches.extend(find_keyword_matches(database, *candidates))
    return matches


def find_keyword_matches(database, *values):
    candidates = [
        normalize_keyword(value).casefold()
        for value in values
        if isinstance(value, str)
    ]
    matches = []
    for entry in database.execute(
        "SELECT keyword, language FROM keywords ORDER BY language, keyword"
    ):
        keyword = normalize_keyword(entry["keyword"]).casefold()
        if keyword and any(keyword in candidate for candidate in candidates):
            matches.append(
                {
                    "type": "Keyword",
                    "value": entry["keyword"],
                    "detail": entry["language"],
                }
            )
    return matches


def inspect_filter_input(database, value):
    matches = find_filter_matches(database, value)
    if not matches:
        return False, ""
    first = matches[0]
    if first["type"] == "Keyword":
        reason = f"Matched {first['detail']} keyword: {first['value']}"
    else:
        reason = f"Matched blocked domain: {first['value']}"
    return True, reason


app = create_app()


def run_desktop(window_only=False):
    try:
        import webview
    except ImportError as error:
        raise RuntimeError(
            "The desktop window requires pywebview. Install requirements.txt "
            "and try again."
        ) from error

    host = os.environ.get("CONTENT_GUARD_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTENT_GUARD_PORT", "5000"))
    debug = os.environ.get("CONTENT_GUARD_DEBUG") == "1"
    app.debug = debug
    window_host = {
        "0.0.0.0": "127.0.0.1",
        "::": "::1",
    }.get(host, host)
    url_host = f"[{window_host}]" if ":" in window_host else window_host
    server = None
    if not window_only:
        from werkzeug.serving import make_server

        server = make_server(host, port, app, threaded=True)
        threading.Thread(
            target=server.serve_forever,
            name="content-guard-web-server",
            daemon=True,
        ).start()

    try:
        webview.create_window(
            "Content Guard",
            f"http://{url_host}:{port}/",
            width=1120,
            height=800,
            min_size=(760, 560),
        )
        webview.start(debug=debug)
    finally:
        if server is not None:
            server.shutdown()


if __name__ == "__main__":
    run_desktop(window_only="--window-only" in sys.argv[1:])
