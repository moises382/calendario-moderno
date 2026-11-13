#!/bin/zsh
# Instala un Python 3.13 con Tk 9 en la carpeta del usuario, sin permisos de
# administrador. Necesario porque el Tk 8.5 del sistema no dibuja la interfaz
# en macOS 27.
set -euo pipefail

DEST="$HOME/.local/share/calendario-python"

case "$(uname -m)" in
  arm64)  SLUG="aarch64-apple-darwin" ;;
  x86_64) SLUG="x86_64-apple-darwin" ;;
  *)
    echo "Arquitectura no compatible: $(uname -m)"
    exit 1
    ;;
esac

URL="https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.13.18%2B20261026-${SLUG}-install_only.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Descargando Python 3.13 con Tk 9…"
curl -fL --retry 3 --progress-bar -o "$TMP/python.tar.gz" "$URL"

echo "Instalando en $DEST…"
rm -rf "$DEST"
mkdir -p "$DEST"
tar -xzf "$TMP/python.tar.gz" -C "$DEST" --strip-components=1

"$DEST/bin/python3" -c "import tkinter; print('Listo: Python 3.13 con Tk', tkinter.TkVersion)"
