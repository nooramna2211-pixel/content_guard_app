[app]

title = Content Guard
package.name = contentguard
package.domain = org.contentguard
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,json,html,css,js,svg,woff,woff2,ttf,txt,xml
source.include_patterns = app.py,main.py,android/**,templates/**,static/**
source.exclude_dirs = .venv,build,dist,extension,instance,packaging,tests,__pycache__
version = 1.0.0
requirements = python3,kivy,pyjnius,flask,flask-wtf,werkzeug
orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECEIVE_BOOT_COMPLETED, BIND_DEVICE_ADMIN, ACCESSIBILITY_SERVICE
android.api = 35
android.minapi = 26
android.ndk = 27c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.extra_manifest_application_arguments = android/extra_manifest_application_arguments.xml

[buildozer]
log_level = 2
warn_on_root = 1
