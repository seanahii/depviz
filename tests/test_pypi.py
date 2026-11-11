"""Тесты получения зависимостей из PyPI."""
import unittest

from depviz.pypi import (RepoError, Requirement, direct_requirements,
                         normalize_name, parse_requirement, release_url)
from tests.fakepypi import load_info, patch_pypi

PYPI = "https://pypi.org/pypi"


class ParseTest(unittest.TestCase):
    """Разбор строк requires_dist."""

    def test_normalize(self):
        """Имена нормализуются по PEP 503."""
        self.assertEqual(normalize_name("Foo_Bar.baz"), "foo-bar-baz")

    def test_old_style(self):
        """Ограничение версии в скобках."""
        req = parse_requirement("idna (<4,>=2.5)")
        self.assertEqual(req, Requirement("idna", "<4,>=2.5"))

    def test_new_style_with_marker(self):
        """Ограничение без скобок и маркер окружения."""
        req = parse_requirement(
            'importlib-metadata>=3.6.0; python_version < "3.10"')
        self.assertEqual(req.name, "importlib-metadata")
        self.assertEqual(req.specifier, ">=3.6.0")
        self.assertEqual(req.marker, 'python_version < "3.10"')

    def test_extras_in_name(self):
        """Дополнительные группы в имени отбрасываются."""
        req = parse_requirement("urllib3[socks]>=1.26")
        self.assertEqual(req, Requirement("urllib3", ">=1.26"))

    def test_extra_marker_skipped(self):
        """Необязательные зависимости (extra) не учитываются."""
        self.assertIsNone(
            parse_requirement("PySocks (>=1.5.6) ; extra == 'socks'"))

    def test_bad_requirement(self):
        """Неразбираемая строка вызывает RepoError."""
        with self.assertRaises(RepoError):
            parse_requirement("!!!")

    def test_release_url(self):
        """URL с версией и без неё."""
        self.assertEqual(release_url(PYPI + "/", "flask", "3.0.0"),
                         PYPI + "/flask/3.0.0/json")
        self.assertEqual(release_url(PYPI, "flask"), PYPI + "/flask/json")


class FetchTest(unittest.TestCase):
    """Загрузка метаданных с подменой сети."""

    def test_requests(self):
        """Прямые зависимости requests 2.31.0."""
        info = load_info("requests-2.31.0.json")
        with patch_pypi({"/requests/2.31.0/json": info}):
            version, reqs = direct_requirements(PYPI, "requests", "2.31.0")
        self.assertEqual(version, "2.31.0")
        self.assertEqual([r.name for r in reqs],
                         ["charset-normalizer", "idna", "urllib3",
                          "certifi"])

    def test_not_found(self):
        """Неизвестная версия даёт понятную ошибку."""
        with patch_pypi({}), self.assertRaises(RepoError) as ctx:
            direct_requirements(PYPI, "requests", "0.0.0")
        self.assertIn("не найдено", str(ctx.exception))

    def test_no_requires(self):
        """Пакет без зависимостей (requires_dist = null)."""
        info = {"version": "1.0", "requires_dist": None}
        with patch_pypi({"/six/1.0/json": info}):
            _, reqs = direct_requirements(PYPI, "six", "1.0")
        self.assertEqual(reqs, [])


if __name__ == "__main__":
    unittest.main()
