"""Построение графа зависимостей обходом в глубину без рекурсии."""
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Граф зависимостей, достижимых из корневого пакета.

    ``edges`` — словарь смежности в порядке обнаружения вершин,
    ``cycles`` — найденные циклы в виде списков вершин, где последняя
    вершина совпадает с первой.
    """

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)

    @property
    def edge_count(self):
        """Количество рёбер графа."""
        return sum(len(deps) for deps in self.edges.values())

    def cycle_edges(self):
        """Множество рёбер (откуда, куда), входящих в найденные циклы."""
        result = set()
        for cycle in self.cycles:
            result.update(zip(cycle, cycle[1:]))
        return result


def make_filter(substring):
    """Создаёт предикат: True, если пакет нужно исключить."""
    if not substring:
        return lambda name: False
    needle = substring.lower()
    return lambda name: needle in name.lower()


def build_graph(root, get_deps, is_excluded=None):
    """Строит граф обходом в глубину на явном стеке.

    ``get_deps(name)`` возвращает прямые зависимости пакета,
    ``is_excluded(name)`` — True для пакетов, которые не учитываются.
    Стек хранит итераторы по зависимостям вершин текущего пути, поэтому
    рекурсия не нужна. Ребро в вершину текущего пути — цикл: он
    сохраняется, а повторный вход в вершину не выполняется.
    """
    excluded = is_excluded or make_filter(None)
    graph = DependencyGraph(root)
    path, on_path, done, stack = [], set(), set(), []

    def enter(node):
        """Добавляет вершину на путь и в стек обхода."""
        deps = [dep for dep in get_deps(node) or [] if not excluded(dep)]
        graph.edges[node] = deps
        path.append(node)
        on_path.add(node)
        stack.append(iter(deps))

    enter(root)
    while stack:
        child = next(stack[-1], None)
        if child is None:
            stack.pop()
            node = path.pop()
            on_path.discard(node)
            done.add(node)
        elif child in on_path:
            graph.cycles.append(path[path.index(child):] + [child])
        elif child not in done:
            enter(child)
    return graph


def node_label(name, versions=None):
    """Возвращает подпись вершины: имя и, если известна, версия."""
    version = (versions or {}).get(name)
    return f"{name}=={version}" if version else name


def format_graph(graph, versions=None):
    """Возвращает текстовое представление графа и найденных циклов."""
    root = node_label(graph.root, versions)
    lines = [f"Граф зависимостей {root} (пакетов: "
             f"{len(graph.edges)}, связей: {graph.edge_count}):"]
    for node, deps in graph.edges.items():
        lines.append(f"  {node_label(node, versions)} -> "
                     f"{', '.join(deps) or '(нет)'}")
    if graph.cycles:
        lines.append("Циклические зависимости:")
        lines.extend(f"  {' -> '.join(cycle)}" for cycle in graph.cycles)
    return "\n".join(lines)


def invert(edges):
    """Обращает словарь смежности: для каждого пакета — кто от него
    зависит."""
    reverse = {node: [] for node in edges}
    for node, deps in edges.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(node)
    return reverse


def reverse_dependencies(target, edges, is_excluded=None):
    """Строит граф обратных зависимостей пакета ``target``.

    Используется тот же обход в глубину без рекурсии (``build_graph``),
    но по обращённому графу: вершины результата — пакеты, которые прямо
    или транзитивно зависят от ``target``.
    """
    reverse = invert(edges)
    return build_graph(target, lambda name: reverse.get(name, []),
                       is_excluded)


def format_reverse(graph):
    """Возвращает текстовое представление обратных зависимостей."""
    dependents = [node for node in graph.edges if node != graph.root]
    lines = [f"Обратные зависимости {graph.root} "
             f"(пакетов, зависящих от него: {len(dependents)}):",
             f"  {', '.join(dependents) or '(нет)'}",
             "Связи (X <- Y: Y зависит от X):"]
    for node, users in graph.edges.items():
        lines.append(f"  {node} <- {', '.join(users) or '(нет)'}")
    if graph.cycles:
        lines.append("Циклические зависимости:")
        lines.extend(f"  {' <- '.join(cycle)}" for cycle in graph.cycles)
    return "\n".join(lines)
