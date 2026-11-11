"""Получение зависимостей пакетов из репозитория PyPI (JSON API).

Используется только стандартная библиотека: метаданные пакета
запрашиваются по адресу ``<repo>/<name>/<version>/json`` и из поля
``info.requires_dist`` извлекаются требования формата PEP 508.
"""
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from depviz.errors import DepvizError

TIMEOUT_SECONDS = 20
HTTP_NOT_FOUND = 404
USER_AGENT = "depviz/0.1 (study project)"

NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXTRAS_RE = re.compile(r"^\s*\[[^\]]*\]")
EXTRA_MARKER_RE = re.compile(r"\bextra\s*==")
NORMALIZE_RE = re.compile(r"[-_.]+")


class RepoError(DepvizError):
    """Ошибка получения данных из репозитория."""


@dataclass(frozen=True)
class Requirement:
    """Одна зависимость пакета: имя, ограничение версии и маркер."""

    name: str
    specifier: str = ""
    marker: str = ""

    def __str__(self):
        """Возвращает требование в читаемом виде."""
        text = self.name
        if self.specifier:
            text += f" ({self.specifier})"
        if self.marker:
            text += f"; {self.marker}"
        return text


def normalize_name(name):
    """Нормализует имя пакета по PEP 503 (нижний регистр, дефисы)."""
    return NORMALIZE_RE.sub("-", name).lower()


def parse_requirement(spec):
    """Разбирает строку requires_dist.

    Возвращает Requirement или None, если зависимость относится
    к дополнительной группе (``extra == ...``) и не ставится по умолчанию.
    """
    requirement, _, marker = spec.partition(";")
    marker = marker.strip()
    if EXTRA_MARKER_RE.search(marker):
        return None
    match = NAME_RE.match(requirement)
    if not match:
        raise RepoError(f"не удалось разобрать требование '{spec}'")
    rest = EXTRAS_RE.sub("", requirement[match.end():]).strip()
    rest = rest.strip("()").strip()
    return Requirement(normalize_name(match.group(1)), rest, marker)


def release_url(repo, name, version=None):
    """Строит URL метаданных пакета (версия None — последняя)."""
    base = repo.rstrip("/")
    if version is None:
        return f"{base}/{name}/json"
    return f"{base}/{name}/{version}/json"


def fetch_json(url):
    """Загружает и декодирует JSON по URL."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT,
                      "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepoError(f"не найдено в репозитории: {url}") from error
        raise RepoError(f"HTTP {error.code} при запросе {url}") from error
    except urllib.error.URLError as error:
        raise RepoError(f"нет доступа к {url}: {error.reason}") from error
    except (ValueError, UnicodeDecodeError) as error:
        raise RepoError(f"некорректный JSON по адресу {url}") from error


def direct_requirements(repo, name, version=None):
    """Возвращает (версия, список Requirement) прямых зависимостей."""
    data = fetch_json(release_url(repo, name, version))
    info = data.get("info") or {}
    result = []
    for spec in info.get("requires_dist") or []:
        requirement = parse_requirement(spec)
        if requirement is not None and requirement not in result:
            result.append(requirement)
    return info.get("version", version), result
