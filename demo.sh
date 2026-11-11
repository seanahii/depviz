#!/usr/bin/env sh
# Демонстрация этапа 5: графы трёх реальных пакетов и тестовых репозиториев.
# Нужны доступ к pypi.org и утилита d2 (brew install d2).
set -e
cd "$(dirname "$0")"
./run.sh -p requests -v 2.31.0 -r https://pypi.org/pypi --d2 out/requests.d2 --show
./run.sh -p flask -v 3.0.0 -r https://pypi.org/pypi --d2 out/flask.d2 --show
./run.sh -p pandas -v 2.1.4 -r https://pypi.org/pypi --d2 out/pandas.d2 --show
./run.sh -p A -r examples/big.txt -m test --d2 out/big.d2 --show
./run.sh -p A -r examples/cycle.txt -m test --d2 out/cycle.d2 --show
./run.sh -p L -r examples/big.txt -m test --reverse --d2 out/big-reverse.d2 --show
