"""Тесты визуализации на языке D2."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from depviz import d2
from depviz.cli import EXIT_OK
from depviz.errors import DepvizError
from depviz.graph import build_graph, reverse_dependencies
from depviz.testrepo import parse_repo
from tests.test_cli import run

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class ToD2Test(unittest.TestCase):
    """Формирование текста D2."""

    def test_nodes_and_edges(self):
        """Вершины, рёбра, стиль корня и цикла."""
        repo = parse_repo("A: B\nB: A C\nC:")
        text = d2.to_d2(build_graph("A", repo.get))
        self.assertTrue(text.startswith("direction: down"))
        self.assertIn('"A": {style.fill', text)
        self.assertIn('"B" -> "C"\n', text)
        self.assertIn('"B" -> "A": {style.stroke: "#dc2626"', text)

    def test_versions(self):
        """Подписи вершин содержат версии."""
        graph = build_graph("flask", {"flask": ["click"]}.get)
        text = d2.to_d2(graph, {"flask": "3.0.0", "click": "8.1.7"})
        self.assertIn('"click": "click==8.1.7"', text)

    def test_reverse_direction(self):
        """В обратном режиме стрелка идёт от зависящего пакета."""
        graph = reverse_dependencies("C", {"A": ["B"], "B": ["C"]})
        text = d2.to_d2(graph, reverse=True)
        self.assertIn('"B" -> "C"', text)
        self.assertIn('"A" -> "B"', text)

    def test_quote(self):
        """Кавычки экранируются."""
        self.assertEqual(d2.quote('a"b'), '"a\\"b"')


class RenderTest(unittest.TestCase):
    """Вызов утилиты d2."""

    def test_no_binary(self):
        """Без d2 — понятная ошибка."""
        with mock.patch("depviz.d2.shutil.which", return_value=None):
            with self.assertRaises(DepvizError):
                d2.render("graph.d2")

    def test_render_and_show(self):
        """d2 вызывается с путями к .d2 и .svg."""
        done = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch("depviz.d2.shutil.which", return_value="/bin/d2"), \
                mock.patch("depviz.d2.subprocess.run",
                           return_value=done) as fake_run:
            image = d2.render("out/g.d2")
        self.assertEqual(image, Path("out/g.svg"))
        fake_run.assert_called_once()
        with mock.patch("depviz.d2.webbrowser.open") as fake_open:
            d2.show(image)
        self.assertTrue(fake_open.call_args[0][0].startswith("file://"))

    def test_render_error(self):
        """Ошибка d2 передаётся пользователю."""
        failed = subprocess.CompletedProcess([], 1, "", "bad syntax")
        with mock.patch("depviz.d2.shutil.which", return_value="/bin/d2"), \
                mock.patch("depviz.d2.subprocess.run", return_value=failed):
            with self.assertRaises(DepvizError) as ctx:
                d2.render("g.d2")
        self.assertIn("bad syntax", str(ctx.exception))


class CliD2Test(unittest.TestCase):
    """Опции --d2 и --show."""

    def test_save(self):
        """Файл D2 сохраняется и печатается."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "g.d2"
            code, out, _ = run(["-p", "A", "-m", "test",
                                "-r", str(EXAMPLES / "simple.txt"),
                                "--d2", str(target)])
            self.assertEqual(code, EXIT_OK)
            self.assertIn('"A" -> "B"', target.read_text())
        self.assertIn("Описание на языке D2", out)


if __name__ == "__main__":
    unittest.main()
