#!/usr/bin/env python3
"""Patch a freshly generated Flutter Android project for Chaquopy/Python."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ANDROID = ROOT / "android"
PACKAGE = "com.pyvault.app"

def patch_settings():
    p = ANDROID / "settings.gradle.kts"
    text = p.read_text()
    if 'maven("https://chaquo.com/maven")' not in text:
        text = re.sub(r'(repositories\s*\{)', r'\1\n        maven("https://chaquo.com/maven")', text, count=1)
    if "com.chaquo.python" not in text:
        text = re.sub(r'(plugins\s*\{)', r'\1\n    id("com.chaquo.python") version "17.1.0" apply false', text, count=1)
    p.write_text(text)

def patch_app():
    p = ANDROID / "app/build.gradle.kts"
    text = p.read_text()
    if "com.chaquo.python" not in text:
        text = re.sub(r'(plugins\s*\{)', r'\1\n    id("com.chaquo.python")', text, count=1)
    text = re.sub(r'namespace\s*=\s*"[^"]+"', f'namespace = "{PACKAGE}"', text, count=1)
    text = re.sub(r'applicationId\s*=\s*"[^"]+"', f'applicationId = "{PACKAGE}"', text, count=1)
    if re.search(r'minSdk\s*=\s*\d+', text):
        text = re.sub(r'minSdk\s*=\s*\d+', 'minSdk = 24', text, count=1)
    else:
        text = re.sub(r'(defaultConfig\s*\{)', r'\1\n        minSdk = 24', text, count=1)
    if 'abiFilters += listOf("arm64-v8a")' not in text:
        text = re.sub(r'(defaultConfig\s*\{)', r'\1\n        ndk { abiFilters += listOf("arm64-v8a") }', text, count=1)
    if "chaquopy {" not in text:
        block = '''\n\nchaquopy {\n    defaultConfig {\n        version = "3.13"\n        buildPython("python")\n        pip {\n            install("cryptography==42.0.8")\n        }\n    }\n}\n'''
        text += block
    p.write_text(text)

def main():
    if not (ANDROID / "settings.gradle.kts").exists() or not (ANDROID / "app/build.gradle.kts").exists():
        raise SystemExit("Expected Flutter-generated Android Gradle Kotlin DSL files")
    patch_settings()
    patch_app()
    kotlin = ANDROID / "app/src/main/kotlin/com/pyvault/app/MainActivity.kt"
    kotlin.parent.mkdir(parents=True, exist_ok=True)
    kotlin.write_text((ROOT / "MainActivity.kt.template").read_text())
    manifest = ANDROID / "app/src/main/AndroidManifest.xml"
    if manifest.exists():
        xml = manifest.read_text()
        xml = re.sub(r'android:label="[^"]*"', 'android:label="PyVault"', xml, count=1)
        manifest.write_text(xml)
    py = ANDROID / "app/src/main/python"
    py.mkdir(parents=True, exist_ok=True)
    (py / "protector_core.py").write_text((ROOT / "protector_core.py").read_text())
    print("Configured Chaquopy Python 3.13 / arm64-v8a and copied the offline protector.")

if __name__ == "__main__":
    main()
