"""Тесты построения графа зависимостей."""
import unittest
from pathlib import Path

from depviz.graph import build_graph, format_graph, make_filter
from depviz.testrepo import RepoFileError, load_repo, parse_repo

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def graph_of(text, root="A", substring=None):
    """Строит граф по тексту тестового репозитория."""
    repo = parse_repo(text)
    return build_graph(root, lambda n: repo.get(n, []),
                       make_filter(substring))


class ParseRepoTest(unittest.TestCase):
    """Разбор файла тестового репозитория."""

    def test_parse(self):
        """Строки, комментарии и разделители."""
        repo = parse_repo("# c\nA: B, C\n\nB:\n")
        self.assertEqual(repo, {"A": ["B", "C"], "B": []})

    def test_bad_name(self):
        """Имя не из больших букв — ошибка с номером строки."""
        with self.assertRaises(RepoFileError) as ctx:
            load_repo(EXAMPLES / "bad.txt")
        self.assertIn("строка 2", str(ctx.exception))

    def test_no_colon(self):
        """Строка без двоеточия — ошибка."""
        with self.assertRaises(RepoFileError):
            parse_repo("A B")

    def test_duplicate(self):
        """Повторное описание пакета — ошибка."""
        with self.assertRaises(RepoFileError):
            parse_repo("A: B\nA: C")


class BuildGraphTest(unittest.TestCase):
    """Обход в глубину, фильтр и циклы."""

    def test_diamond(self):
        """Общая зависимость обходится один раз, порядок — DFS."""
        repo = load_repo(EXAMPLES / "simple.txt")
        graph = build_graph("A", repo.get)
        self.assertEqual(list(graph.edges), ["A", "B", "D", "F", "C", "E"])
        self.assertEqual(graph.cycles, [])
        self.assertEqual(graph.edge_count, 6)

    def test_cycles(self):
        """Цикл через несколько пакетов и петля."""
        graph = graph_of((EXAMPLES / "cycle.txt").read_text())
        self.assertEqual(graph.cycles,
                         [["A", "B", "C", "A"], ["E", "E"]])
        self.assertIn(("C", "A"), graph.cycle_edges())

    def test_filter(self):
        """Пакеты с подстрокой в имени не учитываются."""
        graph = graph_of("A: B C\nB: D\nC: D\nD:", substring="B")
        self.assertEqual(graph.edges, {"A": ["C"], "C": ["D"], "D": []})

    def test_filter_breaks_cycle(self):
        """Исключение пакета разрывает цикл."""
        graph = graph_of("A: B\nB: C\nC: A", substring="c")
        self.assertEqual(graph.cycles, [])
        self.assertEqual(list(graph.edges), ["A", "B"])

    def test_deep_chain(self):
        """Длинная цепочка не упирается в предел рекурсии."""
        size = 5000
        chain = {f"N{i}": [f"N{i + 1}"] for i in range(size)}
        graph = build_graph("N0", lambda n: chain.get(n, []))
        self.assertEqual(len(graph.edges), size + 1)

    def test_format(self):
        """Текстовый вывод содержит связи и циклы."""
        text = format_graph(graph_of("A: B\nB: A"))
        self.assertIn("A -> B", text)
        self.assertIn("Циклические зависимости", text)


if __name__ == "__main__":
    unittest.main()
