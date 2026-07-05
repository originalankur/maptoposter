#!/usr/bin/env bash
#
# Installs the City Map Poster Generator (CLI + web UI): clones the repo (or
# reuses the checkout this script lives in) and installs its Python
# dependencies with uv if available, otherwise a pip virtual environment.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/tiuchs/maptoposter/main/install.sh | bash
#   ./install.sh [-d DIR] [-s]
#
set -euo pipefail

REPO_URL="https://github.com/tiuchs/maptoposter.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
INSTALL_DIR="maptoposter"
DIR_EXPLICIT=0
SERVE_AFTER_INSTALL=0

usage() {
  cat <<'EOF'
Install the City Map Poster Generator (CLI + web UI).

Usage: install.sh [options]

Options:
  -d, --dir <path>   Directory to install into (default: ./maptoposter)
  -s, --serve        Start the web UI after installing
  -h, --help         Show this help message
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    -d|--dir)
      INSTALL_DIR="$2"
      DIR_EXPLICIT=1
      shift 2
      ;;
    -s|--serve)
      SERVE_AFTER_INSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

log() { printf '\n==> %s\n' "$1"; }

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required but was not found on PATH." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but was not found on PATH." >&2
  exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "Warning: found Python $PY_VERSION, but this project requires Python 3.11+." >&2
fi

# If this script is being run from inside an existing checkout (e.g. you
# already cloned the repo and ran ./install.sh) rather than piped via curl,
# install in place instead of cloning a nested copy.
if [ "$DIR_EXPLICIT" -eq 0 ] && [ -f "$SCRIPT_DIR/create_map_poster.py" ]; then
  INSTALL_DIR="$SCRIPT_DIR"
fi

if [ -d "$INSTALL_DIR/.git" ] && [ -f "$INSTALL_DIR/create_map_poster.py" ]; then
  log "Using existing checkout at '$INSTALL_DIR', pulling latest changes..."
  git -C "$INSTALL_DIR" pull --ff-only
elif [ -e "$INSTALL_DIR" ]; then
  echo "Error: '$INSTALL_DIR' already exists and is not a checkout of this project." >&2
  echo "Choose a different directory with --dir, or remove it first." >&2
  exit 1
else
  log "Cloning $REPO_URL into '$INSTALL_DIR'..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if command -v uv >/dev/null 2>&1; then
  log "Installing dependencies with uv..."
  uv sync --locked
  run_py() { uv run python "$@"; }
  cli_hint="uv run ./create_map_poster.py --city Paris --country France"
  serve_hint="uv run python webapp/server.py"
else
  log "uv not found; creating a virtual environment with pip instead..."
  python3 -m venv .venv
  set +u
  # shellcheck disable=SC1091
  source .venv/bin/activate
  set -u
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt
  run_py() { python "$@"; }
  cli_hint="source .venv/bin/activate && python create_map_poster.py --city Paris --country France"
  serve_hint="source .venv/bin/activate && python webapp/server.py"
fi

log "Installation complete."
echo "Location: $(pwd)"

if [ "$SERVE_AFTER_INSTALL" -eq 1 ]; then
  log "Starting the web UI at http://127.0.0.1:8000 ..."
  run_py webapp/server.py
else
  echo
  echo "Start the web UI:"
  echo "  cd '$INSTALL_DIR' && $serve_hint"
  echo
  echo "...or generate a poster from the command line:"
  echo "  cd '$INSTALL_DIR' && $cli_hint"
fi
