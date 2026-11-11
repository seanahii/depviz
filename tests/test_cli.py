"""Тесты интерфейса командной строки."""
import contextlib
import io
import unittest
from pathlib import Path

from depviz.cli import EXIT_ERROR, EXIT_OK, main
from tests.fakepypi import load_info, patch_pypi

PYPI = "https://pypi.org/pypi"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
LEAVES = {"charset-normalizer": "3.3.2", "idna": "3.6",
          "urllib3": "2.0.7", "certifi": "2023.11.17"}


def fake_packages():
    """Поддельный PyPI: requests 2.31.0 и его зависимости-листья."""
    packages = {"/requests/2.31.0/json": load_info("requests-2.31.0.json")}
    for name, version in LEAVES.items():
        packages[f"/{name}/json"] = {"version": version,
                                     "requires_dist": None}
    return packages


def run_requests(extra):
    """Запускает анализ requests 2.31.0 на поддельном PyPI."""
    with patch_pypi(fake_packages()):
        return run(["-p", "requests", "-r", PYPI, "-v", "2.31.0", *extra])


def run(argv):
    """Запускает main и возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Проверка запуска приложения."""

    def test_real_graph(self):
        """Граф строится для заданной версии, extra не учитываются."""
        code, out, _ = run_requests(["-f", "idna"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("requests==2.31.0 -> charset-normalizer, "
                      "urllib3, certifi", out)
        self.assertIn("urllib3==2.0.7 -> (нет)", out)
        self.assertNotIn("pysocks", out)
        self.assertNotIn("idna", out)

    def test_test_repo(self):
        """Граф тестового репозитория с циклом."""
        code, out, _ = run(["-p", "A", "-r", str(EXAMPLES / "cycle.txt"),
                            "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("A -> B -> C -> A", out)

    def test_root_filtered(self):
        """Фильтр, исключающий корневой пакет, — ошибка."""
        code, _, err = run(["-p", "A", "-r", str(EXAMPLES / "cycle.txt"),
                            "-m", "test", "-f", "A"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("исключён фильтром", err)

    def test_error_message(self):
        """Ошибка параметра выводится в stderr с кодом 1."""
        code, _, err = run(["-p", "requests", "-r", "pypi.org",
                            "-v", "1.0"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)


if __name__ == "__main__":
    unittest.main()
