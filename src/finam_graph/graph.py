"""Helpers for graph analysis"""
from finam import Composition
from finam.interfaces import IAdapter, IInput, IOutput


class Graph:
    """Container for graph data"""

    def __init__(self, comp: Composition, excluded: set):
        self.components, self.adapters, self.edges, self.direct_edges = _get_graph(comp, excluded)

        self.simple_edges = set()
        for edge in self.direct_edges:
            self.simple_edges.add((edge.source, edge.target))


def _get_graph(composition, excluded):
    components, adapters, direct_edges = _get_graph_nodes(composition, excluded)

    edges = _get_component_edges(components)
    edges = edges.union(_get_adapter_edges(adapters))

    return components, adapters, edges, direct_edges


def _get_component_edges(components):
    edges = set()

    for comp in components:
        for i, (n, inp) in enumerate(comp.inputs.items()):
            src = inp.get_source()
            if isinstance(src, IAdapter):
                edges.add(Edge(src, None, 0, comp, n, i, 0))
                continue
            for comp2 in components:
                for ii, (nm, out) in enumerate(comp2.outputs.items()):
                    if out == src:
                        edges.add(Edge(comp2, nm, ii, comp, n, i, 0))
                        break

        for i, (n, out) in enumerate(comp.outputs.items()):
            for trg in out.get_targets():
                if isinstance(trg, IAdapter):
                    edges.add(Edge(comp, n, i, trg, None, 0, 0))

    return edges


def _get_adapter_edges(adapters):
    edges = set()

    for ad in adapters:
        src = ad.get_source()
        if isinstance(src, IAdapter):
            edges.add(Edge(src, None, 0, ad, None, 0, 0))
        for trg in ad.get_targets():
            if isinstance(trg, IAdapter):
                edges.add(Edge(ad, None, 0, trg, None, 0, 0))

    return edges


def _get_graph_nodes(composition, excluded):
    components = set()
    adapters = set()
    direct_edges = set()

    for comp in composition.modules:
        if comp in excluded:
            continue

        components.add(comp)
        for i, (n, inp) in enumerate(comp.inputs.items()):
            out, depth = _trace_input(inp, adapters)
            if out is None:
                continue
            for comp2 in composition.modules:
                if comp2 in excluded:
                    continue
                for ii, (nm, src) in enumerate(comp2.outputs.items()):
                    if out == src:
                        direct_edges.add(Edge(comp2, nm, ii, comp, n, i, depth))
                        break

        for _n, out in comp.outputs.items():
            _trace_output(out, adapters)

    return components, adapters, direct_edges


def _trace_input(inp: IInput, out_adapters: set, depth=0):
    src = inp.get_source()
    if src is None:
        return None, depth

    if isinstance(src, IAdapter):
        out_adapters.add(src)
        return _trace_input(src, out_adapters, depth + 1)

    return src, depth


def _trace_output(out: IOutput, out_adapters: set):
    for trg in out.get_targets():
        if isinstance(trg, IAdapter):
            out_adapters.add(trg)
            _trace_output(trg, out_adapters)


class Edge:
    """Representation of a graph edge"""

    def __init__(
        self, source, out_name, out_index, target, in_name, in_index, num_adapters
    ):
        self.source = source
        self.out_name = out_name
        self.out_index = out_index
        self.target = target
        self.in_name = in_name
        self.in_index = in_index
        self.num_adapters = num_adapters

    def __hash__(self):
        return hash((self.source, self.out_name, self.target, self.in_name))

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.source == other.source
            and self.out_name == other.out_name
            and self.out_index == other.out_index
            and self.target == other.target
            and self.in_name == other.in_name
            and self.in_index == other.in_index
            and self.num_adapters == other.num_adapters
        )

    def __repr__(self):
        return (
            f"{self.source.__class__.__name__}[{self.out_name or '-'}] -> "
            f"{self.target.__class__.__name__}[{self.in_name or '-'}]"
        )
