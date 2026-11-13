#!/bin/zsh
# Abre el calendario con el Python moderno (Tk 9) incluido para esta app.
cd "$(dirname "$0")" || exit 1

PYTHON="$HOME/.local/share/calendario-python/bin/python3"

if [[ ! -x "$PYTHON" ]]; then
  echo "Preparando Python moderno (solo la primera vez)…"
  if ! ./instalar-python.sh; then
    echo
    echo "No se pudo instalar Python. Revisa tu conexión a internet."
    read -r "?Pulsa Enter para cerrar..."
    exit 1
  fi
fi

exec "$PYTHON" calendario.py
