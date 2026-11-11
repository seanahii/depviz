"""Тесты интерфейса командной строки."""
import contextlib
import io
import unittest

from depviz.cli import EXIT_ERROR, EXIT_OK, main

PYPI = "https://pypi.org/pypi"


def run(argv):
    """Запускает main и возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Проверка запуска приложения."""

    def test_print_params(self):
        """Параметры выводятся в формате ключ=значение."""
        code, out, _ = run(["-p", "requests", "-r", PYPI, "-v", "2.31.0",
                            "-f", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("package=requests", out)
        self.assertIn("version=2.31.0", out)
        self.assertIn("filter=test", out)

    def test_error_message(self):
        """Ошибка параметра выводится в stderr с кодом 1."""
        code, _, err = run(["-p", "requests", "-r", "pypi.org",
                            "-v", "1.0"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)


if __name__ == "__main__":
    unittest.main()
