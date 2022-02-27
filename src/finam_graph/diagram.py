import math
import numpy as np

import matplotlib.pyplot as plt
from finam.core.interfaces import IComponent, ITimeComponent
from matplotlib import patches
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton
from matplotlib.path import Path

from finam_graph.graph import Graph


class GraphDiagram:
    """Diagram drawer"""

    def __init__(
        self,
        grid_size=(160, 100),
        component_size=(80, 60),
        adapter_size=(80, 30),
        margin=50,
        comp_slot_size=(30, 14),
        adap_slot_size=(10, 10),
        curve_size=20,
        corner_radius=5,
        max_label_length=12,
        max_slot_label_length=6,
        comp_color="lightgreen",
        time_comp_color="lightblue",
        selected_comp_color="blue",
        adapter_color="orange",
        selected_adapter_color="red",
    ):
        """
        Constructs a graph diagram drawer with style parameters

        :param grid_size: Size of grid cells for alignment
        :param component_size: Size of component boxes
        :param adapter_size: Size of adapter boxes
        :param margin: Margin around all boxes
        :param comp_slot_size: Input and output slot size for components
        :param adap_slot_size: Input and output slot size for adapters
        :param curve_size: Connection curve "radius" (control point distance)
        :param corner_radius: Radius for rounded corners
        :param max_label_length: Maximum number of letters in component and adapter labels
        :param max_slot_label_length: Maximum number of letters in input and output slot labels
        :param comp_color: Component color
        :param time_comp_color: TimeComponent color
        :param selected_comp_color: Component color for selection
        :param adapter_color: Adapter color
        :param selected_adapter_color: Adapter color for selection
        """

        self.grid_size = grid_size
        self.component_size = component_size
        self.adapter_size = adapter_size
        self.margin = margin

        self.comp_slot_size = comp_slot_size
        self.adap_slot_size = adap_slot_size
        self.curve_size = curve_size
        self.corner_radius = corner_radius
        self.max_label_length = max_label_length
        self.max_slot_label_length = max_slot_label_length

        self.comp_color = comp_color
        self.time_comp_color = time_comp_color
        self.selected_comp_color = selected_comp_color
        self.adapter_color = adapter_color
        self.selected_adapter_color = selected_adapter_color

        self.component_offset = (grid_size[0] - component_size[0]) / 2, (
            grid_size[1] - component_size[1]
        ) / 2
        self.adapter_offset = (grid_size[0] - adapter_size[0]) / 2, (
            grid_size[1] - adapter_size[1]
        ) / 2

        self.selected_cell = None
        self.show_grid = False

    def draw(
        self,
        composition,
        show_adapters=True,
        positions=None,
        show=True,
        block=True,
        save_path=None,
        max_iterations=25000,
        seed=None,
    ):
        """
        Draw a graph diagram.

        :param composition: The composition to draw a graph diagram for
        :param show_adapters: Whether to show adapters
        :param positions: Dictionary of grid cell position tuples per component/adapter
        :param show: Whether to show the diagram
        :param block: Should the diagram be shown in blocking mode?
        :param save_path: Path to save image file. Default: None (i.e. don't save)
        :param max_iterations: Maximum iterations for optimizing node placement. Default: 25000
        :param seed: Random seed for the optimizer. Default: None
        """
        rng = (
            np.random.default_rng()
            if seed is None
            else np.random.default_rng(seed=seed)
        )
        graph = Graph(composition)

        if positions is None:
            positions = optimize_positions(graph, rng, show_adapters, max_iterations)

        figure, ax = plt.subplots(figsize=(12, 6))
        figure.canvas.set_window_title("Graph - SPACE for grid, click to re-arrange")

        ax.axis("off")
        ax.set_aspect("equal")

        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.repaint(graph, positions, show_adapters, ax)

        if save_path is not None:
            plt.savefig(save_path)

        if show:

            def onclick(event):
                if event.xdata is None:
                    return

                if event.button == MouseButton.RIGHT:
                    self.selected_cell = None
                    self.repaint(graph, positions, show_adapters, ax)
                    return

                xdata, ydata = event.xdata, event.ydata
                cell = int(math.floor(xdata / self.grid_size[0])), int(
                    math.floor(ydata / self.grid_size[1])
                )

                if self.selected_cell is None:
                    for k, v in positions.items():
                        if v == cell:
                            self.selected_cell = k
                            self.repaint(graph, positions, show_adapters, ax)
                            break
                else:
                    positions[self.selected_cell] = cell
                    self.selected_cell = None
                    self.repaint(graph, positions, show_adapters, ax)

            def on_press(event):
                if event.key == " ":
                    self.show_grid = not self.show_grid
                    self.repaint(graph, positions, show_adapters, ax)

            def on_close(_event):
                plt.close(figure)
                plt.ioff()

            cid = figure.canvas.mpl_connect("button_press_event", onclick)
            cid = figure.canvas.mpl_connect("key_press_event", on_press)
            cid = figure.canvas.mpl_connect("close_event", on_close)

            plt.ion()
            plt.show(block=block)

    def repaint(self, graph, positions, show_adapters: bool, axes: Axes):
        while bool(axes.patches):
            axes.patches[0].remove()
        while bool(axes.texts):
            axes.texts[0].remove()

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

        axes.set_xlim(*x_lim)
        axes.set_ylim(*y_lim)

        if self.show_grid:
            self.draw_grid((x_min, y_min), (x_max, y_max), axes)

        for comp in graph.components:
            self.draw_component(comp, positions[comp], axes)

        if show_adapters:
            for ad in graph.adapters:
                self.draw_adapter(ad, positions[ad], axes)

        edges = graph.edges if show_adapters else graph.direct_edges
        for edge in edges:
            self.draw_edge(edge, positions, show_adapters, axes)

    def draw_grid(self, lower, upper, axes: Axes):
        for i in range(lower[0] - 1, upper[0] + 2):
            for j in range(lower[1] - 1, upper[1] + 2):
                rect = patches.Rectangle(
                    (i * self.grid_size[0], j * self.grid_size[1]),
                    *self.grid_size,
                    linewidth=1,
                    edgecolor="lightgrey",
                    facecolor="none",
                )
                axes.add_patch(rect)

    def draw_edge(self, edge, positions, show_adapters: bool, axes: Axes):
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

        dx = abs(p4[0] - p1[0])
        curve_sz = max(self.curve_size, dx / 2)

        p2 = p1[0] + curve_sz, p1[1]
        p3 = p4[0] - curve_sz, p4[1]

        pp1 = patches.PathPatch(
            Path(
                [p1, p2, p3, p4], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
            ),
            fc="none",
        )

        axes.add_patch(pp1)

        if edge.num_adapters > 0 and not show_adapters:
            pc = (p1[0] + p4[0]) / 2, (p1[1] + p4[1]) / 2
            rect = patches.Rectangle(
                (pc[0] - 4, pc[1] - 4),
                8,
                8,
                linewidth=1,
                edgecolor="k",
                facecolor=self.adapter_color,
            )
            axes.add_patch(rect)

            axes.text(
                *pc,
                str(edge.num_adapters),
                ha="center",
                va="center",
                size=6,
            )

    def draw_component(self, comp, position, axes: Axes):
        name = comp.__class__.__name__
        xll, yll = self.comp_pos(comp, position)

        rect = patches.FancyBboxPatch(
            (xll, yll),
            *self.component_size,
            boxstyle="round,rounding_size=%f" % (self.corner_radius,),
            linewidth=1,
            edgecolor="k",
            facecolor=self.selected_comp_color
            if self.selected_cell == comp
            else (
                self.time_comp_color
                if isinstance(comp, ITimeComponent)
                else self.comp_color
            ),
        )
        axes.add_patch(rect)

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
                axes.add_patch(inp)
                axes.text(
                    xll + xlli + 2,
                    yll + ylli + self.comp_slot_size[1] / 2,
                    shorten_str(n, self.max_slot_label_length),
                    ha="left",
                    va="center",
                    size=7,
                )

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
                axes.add_patch(inp)
                axes.text(
                    xll + xllo + 2,
                    yll + yllo + self.comp_slot_size[1] / 2,
                    shorten_str(n, self.max_slot_label_length),
                    ha="left",
                    va="center",
                    size=7,
                )

        axes.text(
            xll + self.component_size[0] / 2,
            yll + self.component_size[1] / 2,
            shorten_str(name.replace("Component", "Co"), self.max_label_length),
            ha="center",
            va="center",
            size=8,
        )

    def draw_adapter(self, comp, position, axes: Axes):
        name = comp.__class__.__name__
        xll, yll = self.comp_pos(comp, position)

        rect = patches.FancyBboxPatch(
            (xll, yll),
            *self.adapter_size,
            boxstyle="round, pad=0, rounding_size=%f" % (self.corner_radius,),
            linewidth=1,
            edgecolor="k",
            facecolor=self.selected_adapter_color
            if self.selected_cell == comp
            else self.adapter_color,
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

        axes.add_patch(rect)
        axes.add_patch(inp)
        axes.add_patch(out)

        axes.text(
            xll + self.adapter_size[0] / 2,
            yll + self.adapter_size[1] / 2,
            shorten_str(name.replace("Adapter", "Cd."), self.max_label_length),
            ha="center",
            va="center",
            size=8,
        )

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
            cnt = len(comp_or_ada.inputs)
            inv_idx = cnt - 1 - idx
            in_sp = self.component_size[1] / cnt
            return (
                -self.comp_slot_size[0],
                in_sp / 2 + in_sp * inv_idx - self.comp_slot_size[1] / 2,
            )
        else:
            return (
                -self.adap_slot_size[0],
                self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2,
            )

    def output_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            cnt = len(comp_or_ada.outputs)
            inv_idx = cnt - 1 - idx
            out_sp = self.component_size[1] / cnt
            return (
                self.component_size[0],
                out_sp / 2 + out_sp * inv_idx - self.comp_slot_size[1] / 2,
            )
        else:
            return (
                self.adapter_size[0],
                self.adapter_size[1] / 2 - self.adap_slot_size[1] / 2,
            )


def shorten_str(s, max_length):
    if len(s) > max_length:
        return "%s." % s[0 : (max(1, max_length - 1))]
    return s


def optimize_positions(graph: Graph, rng, show_adapters: bool, max_iterations: int):
    length = len(graph.components)
    if show_adapters:
        length += len(graph.adapters)
    size = math.ceil(math.sqrt(length)) * 3
    grid = np.ndarray((size, size), dtype=object)
    pos = {}

    all_mods = (
        set.union(graph.components, graph.adapters)
        if show_adapters
        else graph.components
    )
    for c in all_mods:
        while True:
            x, y = rng.integers(0, size, 2)
            if grid[x, y] is None:
                grid[x, y] = c
                break
        pos[c] = x, y

    score = rate_positions(pos, graph.edges if show_adapters else graph.direct_edges)

    nodes = list(pos.keys())
    nodes.sort(key=lambda co: co.__class__.__name__)

    last_improvement = 0

    print("Optimizing graph layout...")

    i = -1
    for i in range(max_iterations):
        pos_new = dict(pos)
        grid_new = grid.copy()

        for j in range(rng.integers(1, 5, 1)[0]):
            node = rng.choice(nodes)
            x, y = rng.integers(0, size, 2)

            node_here = grid_new[x, y]
            if node_here == node:
                continue

            if node_here is None:
                grid_new[pos_new[node]] = None
                grid_new[x, y] = node
                pos_new[node] = (x, y)
            else:
                grid_new[pos_new[node]] = node_here
                grid_new[x, y] = node
                pos_new[node_here] = pos_new[node]
                pos_new[node] = (x, y)

        score_new = rate_positions(
            pos_new, graph.edges if show_adapters else graph.direct_edges
        )

        if score_new <= score:
            if score_new < score:
                last_improvement = i

            pos = pos_new
            grid = grid_new
            score = score_new

        if i > 2500 and i > 4 * last_improvement:
            break

    print("Done (%d iterations, score %s)" % (i + 1, score))

    return pos


def rate_positions(pos, edges):
    score = 0.0
    for e in edges:
        p1 = pos[e.source]
        p2 = pos[e.target]

        dx = p2[0] - (p1[0] + 1)

        sc_rev_same_row = 0
        sc_x = dx
        if dx < 0:
            if p2[1] == p1[1]:
                sc_rev_same_row = 5
            if dx < -1:
                sc_x *= 2

        dist = abs(sc_x) + max(0, abs(p2[1] - p1[1]) - 0.5) + sc_rev_same_row
        score += dist

    return score**2
