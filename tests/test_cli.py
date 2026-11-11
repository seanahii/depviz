"""Тесты интерфейса командной строки."""
import contextlib
import io
import unittest

from depviz.cli import EXIT_ERROR, EXIT_OK, main
from tests.fakepypi import load_info, patch_pypi

PYPI = "https://pypi.org/pypi"


def run(argv):
    """Запускает main и возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Проверка запуска приложения."""

    def test_direct_dependencies(self):
        """Выводятся прямые зависимости заданной версии."""
        info = load_info("requests-2.31.0.json")
        with patch_pypi({"/requests/2.31.0/json": info}):
            code, out, _ = run(["-p", "requests", "-r", PYPI,
                                "-v", "2.31.0"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("requests==2.31.0", out)
        self.assertIn("urllib3 (<3,>=1.21.1)", out)
        self.assertNotIn("PySocks", out)

    def test_error_message(self):
        """Ошибка параметра выводится в stderr с кодом 1."""
        code, _, err = run(["-p", "requests", "-r", "pypi.org",
                            "-v", "1.0"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)


if __name__ == "__main__":
    unittest.main()
