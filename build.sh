#!/usr/bin/env bash
#
# Baut aus dem Quellcode eine doppelklickbare macOS-App:  dist/Neko.app
#
# Wichtig 1: Es wird bewusst ein Python mit Tcl/Tk 8.6 verwendet. Nur damit
# funktioniert die transparente Fenster-Darstellung auf macOS zuverlässig
# (Tk 9.0 rendert den Hintergrund schwarz). Die gebaute App bringt dieses Tk
# selbst mit — die Nutzer brauchen also gar kein Python.
#
# Wichtig 2: Wir bauen im "onedir"-Modus (--windowed, ohne --onefile). Ein
# .app-Bundle IST bereits ein Ordner; PyInstaller rät ausdrücklich von
# --onefile bei .app ab (kollidiert mit Gatekeeper und wird in v7 zum Fehler).
# onedir startet schneller und läuft auf fremden Macs zuverlässiger.
#
# Aufruf:   ./build.sh
#
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Neko — Build startet"

# ── 1) Python mit Tk 8.6 wählen ──────────────────────────────────────────────
PYTHON=""
if command -v uv >/dev/null 2>&1; then
    echo "==> uv gefunden — richte Python 3.9 (Tk 8.6) ein…"
    uv python install 3.9 >/dev/null 2>&1 || true
    PYTHON="$(uv python find 3.9 2>/dev/null || true)"
fi

if [ -z "${PYTHON}" ] || [ ! -x "${PYTHON}" ]; then
    echo "!! Kein Tk-8.6-Python über uv gefunden — nutze system python3."
    echo "!! Hinweis: Hat dieses python3 Tk 9.0, wird der Hintergrund schwarz."
    echo "!! Für echte Transparenz: 'curl -LsSf https://astral.sh/uv/install.sh | sh' und neu bauen."
    PYTHON="$(command -v python3)"
fi

TKV="$("${PYTHON}" -c 'import tkinter; print(tkinter.TkVersion)' 2>/dev/null || echo '?')"
echo "==> Python: ${PYTHON}"
echo "==> Tk-Version: ${TKV}"

# ── 2) Isolierte Build-Umgebung (verändert dein System-Python nicht) ─────────
echo "==> Erstelle Build-Umgebung & installiere PyInstaller…"
rm -rf .buildenv build dist
"${PYTHON}" -m venv .buildenv
# shellcheck disable=SC1091
source .buildenv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet pyinstaller

# ── 3) App bauen ─────────────────────────────────────────────────────────────
echo "==> Baue dist/Neko.app …"
pyinstaller --noconfirm --clean \
    --windowed \
    --name Neko \
    --osx-bundle-identifier com.neko.focuscat \
    src/desktop_katze.py

deactivate

echo ""
echo "✓ Fertig!  →  dist/Neko.app"
echo "   Testen:   open dist/Neko.app"
echo "   Teilen:   'cd dist && zip -r -y Neko.app.zip Neko.app'  und die .zip als GitHub-Release hochladen."
