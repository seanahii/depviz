"""Интерфейс командной строки."""
import argparse
import sys

from depviz.config import MODE_REAL, make_config
from depviz.errors import DepvizError
from depviz.graph import build_graph, format_graph, make_filter
from depviz.sources import make_source, root_name

EXIT_OK = 0
EXIT_ERROR = 1


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
        graph, source = analyze(config)
        print(format_graph(graph, source.versions))
        report_missing(source)
    except DepvizError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
