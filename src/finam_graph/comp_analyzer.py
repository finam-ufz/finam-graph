from finam.core.interfaces import IInput, IAdapter, IOutput
from finam.core.schedule import Composition


class CompAnalyzer:
    def __init__(self, comp: Composition):
        self.composition = comp

    def get_graph(self):
        components, adapters = self.get_graph_nodes()

        return components, adapters

    def get_graph_nodes(self):
        components = set(self.composition.modules)
        adapters = set()

        for comp in components:
            for _n, inp in comp.inputs.items():
                self._trace_input(inp, adapters)
            for _n, out in comp.outputs.items():
                self._trace_output(out, adapters)

        return components, adapters

    def _trace_input(self, inp: IInput, out_set: set):
        src = inp.get_source()
        if isinstance(src, IAdapter):
            out_set.add(src)
            self._trace_input(src, out_set)

    def _trace_output(self, out: IOutput, out_set: set):
        for trg in out.get_targets():
            if isinstance(trg, IAdapter):
                out_set.add(trg)
                self._trace_output(trg, out_set)
