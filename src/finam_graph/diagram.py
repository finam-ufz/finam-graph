import matplotlib.pyplot as plt
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

        plt.show(block=True)

    def draw_component(self, comp, position, axes):
        x, y = position
        name = comp.__class__.__name__

        xll, yll = (
            x * self.grid_size[0] + self.component_offset[0] + self.margin,
            y * self.grid_size[1] + self.component_offset[0] + self.margin,
        )

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
            in_sp = self.component_size[1] / len(comp.inputs)
            for i, n in enumerate(comp.inputs.keys()):
                xll_in = xll - 25
                yc_in = yll + in_sp / 2 + in_sp * i
                inp = patches.Rectangle(
                    (xll_in, yc_in - 7),
                    30, 14,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="lightgrey",
                )
                txt_in = text.Text(
                    xll_in + 2,
                    yc_in,
                    n, ha="left", va="center", size=7)

                axes.add_artist(inp)
                axes.add_artist(txt_in)

        if len(comp.outputs) > 0:
            out_sp = self.component_size[1] / len(comp.outputs)
            for i, n in enumerate(comp.outputs.keys()):
                xll_out = xll + self.component_size[0] - 5
                yc_out = yll + out_sp / 2 + out_sp * i
                inp = patches.Rectangle(
                    (xll_out, yc_out - 7),
                    30, 14,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="white",
                )
                txt_out = text.Text(
                    xll_out + 2,
                    yc_out,
                    n, ha="left", va="center", size=7)
                axes.add_artist(inp)
                axes.add_artist(txt_out)

        axes.add_artist(txt)

    def draw_adapter(self, comp, position, axes):
        x, y = position
        name = comp.__class__.__name__

        xll, yll = (
            x * self.grid_size[0] + self.adapter_offset[0] + self.margin,
            y * self.grid_size[1] + self.adapter_offset[0] + self.margin,
        )

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

        inp = patches.Rectangle(
            (xll - 5, yll + self.adapter_size[1] / 2 - 5),
            10, 10,
            linewidth=1,
            edgecolor="k",
            facecolor="lightgrey",
        )

        out = patches.Rectangle(
            (xll + self.adapter_size[0] - 5, yll + self.adapter_size[1] / 2 - 5),
            10, 10,
            linewidth=1,
            edgecolor="k",
            facecolor="white",
        )

        axes.add_artist(rect)
        axes.add_artist(inp)
        axes.add_artist(out)
        axes.add_artist(txt)
