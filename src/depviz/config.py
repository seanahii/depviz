"""Параметры приложения и их проверка."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from depviz.errors import ConfigError

MODE_REAL = "real"
MODE_TEST = "test"
MODES = (MODE_REAL, MODE_TEST)
URL_SCHEMES = ("http", "https")

REAL_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(
    r"^\d+(\.\d+)*((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?$")
FILTER_RE = re.compile(r"^\S+$")


@dataclass(frozen=True)
class Config:
    """Настраиваемые пользователем параметры."""

    package: str
    repo: str
    mode: str = MODE_REAL
    version: str | None = None
    substring: str | None = None

    @property
    def is_test(self):
        """Возвращает True, если включён режим тестового репозитория."""
        return self.mode == MODE_TEST

    def as_pairs(self):
        """Возвращает параметры в виде списка пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("mode", self.mode),
            ("version", self.version or ""),
            ("filter", self.substring or ""),
        ]


def validate_mode(mode):
    """Проверяет режим работы с репозиторием."""
    if mode not in MODES:
        raise ConfigError(
            f"неизвестный режим '{mode}', допустимо: {', '.join(MODES)}")


def validate_package(name, mode):
    """Проверяет имя пакета с учётом режима работы."""
    if not name or not name.strip():
        raise ConfigError("имя пакета не может быть пустым")
    if mode == MODE_TEST and not TEST_NAME_RE.match(name):
        raise ConfigError(
            f"в тестовом репозитории пакеты называются большими "
            f"латинскими буквами, получено '{name}'")
    if mode == MODE_REAL and not REAL_NAME_RE.match(name):
        raise ConfigError(f"недопустимое имя пакета Python '{name}'")


def validate_repo(repo, mode):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    if not repo or not repo.strip():
        raise ConfigError("не задан репозиторий (--repo)")
    if mode == MODE_TEST:
        path = Path(repo)
        if not path.is_file():
            raise ConfigError(f"файл тестового репозитория не найден: "
                              f"'{repo}'")
        return
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"некорректный URL репозитория '{repo}', ожидается "
            f"http(s)://хост/путь")


def validate_version(version, mode):
    """Проверяет версию пакета (обязательна для реального репозитория)."""
    if version is None:
        if mode == MODE_REAL:
            raise ConfigError("для реального репозитория нужна версия "
                              "пакета (--version)")
        return
    if not VERSION_RE.match(version):
        raise ConfigError(f"некорректная версия пакета '{version}', "
                          f"пример: 2.31.0")


def validate_filter(substring):
    """Проверяет подстроку фильтрации пакетов."""
    if substring is None:
        return
    if not FILTER_RE.match(substring):
        raise ConfigError("подстрока фильтра не может быть пустой "
                          "или содержать пробелы")


def make_config(package, repo, mode, version=None, substring=None):
    """Создаёт проверенный объект Config или бросает ConfigError."""
    validate_mode(mode)
    validate_package(package, mode)
    validate_repo(repo, mode)
    validate_version(version, mode)
    validate_filter(substring)
    return Config(package, repo, mode, version, substring)
