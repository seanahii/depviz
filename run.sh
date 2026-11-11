#!/usr/bin/env sh
# Запуск depviz без установки: ./run.sh -p ПАКЕТ -r РЕПОЗИТОРИЙ ...
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m depviz "$@"
