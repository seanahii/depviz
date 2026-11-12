"""Тесты проверки параметров."""
import unittest
from pathlib import Path

from depviz.config import make_config
from depviz.errors import ConfigError

PYPI = "https://pypi.org/pypi"
REPO_FILE = (Path(__file__).resolve().parent.parent / "examples"
             / "simple.txt")


class RealModeTest(unittest.TestCase):
    """Проверка параметров для реального репозитория."""

    def test_valid(self):
        """Корректные параметры принимаются."""
        cfg = make_config("requests", PYPI, "real", "2.31.0", "test")
        self.assertEqual(cfg.package, "requests")
        self.assertFalse(cfg.is_test)

    def test_bad_mode(self):
        """Неизвестный режим отклоняется."""
        with self.assertRaises(ConfigError):
            make_config("requests", PYPI, "fake", "1.0")

    def test_empty_package(self):
        """Пустое имя пакета отклоняется."""
        with self.assertRaises(ConfigError):
            make_config("  ", PYPI, "real", "1.0")

    def test_bad_package(self):
        """Имя с недопустимыми символами отклоняется."""
        with self.assertRaises(ConfigError):
            make_config("req uests!", PYPI, "real", "1.0")

    def test_bad_url(self):
        """URL без схемы http(s) отклоняется."""
        for url in ("pypi.org", "ftp://pypi.org", "http://", ""):
            with self.subTest(url=url), self.assertRaises(ConfigError):
                make_config("requests", url, "real", "1.0")

    def test_missing_version(self):
        """Без версии реальный режим не работает."""
        with self.assertRaises(ConfigError):
            make_config("requests", PYPI, "real")

    def test_bad_version(self):
        """Некорректная версия отклоняется."""
        for version in ("abc", "1..2", "v1.0", ""):
            with self.subTest(v=version), self.assertRaises(ConfigError):
                make_config("requests", PYPI, "real", version)

    def test_good_versions(self):
        """Варианты версий по PEP 440 принимаются."""
        for version in ("1", "2.31.0", "1.0rc1", "1.0.post2", "2.0.dev3"):
            with self.subTest(v=version):
                make_config("requests", PYPI, "real", version)

    def test_bad_filter(self):
        """Пустая подстрока или подстрока с пробелами отклоняется."""
        for value in ("", " ", "a b"):
            with self.subTest(f=value), self.assertRaises(ConfigError):
                make_config("requests", PYPI, "real", "1.0", value)


class RepoFileModeTest(unittest.TestCase):
    """Проверка параметров для тестового репозитория."""

    path = REPO_FILE

    def test_valid(self):
        """Корректные параметры принимаются, версия не обязательна."""
        cfg = make_config("A", str(self.path), "test")
        self.assertTrue(cfg.is_test)

    def test_lowercase_name(self):
        """Имена тестовых пакетов — только большие латинские буквы."""
        with self.assertRaises(ConfigError):
            make_config("a", str(self.path), "test")

    def test_missing_file(self):
        """Несуществующий файл отклоняется."""
        with self.assertRaises(ConfigError):
            make_config("A", str(self.path) + ".nope", "test")


if __name__ == "__main__":
    unittest.main()
