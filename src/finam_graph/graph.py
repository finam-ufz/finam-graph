from finam.core.interfaces import IInput, IAdapter, IOutput
from finam.core.schedule import Composition


class Graph:
    def __init__(self, comp: Composition):
        self.components, self.adapters, self.edges = _get_graph(comp)


def _get_graph(composition):
    components, adapters = _get_graph_nodes(composition)

    edges = set()

    for comp in components:
        for n, inp in comp.inputs.items():
            src = inp.get_source()
            if isinstance(src, IAdapter):
                edges.add(Edge(src, None, comp, n))
        for n, out in comp.outputs.items():
            for trg in out.get_targets():
                if isinstance(trg, IAdapter):
                    edges.add(Edge(comp, n, trg, None))

    for ad in adapters:
        src = ad.get_source()
        if isinstance(src, IAdapter):
            edges.add(Edge(src, None, ad, None))
        for trg in ad.get_targets():
            if isinstance(trg, IAdapter):
                edges.add(Edge(ad, None, trg, None))

    return components, adapters, edges


def _get_graph_nodes(composition):
    components = set(composition.modules)
    adapters = set()

    for comp in components:
        for _n, inp in comp.inputs.items():
            _trace_input(inp, adapters)
        for _n, out in comp.outputs.items():
            _trace_output(out, adapters)

    return components, adapters


def _trace_input(inp: IInput, out_adapters: set):
    src = inp.get_source()
    if isinstance(src, IAdapter):
        out_adapters.add(src)
        _trace_input(src, out_adapters)


def _trace_output(out: IOutput, out_adapters: set):
    for trg in out.get_targets():
        if isinstance(trg, IAdapter):
            out_adapters.add(trg)
            _trace_output(trg, out_adapters)


class Edge:
    def __init__(self, source, out_name, target, in_name):
        self.source = source
        self.out_name = out_name
        self.target = target
        self.in_name = in_name

    def __hash__(self):
        return hash((self.source, self.out_name, self.target, self.in_name))

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.source == other.source
            and self.out_name == other.out_name
            and self.target == other.target
            and self.in_name == other.in_name
        )

    def __repr__(self):
        return "%s[%s] -> %s[%s]" % (
            self.source.__class__.__name__,
            self.out_name or "-",
            self.target.__class__.__name__,
            self.in_name or "-",
        )
