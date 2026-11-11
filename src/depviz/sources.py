"""Источники зависимостей: реальный PyPI и тестовый репозиторий."""
import sys

from depviz.errors import DepvizError
from depviz.pypi import direct_requirements, normalize_name
from depviz.testrepo import load_repo


class PyPISource:
    """Зависимости из PyPI.

    Для корневого пакета берётся заданная пользователем версия, для
    транзитивных зависимостей — последняя версия из репозитория.
    Результаты запросов кэшируются.
    """

    def __init__(self, repo, root, version):
        """Запоминает адрес репозитория и версию корневого пакета."""
        self.repo = repo
        self.root = normalize_name(root)
        self.root_version = version
        self.versions = {}
        self.missing = []
        self._cache = {}

    def dependencies(self, name):
        """Возвращает список имён прямых зависимостей пакета."""
        if name not in self._cache:
            self._cache[name] = self._fetch(name)
        return self._cache[name]

    def _fetch(self, name):
        """Загружает зависимости; ошибка корня прерывает работу."""
        version = self.root_version if name == self.root else None
        try:
            found, requirements = direct_requirements(self.repo, name,
                                                      version)
        except DepvizError as error:
            if name == self.root:
                raise
            print(f"Предупреждение: {error}", file=sys.stderr)
            self.missing.append(name)
            return []
        self.versions[name] = found
        return list(dict.fromkeys(req.name for req in requirements))


class FileRepoSource:
    """Зависимости из файла тестового репозитория."""

    def __init__(self, path):
        """Загружает граф из файла."""
        self.graph = load_repo(path)
        self.versions = {}
        self.missing = []

    def dependencies(self, name):
        """Возвращает зависимости; неописанный пакет считается листом."""
        if name not in self.graph and name not in self.missing:
            self.missing.append(name)
        return self.graph.get(name, [])


def make_source(config):
    """Создаёт источник зависимостей по конфигурации."""
    if config.is_test:
        return FileRepoSource(config.repo)
    return PyPISource(config.repo, config.package, config.version)


def root_name(config):
    """Возвращает имя корневого пакета в форме, принятой источником."""
    if config.is_test:
        return config.package
    return normalize_name(config.package)
