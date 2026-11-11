"""Тестовый репозиторий: описание графа пакетов в текстовом файле.

Формат файла — по одной строке на пакет::

    # комментарий
    A: B C
    B: D
    D:

Слева от двоеточия — имя пакета, справа — его прямые зависимости
через пробел или запятую. Имена — большие латинские буквы.
"""
import re
from pathlib import Path

from depviz.errors import DepvizError

NAME_RE = re.compile(r"^[A-Z]+$")
SEPARATOR_RE = re.compile(r"[\s,]+")
COMMENT_PREFIX = "#"


class RepoFileError(DepvizError):
    """Ошибка в файле тестового репозитория."""


def check_name(name, line_no):
    """Проверяет имя пакета тестового репозитория."""
    if not NAME_RE.match(name):
        raise RepoFileError(
            f"строка {line_no}: имя пакета '{name}' должно состоять "
            f"из больших латинских букв")


def parse_line(line, line_no):
    """Разбирает строку 'A: B C' в пару (A, [B, C])."""
    name, colon, rest = line.partition(":")
    if not colon:
        raise RepoFileError(f"строка {line_no}: ожидается 'ПАКЕТ: "
                            f"ЗАВИСИМОСТИ', получено '{line}'")
    name = name.strip()
    check_name(name, line_no)
    deps = [dep for dep in SEPARATOR_RE.split(rest.strip()) if dep]
    for dep in deps:
        check_name(dep, line_no)
    return name, list(dict.fromkeys(deps))


def parse_repo(text):
    """Разбирает текст тестового репозитория в словарь смежности."""
    graph = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        name, deps = parse_line(line, line_no)
        if name in graph:
            raise RepoFileError(f"строка {line_no}: пакет '{name}' "
                                f"описан повторно")
        graph[name] = deps
    return graph


def load_repo(path):
    """Читает файл тестового репозитория."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise RepoFileError(f"не удалось прочитать '{path}': "
                            f"{error.strerror}") from error
    return parse_repo(text)
