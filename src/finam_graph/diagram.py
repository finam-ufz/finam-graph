import matplotlib.pyplot as plt
from finam.core.interfaces import IComponent
from matplotlib import patches, text
from matplotlib.path import Path

from finam_graph.comp_analyzer import CompAnalyzer


class CompDiagram:
    def __init__(
        self,
        grid_size=(200, 100),
        component_size=(140, 80),
        adapter_size=(120, 40),
        margin=20,
        comp_slot_size=(30, 14),
        adap_slot_size=(10, 10),
        curve_size=30,
    ):
        self.grid_size = grid_size
        self.component_size = component_size
        self.adapter_size = adapter_size
        self.margin = margin

        self.comp_slot_size = comp_slot_size
        self.adap_slot_size = adap_slot_size
        self.curve_size = curve_size

        self.component_offset = (grid_size[0] - component_size[0]) / 2, (
            grid_size[1] - component_size[1]
        ) / 2
        self.adapter_offset = (grid_size[0] - adapter_size[0]) / 2, (
            grid_size[1] - adapter_size[1]
        ) / 2

    def draw(self, composition, positions, show=True, save_path=None):
        analyzer = CompAnalyzer(composition)
        components, adapters, edges = analyzer.get_graph()

        plt.ion()

        figure, ax = plt.subplots(figsize=(12, 6))
        ax.axis("off")
        ax.set_aspect("equal")

        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        x_min, y_min = 99999, 99999
        x_max, y_max = -99999, -99999
        for _c, pos in positions.items():
            if pos[0] < x_min:
                x_min = pos[0]
            if pos[1] < y_min:
                y_min = pos[1]
            if pos[0] > x_max:
                x_max = pos[0]
            if pos[1] > y_max:
                y_max = pos[1]

        x_lim = (
            x_min * self.grid_size[0] - self.margin,
            (x_max + 1) * self.grid_size[0] + self.margin,
        )
        y_lim = (
            y_min * self.grid_size[1] - self.margin,
            (y_max + 1) * self.grid_size[1] + self.margin,
        )

        ax.set_xlim(*x_lim)
        ax.set_ylim(*y_lim)

        for comp in components:
            self.draw_component(comp, positions[comp], ax)

        for ad in adapters:
            self.draw_adapter(ad, positions[ad], ax)

        for edge in edges:
            self.draw_edge(edge, positions, ax)

        if save_path is not None:
            plt.savefig(save_path)

        if show:
            plt.show(block=True)

    def draw_edge(self, edge, positions, axes):
        src_pos = self.comp_pos(edge.source, positions[edge.source])
        trg_pos = self.comp_pos(edge.target, positions[edge.target])

        if isinstance(edge.source, IComponent):
            out_idx = list(edge.source.outputs.keys()).index(edge.out_name)
            out_size = self.comp_slot_size
        else:
            out_idx = 0
            out_size = self.adap_slot_size

        if isinstance(edge.target, IComponent):
            in_idx = list(edge.target.inputs.keys()).index(edge.in_name)
            in_size = self.comp_slot_size
        else:
            in_idx = 0
            in_size = self.adap_slot_size

        out_off = self.output_pos(edge.source, out_idx)
        in_off = self.input_pos(edge.target, in_idx)

        p1 = (
            src_pos[0] + out_off[0] + out_size[0],
            src_pos[1] + out_off[1] + out_size[1] / 2,
        )
        p4 = trg_pos[0] + in_off[0], trg_pos[1] + in_off[1] + in_size[1] / 2

        p2 = p1[0] + self.curve_size, p1[1]
        p3 = p4[0] - self.curve_size, p4[1]

        pp1 = patches.PathPatch(
            Path(
                [p1, p2, p3, p4], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
            ),
            fc="none",
        )

        axes.add_patch(pp1)

    def draw_component(self, comp, position, axes):
        name = comp.__class__.__name__
        xll, yll = self.comp_pos(comp, position)

        rect = patches.Rectangle(
            (xll, yll),
            *self.component_size,
            linewidth=1,
            edgecolor="k",
            facecolor="lightblue",
        )
        txt = text.Text(
            xll + self.component_size[0] / 2,
            yll + self.component_size[1] / 2,
            name.replace("Component", "Co."),
            ha="center",
            va="center",
            size=8,
        )

        axes.add_artist(rect)

        if len(comp.inputs) > 0:
            for i, n in enumerate(comp.inputs.keys()):
                xlli, ylli = self.input_pos(comp, i)
                inp = patches.Rectangle(
                    (xll + xlli, yll + ylli),
                    *self.comp_slot_size,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="lightgrey",
                )
                txt_in = text.Text(
                    xll + xlli + 2,
                    yll + ylli + self.comp_slot_size[1] / 2,
                    n,
                    ha="left",
                    va="center",
                    size=7,
                )

                axes.add_artist(inp)
                axes.add_artist(txt_in)

        if len(comp.outputs) > 0:
            for i, n in enumerate(comp.outputs.keys()):
                xllo, yllo = self.output_pos(comp, i)
                inp = patches.Rectangle(
                    (xll + xllo, yll + yllo),
                    *self.comp_slot_size,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="white",
                )
                txt_out = text.Text(
                    xll + xllo + 2,
                    yll + yllo + self.comp_slot_size[1] / 2,
                    n,
                    ha="left",
                    va="center",
                    size=7,
                )
                axes.add_artist(inp)
                axes.add_artist(txt_out)

        axes.add_artist(txt)

    def draw_adapter(self, comp, position, axes):
        name = comp.__class__.__name__
        xll, yll = self.comp_pos(comp, position)

        rect = patches.Rectangle(
            (xll, yll),
            *self.adapter_size,
            linewidth=1,
            edgecolor="k",
            facecolor="orange",
        )
        txt = text.Text(
            xll + self.adapter_size[0] / 2,
            yll + self.adapter_size[1] / 2,
            name.replace("Adapter", "Cd."),
            ha="center",
            va="center",
            size=8,
        )

        xlli, ylli = self.input_pos(comp, 0)
        inp = patches.Rectangle(
            (xll + xlli, yll + ylli),
            *self.adap_slot_size,
            linewidth=1,
            edgecolor="k",
            facecolor="lightgrey",
        )

        xllo, yllo = self.output_pos(comp, 0)
        out = patches.Rectangle(
            (xll + xllo, yll + yllo),
            *self.adap_slot_size,
            linewidth=1,
            edgecolor="k",
            facecolor="white",
        )

        axes.add_artist(rect)
        axes.add_artist(inp)
        axes.add_artist(out)
        axes.add_artist(txt)

    def comp_pos(self, comp_or_ada, pos):
        if isinstance(comp_or_ada, IComponent):
            return (
                pos[0] * self.grid_size[0] + self.component_offset[0],
                pos[1] * self.grid_size[1] + self.component_offset[1],
            )
        else:
            return (
                pos[0] * self.grid_size[0] + self.adapter_offset[0],
                pos[1] * self.grid_size[1] + self.adapter_offset[1],
            )

    def input_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            in_sp = self.component_size[1] / len(comp_or_ada.inputs)
            return (
                -self.comp_slot_size[0],
                in_sp / 2 + in_sp * idx - self.comp_slot_size[1] / 2,
            )
        else:
            return (
                -self.adap_slot_size[0],
                self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2,
            )

    def output_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            out_sp = self.component_size[1] / len(comp_or_ada.outputs)
            return (
                self.component_size[0],
                out_sp / 2 + out_sp * idx - self.comp_slot_size[1] / 2,
            )
        else:
            return (
                self.adapter_size[0],
                self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2,
            )
