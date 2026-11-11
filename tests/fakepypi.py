"""Подмена сетевого доступа к PyPI для тестов."""
import io
import json
import urllib.error
from pathlib import Path
from unittest import mock

DATA = Path(__file__).parent / "data"


class FakeResponse(io.BytesIO):
    """Ответ urlopen, поддерживающий контекстный менеджер."""


def make_urlopen(packages):
    """Создаёт поддельный urlopen по словарю {url_suffix: info}."""

    def fake_urlopen(request, timeout=None):
        """Возвращает JSON для известного URL или ошибку 404."""
        url = request.full_url
        for suffix, info in packages.items():
            if url.endswith(suffix):
                body = json.dumps({"info": info}).encode("utf-8")
                return FakeResponse(body)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    return fake_urlopen


def load_info(name):
    """Читает поле info из сохранённого JSON в tests/data."""
    text = (DATA / name).read_text(encoding="utf-8")
    return json.loads(text)["info"]


def patch_pypi(packages):
    """Патчит urlopen в модуле depviz.pypi."""
    return mock.patch("depviz.pypi.urllib.request.urlopen",
                      make_urlopen(packages))
