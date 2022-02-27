from finam.core.interfaces import IInput, IAdapter, IOutput
from finam.core.schedule import Composition


class Graph:
    def __init__(self, comp: Composition):
        self.components, self.adapters, self.edges, self.direct_edges = _get_graph(comp)


def _get_graph(composition):
    components, adapters, direct_edges = _get_graph_nodes(composition)

    edges = set()

    for comp in components:
        for i, (n, inp) in enumerate(comp.inputs.items()):
            src = inp.get_source()
            if isinstance(src, IAdapter):
                edges.add(Edge(src, None, 0, comp, n, i, 0))
            else:
                for comp2 in components:
                    for ii, (nm, out) in enumerate(comp2.outputs.items()):
                        if out == src:
                            edges.add(Edge(comp2, nm, ii, comp, n, i, 0))
                            break

        for i, (n, out) in enumerate(comp.outputs.items()):
            for trg in out.get_targets():
                if isinstance(trg, IAdapter):
                    edges.add(Edge(comp, n, i, trg, None, 0, 0))

    for ad in adapters:
        src = ad.get_source()
        if isinstance(src, IAdapter):
            edges.add(Edge(src, None, 0, ad, None, 0, 0))
        for trg in ad.get_targets():
            if isinstance(trg, IAdapter):
                edges.add(Edge(ad, None, 0, trg, None, 0, 0))

    return components, adapters, edges, direct_edges


def _get_graph_nodes(composition):
    components = set(composition.modules)
    adapters = set()
    direct_edges = set()

    for comp in components:
        for i, (n, inp) in enumerate(comp.inputs.items()):
            out, depth = _trace_input(inp, adapters)
            if out is not None:
                for comp2 in components:
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
    else:
        return src, depth


def _trace_output(out: IOutput, out_adapters: set):
    for trg in out.get_targets():
        if isinstance(trg, IAdapter):
            out_adapters.add(trg)
            _trace_output(trg, out_adapters)


class Edge:
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
        return "%s[%s] -> %s[%s]" % (
            self.source.__class__.__name__,
            self.out_name or "-",
            self.target.__class__.__name__,
            self.in_name or "-",
        )
