"""Интерфейс командной строки."""
import argparse
import sys

from depviz import d2
from depviz.config import MODE_REAL, make_config
from depviz.errors import DepvizError
from depviz.graph import (build_graph, format_graph, format_reverse,
                          make_filter, reverse_dependencies)
from depviz.sources import make_source, root_name

EXIT_OK = 0
EXIT_ERROR = 1
DEFAULT_OUT_DIR = "out"


def build_parser():
    """Создаёт парсер опций командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализатор графа зависимостей пакетов Python.")
    parser.add_argument("-p", "--package", required=True,
                        help="имя анализируемого пакета")
    parser.add_argument("-r", "--repo", required=True,
                        help="URL репозитория или путь к тестовому файлу")
    parser.add_argument("-m", "--mode", default=MODE_REAL,
                        help="режим репозитория: real или test")
    parser.add_argument("-v", "--version", dest="pkg_version",
                        metavar="VERSION",
                        help="версия пакета, например 2.31.0")
    parser.add_argument("-f", "--filter", dest="substring",
                        metavar="SUBSTRING",
                        help="исключить пакеты, имя которых содержит "
                             "подстроку")
    parser.add_argument("--reverse", action="store_true",
                        help="вывести обратные зависимости пакета "
                             "(только для режима test)")
    parser.add_argument("--d2", metavar="FILE",
                        help="сохранить граф на языке D2 в файл")
    parser.add_argument("--show", action="store_true",
                        help="построить изображение графа (SVG) и "
                             "открыть его")
    return parser


def config_from_args(args):
    """Преобразует разобранные аргументы в проверенный Config."""
    return make_config(args.package, args.repo, args.mode,
                       args.pkg_version, args.substring)


def analyze(config):
    """Строит граф зависимостей корневого пакета с учётом фильтра."""
    excluded = make_filter(config.substring)
    root = root_name(config)
    if excluded(root):
        raise DepvizError(f"корневой пакет '{root}' исключён фильтром "
                          f"'{config.substring}'")
    source = make_source(config)
    graph = build_graph(root, source.dependencies, excluded)
    return graph, source


def analyze_reverse(config):
    """Строит граф обратных зависимостей в тестовом репозитории."""
    if not config.is_test:
        raise DepvizError("обратные зависимости поддерживаются только в "
                          "режиме test: PyPI не предоставляет список "
                          "пакетов, зависящих от данного")
    excluded = make_filter(config.substring)
    if excluded(config.package):
        raise DepvizError(f"пакет '{config.package}' исключён фильтром")
    edges = make_source(config).graph
    known = set(edges).union(*edges.values())
    if config.package not in known:
        raise DepvizError(f"пакет '{config.package}' не найден в "
                          f"тестовом репозитории")
    return reverse_dependencies(config.package, edges, excluded)


def run_forward(config):
    """Строит и выводит граф прямых зависимостей."""
    graph, source = analyze(config)
    print(format_graph(graph, source.versions))
    report_missing(source)
    return graph, source.versions


def run_reverse(config):
    """Строит и выводит граф обратных зависимостей."""
    graph = analyze_reverse(config)
    print(format_reverse(graph))
    return graph, {}


def visualize(graph, versions, args):
    """Сохраняет граф в формате D2 и при необходимости показывает его."""
    text = d2.to_d2(graph, versions, args.reverse)
    default = f"{DEFAULT_OUT_DIR}/{graph.root}.d2"
    path = d2.save_d2(text, args.d2 or default)
    print(f"\nОписание на языке D2 ({path}):\n{text}", end="")
    if args.show:
        image = d2.render(path)
        print(f"Изображение графа: {image}")
        d2.show(image)


def report_missing(source):
    """Сообщает о пакетах, для которых не найдено описание."""
    if source.missing:
        print("Не найдены в репозитории (считаются без зависимостей): "
              + ", ".join(source.missing))


def main(argv=None):
    """Запускает приложение и возвращает код завершения."""
    args = build_parser().parse_args(argv)
    try:
        config = config_from_args(args)
        runner = run_reverse if args.reverse else run_forward
        graph, versions = runner(config)
        if args.d2 or args.show:
            visualize(graph, versions, args)
    except DepvizError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
