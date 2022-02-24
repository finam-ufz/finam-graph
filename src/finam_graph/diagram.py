import matplotlib.pyplot as plt
from finam.core.interfaces import IComponent
from matplotlib import patches, text


class CompDiagram:
    def __init__(
        self,
        grid_size=(200, 100),
        component_size=(160, 80),
        adapter_size=(140, 40),
        margin=20,
    ):
        self.grid_size = grid_size
        self.component_size = component_size
        self.adapter_size = adapter_size
        self.margin = margin

        self.comp_slot_size = (30, 14)
        self.adap_slot_size = (10, 10)

        self.component_offset = (grid_size[0] - component_size[0]) / 2, (
            grid_size[1] - component_size[1]
        ) / 2
        self.adapter_offset = (grid_size[0] - adapter_size[0]) / 2, (
                grid_size[1] - adapter_size[1]
        ) / 2

    def draw(self, components, adapters, edges, positions):
        plt.ion()

        figure, ax = plt.subplots(figsize=(12, 6))
        ax.axis("off")
        ax.set_aspect("equal")

        figure.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.06)

        bbox = ax.get_window_extent().transformed(figure.dpi_scale_trans.inverted())
        width, height = bbox.width * figure.dpi, bbox.height * figure.dpi

        ax.set_xlim(0, width)
        ax.set_ylim(0, height)

        for comp in components:
            self.draw_component(comp, positions[comp], ax)

        for ad in adapters:
            self.draw_adapter(ad, positions[ad], ax)

        for edge in edges:
            self.draw_edge(edge, positions, ax)

        plt.show(block=True)

    def draw_edge(self, edge, positions, axes):
        fpos = positions[edge.source]
        tpos = positions[edge.target]

        if isinstance(edge.source, IComponent):
            out_idx = list(edge.source.outputs.keys()).index(edge.out_name)
        else:
            out_idx = 0

        if isinstance(edge.target, IComponent):
            in_idx = list(edge.target.inputs.keys()).index(edge.in_name)
        else:
            in_idx = 0

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
            name.replace("Component", "Co."), ha="center", va="center", size=8)

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
                    n, ha="left", va="center", size=7)

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
                    n, ha="left", va="center", size=7)
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
            name.replace("Adapter", "Cd."), ha="center", va="center", size=8)

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
                pos[0] * self.grid_size[0] + self.component_offset[0] + self.margin,
                pos[1] * self.grid_size[1] + self.component_offset[0] + self.margin,
            )
        else:
            return (
                pos[0] * self.grid_size[0] + self.adapter_offset[0] + self.margin,
                pos[1] * self.grid_size[1] + self.adapter_offset[0] + self.margin,
            )

    def input_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            in_sp = self.component_size[1] / len(comp_or_ada.inputs)
            return -self.comp_slot_size[0], in_sp / 2 + in_sp * idx - self.comp_slot_size[1] / 2
        else:
            return -self.adap_slot_size[0], self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2

    def output_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            out_sp = self.component_size[1] / len(comp_or_ada.outputs)
            return self.component_size[0], out_sp / 2 + out_sp * idx - self.comp_slot_size[1] / 2
        else:
            return self.adapter_size[0], self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2
