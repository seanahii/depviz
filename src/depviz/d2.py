"""Визуализация графа: текст на языке диаграмм D2 и показ изображения.

Изображение строится утилитой ``d2`` (https://d2lang.com) и
открывается программой просмотра по умолчанию.
"""
import shutil
import subprocess
import webbrowser
from pathlib import Path

from depviz.errors import DepvizError
from depviz.graph import node_label

ROOT_STYLE = '{style.fill: "#fde68a"; style.bold: true}'
CYCLE_STYLE = '{style.stroke: "#dc2626"; style.stroke-width: 3}'
D2_BINARY = "d2"
IMAGE_SUFFIX = ".svg"


def quote(text):
    """Заключает идентификатор D2 в кавычки с экранированием."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def drawn_edges(graph, reverse=False):
    """Возвращает рёбра (зависящий, зависимость) и рёбра циклов.

    В графе обратных зависимостей рёбра хранятся от пакета к тем,
    кто от него зависит, поэтому для рисунка они разворачиваются —
    стрелка всегда идёт от пакета к его зависимости.
    """
    edges = [(node, dep) for node, deps in graph.edges.items()
             for dep in deps]
    cycles = graph.cycle_edges()
    if reverse:
        edges = [(dst, src) for src, dst in edges]
        cycles = {(dst, src) for src, dst in cycles}
    return edges, cycles


def node_line(node, root, versions=None):
    """Возвращает объявление вершины: подпись с версией, стиль корня."""
    line = quote(node)
    label = node_label(node, versions)
    parts = [quote(label)] if label != node else []
    if node == root:
        parts.append(ROOT_STYLE)
    if parts:
        line += ": " + " ".join(parts)
    return line


def to_d2(graph, versions=None, reverse=False):
    """Формирует описание графа на языке D2."""
    lines = ["direction: down", ""]
    for node in graph.edges:
        lines.append(node_line(node, graph.root, versions))
    lines.append("")
    edges, cycles = drawn_edges(graph, reverse)
    for src, dst in edges:
        line = f"{quote(src)} -> {quote(dst)}"
        if (src, dst) in cycles:
            line += f": {CYCLE_STYLE}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def save_d2(text, path):
    """Сохраняет описание D2 в файл, создавая каталоги."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def render(d2_path):
    """Строит SVG по файлу D2 утилитой d2 и возвращает путь к SVG."""
    binary = shutil.which(D2_BINARY)
    if binary is None:
        raise DepvizError("утилита d2 не найдена. Установите её: "
                          "'brew install d2' (macOS) или "
                          "'curl -fsSL https://d2lang.com/install.sh | sh'")
    image = Path(d2_path).with_suffix(IMAGE_SUFFIX)
    result = subprocess.run([binary, str(d2_path), str(image)],
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise DepvizError(f"d2 завершилась с ошибкой: "
                          f"{result.stderr.strip()}")
    return image


def show(image):
    """Открывает изображение в программе просмотра по умолчанию."""
    webbrowser.open(Path(image).resolve().as_uri())
