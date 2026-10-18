"""Android Kivy entry point hosting the Content Guard Flask app in WebView."""

import os
from pathlib import Path
import secrets
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label


class ContentGuardAndroidApp(App):
    title = "Content Guard"

    def build(self):
        user_data = Path(self.user_data_dir)
        user_data.mkdir(parents=True, exist_ok=True)
        os.environ["CONTENT_GUARD_DATABASE"] = str(
            user_data / "content_guard.sqlite3"
        )
        secret_path = user_data / "session_secret"
        if not secret_path.exists():
            secret_path.write_text(secrets.token_urlsafe(48), encoding="ascii")
        os.environ["CONTENT_GUARD_SECRET"] = secret_path.read_text(
            encoding="ascii"
        )
        os.environ["CONTENT_GUARD_HOST"] = "127.0.0.1"
        os.environ["CONTENT_GUARD_PORT"] = "5000"

        from app import app as flask_app
        from werkzeug.serving import make_server

        self.server = make_server(
            "127.0.0.1",
            5000,
            flask_app,
            threaded=True,
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            name="content-guard-android-web",
            daemon=True,
        )
        self.server_thread.start()
        Clock.schedule_once(self.open_webview, 0.5)
        return Label(text="Starting Content Guard…")

    def open_webview(self, _dt):
        from jnius import PythonJavaClass, autoclass, java_method

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        web_view_class = autoclass("android.webkit.WebView")
        web_client_class = autoclass("android.webkit.WebViewClient")
        layout_params_class = autoclass("android.view.ViewGroup$LayoutParams")

        class UiRunnable(PythonJavaClass):
            __javainterfaces__ = ["java/lang/Runnable"]
            __javacontext__ = "app"

            @java_method("()V")
            def run(inner_self):
                self.web_view = web_view_class(activity)
                settings = self.web_view.getSettings()
                settings.setJavaScriptEnabled(True)
                settings.setDomStorageEnabled(True)
                self.web_view.setWebViewClient(web_client_class())
                activity.setContentView(
                    self.web_view,
                    layout_params_class(
                        layout_params_class.MATCH_PARENT,
                        layout_params_class.MATCH_PARENT,
                    ),
                )
                self.web_view.loadUrl("http://127.0.0.1:5000/")

        self.ui_runnable = UiRunnable()
        activity.runOnUiThread(self.ui_runnable)

    def on_stop(self):
        server = getattr(self, "server", None)
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    ContentGuardAndroidApp().run()
