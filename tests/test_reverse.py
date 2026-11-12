"""Тесты обратных зависимостей."""
import unittest
from pathlib import Path

from depviz.graph import format_reverse, invert, make_filter
from depviz.graph import reverse_dependencies
from depviz.testrepo import load_repo
from depviz.cli import EXIT_ERROR, EXIT_OK
from tests.test_cli import run

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
SIMPLE = load_repo(EXAMPLES / "simple.txt")


class ReverseTest(unittest.TestCase):
    """Поиск пакетов, зависящих от данного."""

    def test_invert(self):
        """Обращение графа."""
        self.assertEqual(invert({"A": ["B"], "B": []}),
                         {"A": [], "B": ["A"]})

    def test_transitive(self):
        """От F зависят D напрямую и B, C, A транзитивно."""
        graph = reverse_dependencies("F", SIMPLE)
        self.assertEqual(set(graph.edges) - {"F"}, {"D", "B", "C", "A"})
        self.assertEqual(graph.edges["D"], ["B", "C"])

    def test_root_package(self):
        """От корневого пакета никто не зависит."""
        graph = reverse_dependencies("A", SIMPLE)
        self.assertEqual(graph.edges, {"A": []})
        self.assertIn("(нет)", format_reverse(graph))

    def test_filter(self):
        """Отфильтрованные пакеты не учитываются."""
        graph = reverse_dependencies("D", SIMPLE, make_filter("C"))
        self.assertEqual(list(graph.edges), ["D", "B", "A"])

    def test_cycle(self):
        """Цикл в обратном графе обнаруживается."""
        repo = load_repo(EXAMPLES / "cycle.txt")
        graph = reverse_dependencies("A", repo)
        self.assertEqual(graph.cycles, [["A", "C", "B", "A"]])


class ReverseCliTest(unittest.TestCase):
    """Запуск режима --reverse."""

    def test_cli(self):
        """Вывод обратных зависимостей."""
        code, out, _ = run(["-p", "E", "-r", str(EXAMPLES / "simple.txt"),
                            "-m", "test", "--reverse"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("E <- C", out)

    def test_unknown(self):
        """Неизвестный пакет — ошибка."""
        code, _, err = run(["-p", "Q", "-r", str(EXAMPLES / "simple.txt"),
                            "-m", "test", "--reverse"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не найден", err)

    def test_real_mode(self):
        """В режиме real обратные зависимости не поддерживаются."""
        code, _, err = run(["-p", "requests", "-r", "https://pypi.org/pypi",
                            "-v", "2.31.0", "--reverse"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("только в режиме test", err)


if __name__ == "__main__":
    unittest.main()
