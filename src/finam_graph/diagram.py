"""Main module for graph diagram drawer"""
import math

import matplotlib.pyplot as plt
import numpy as np
from finam.interfaces import IComponent, ITimeComponent
from matplotlib import patches
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton
from matplotlib.path import Path

from finam_graph.graph import Graph


class GraphSizes:
    """Graph sizing properties

    Parameters
    ----------
    grid_size : (int, int)
        Size of grid cells for alignment
    component_size : (int, int)
        Size of component boxes
    adapter_size : (int, int)
        Size of adapter boxes
    margin : int
        Margin around all boxes
    comp_slot_size : (int, int)
        Input and output slot size for components
    adap_slot_size : (int, int)
        Input and output slot size for adapters
    curve_size : int
        Connection curve "radius" (control point distance)
    """

    def __init__(
        self,
        grid_size=(160, 100),
        component_size=(80, 60),
        adapter_size=(80, 30),
        margin=50,
        comp_slot_size=(30, 14),
        adap_slot_size=(10, 10),
        curve_size=20,
    ):
        self.grid_size = grid_size
        self.component_size = component_size
        self.adapter_size = adapter_size
        self.margin = margin

        self.comp_slot_size = comp_slot_size
        self.adap_slot_size = adap_slot_size
        self.curve_size = curve_size


class GraphColors:
    """Graph coloring properties

    Parameters
    ----------
    comp_color : str
        :class:`finam.Component` color
    time_comp_color : str
        :class:`finam.TimeComponent` color
    selected_comp_color : str
        Component color for selection
    adapter_color : str
        :class:`finam.Adapter` color
    selected_adapter_color : str
        Adapter color for selection
    """

    def __init__(
        self,
        comp_color="lightgreen",
        time_comp_color="lightblue",
        selected_comp_color="blue",
        adapter_color="orange",
        selected_adapter_color="red",
    ):
        self.comp_color = comp_color
        self.time_comp_color = time_comp_color
        self.selected_comp_color = selected_comp_color
        self.adapter_color = adapter_color
        self.selected_adapter_color = selected_adapter_color


class GraphDiagram:
    """Diagram drawer.

    Examples
    --------

    .. code-block:: Python

        composition = Composition([comp_a, comp_b])
        composition.initialize()

        comp_a.outputs["Out"] >> comp_b.inputs["In"]

        diagram = GraphDiagram()
        diagram.draw(composition, save_path="graph.svg")

    Parameters
    ----------
    sizes : GraphSizes
        Graph sizing properties object :class:`.GraphSizes`.
    colors : GraphColors
        Graph coloring properties object :class:`.GraphColors`.
    corner_radius : int
        Radius for rounded corners
    max_label_length : int
        Maximum number of characters in component and adapter labels
    max_slot_label_length : int
        Maximum number of characters in input and output slot labels
    """

    def __init__(
        self,
        sizes=GraphSizes(),
        colors=GraphColors(),
        corner_radius=5,
        max_label_length=12,
        max_slot_label_length=6,
    ):
        self.sizes = sizes
        self.colors = colors
        self.corner_radius = corner_radius
        self.max_label_length = max_label_length
        self.max_slot_label_length = max_slot_label_length

        self.component_offset = (sizes.grid_size[0] - sizes.component_size[0]) / 2, (
            sizes.grid_size[1] - sizes.component_size[1]
        ) / 2
        self.adapter_offset = (sizes.grid_size[0] - sizes.adapter_size[0]) / 2, (
            sizes.grid_size[1] - sizes.adapter_size[1]
        ) / 2

        self.selected_cell = None
        self.show_grid = False

    def draw(
        self,
        composition,
        details=2,
        excluded=None,
        positions=None,
        labels=None,
        colors=None,
        show=True,
        block=True,
        save_path=None,
        max_iterations=25000,
        seed=None,
    ):
        """
        Draw a graph diagram.

        Parameters
        ----------
        composition : Composition
            The :class:`finam.Composition` to draw a graph diagram for
        excluded : list or set, optional
            List of excluded components. Default: None
        details : int, optional
            Level of details of the graph plot.

            * 0: Simple graph without slots and adapters
            * 1: Detailed graph, with collapsed adapters
            * 2: Full detailed graph, with adapters

            Defaults to 2.
        positions : dict, optional
            Dictionary of grid cell position tuples per component/adapter. Default: None (optimized)
        labels : dict, optional
            Dictionary of label overrides for components, adapters and input/output slots. Default: None
        colors : dict, optional
            Dictionary of component/adapter color overrides. Default: None
        show : bool, optional
            Whether to show the diagram. Default: True
        block : bool, optional
            Should the diagram be shown in blocking mode? Default: True
        save_path : pathlike, optional
            Path to save image file. Default: None (i.e. don't save)
        max_iterations : int, optional
            Maximum iterations for optimizing node placement. Default: 25000
        seed : int, optional
            Random seed for the optimizer. Default: None
        """
        colors = colors or {}
        labels = labels or {}
        excluded = set(excluded) if excluded is not None else set()

        show_adapters = details > 1
        simple = details < 1

        rng = (
            np.random.default_rng()
            if seed is None
            else np.random.default_rng(seed=seed)
        )
        graph = Graph(composition, excluded)

        if positions is None:
            positions = _optimize_positions(
                graph, rng, simple, show_adapters, max_iterations
            )

        figure, ax = plt.subplots(figsize=(12, 6))

        if figure.canvas.manager is not None:
            figure.canvas.manager.set_window_title(
                "Graph - SPACE for grid, click to re-arrange"
            )

        ax.axis("off")
        ax.set_aspect("equal")

        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self._repaint(graph, positions, labels, colors, simple, show_adapters, ax)

        if save_path is not None:
            plt.savefig(save_path)

        if show:
            self._show(
                graph,
                positions,
                labels,
                colors,
                simple,
                show_adapters,
                ax,
                figure,
                block,
            )

    def _show(
        self, graph, positions, labels, colors, simple, show_adapters, ax, figure, block
    ):
        def onclick(event):
            if event.xdata is None:
                return

            if event.button == MouseButton.RIGHT:
                self.selected_cell = None
                self._repaint(
                    graph, positions, labels, colors, simple, show_adapters, ax
                )
                return

            xdata, ydata = event.xdata, event.ydata
            cell = int(math.floor(xdata / self.sizes.grid_size[0])), int(
                math.floor(ydata / self.sizes.grid_size[1])
            )

            if self.selected_cell is None:
                for k, v in positions.items():
                    if v == cell:
                        self.selected_cell = k
                        self._repaint(
                            graph,
                            positions,
                            labels,
                            colors,
                            simple,
                            show_adapters,
                            ax,
                        )
                        break
            else:
                positions[self.selected_cell] = cell
                self.selected_cell = None
                self._repaint(
                    graph, positions, labels, colors, simple, show_adapters, ax
                )

        def on_press(event):
            if event.key == " ":
                self.show_grid = not self.show_grid
                self._repaint(
                    graph, positions, labels, colors, simple, show_adapters, ax
                )

        def on_close(_event):
            plt.close(figure)
            plt.ioff()

        _cid = figure.canvas.mpl_connect("button_press_event", onclick)
        _cid = figure.canvas.mpl_connect("key_press_event", on_press)
        _cid = figure.canvas.mpl_connect("close_event", on_close)

        plt.ion()
        plt.show(block=block)

    def _repaint(
        self,
        graph,
        positions,
        labels,
        colors,
        simple: bool,
        show_adapters: bool,
        axes: Axes,
    ):
        while bool(axes.patches):
            axes.patches[0].remove()
        while bool(axes.texts):
            axes.texts[0].remove()

        x_bounds, y_bounds = _calc_bounds(positions)
        x_lim, y_lim = self._calc_limits(x_bounds, y_bounds)

        axes.set_xlim(*x_lim)
        axes.set_ylim(*y_lim)

        if self.show_grid:
            self._draw_grid(x_bounds, y_bounds, axes)

        comp_patches = {}
        for comp in graph.components:
            comp_patches[comp] = self._draw_component(
                comp,
                positions[comp],
                labels.get(comp),
                colors.get(comp),
                simple,
                labels,
                axes,
            )

        if show_adapters:
            for ad in graph.adapters:
                self._draw_adapter(
                    ad, positions[ad], labels.get(ad), colors.get(ad), axes
                )

        if simple:
            self._draw_edges_simple(graph.simple_edges, positions, comp_patches, axes)
            return

        edges = graph.edges if show_adapters else graph.direct_edges
        for edge in edges:
            self._draw_edge(edge, positions, show_adapters, axes)

    def _calc_limits(self, x_min_max, y_min_max):
        x_lim = (
            x_min_max[0] * self.sizes.grid_size[0] - self.sizes.margin,
            (x_min_max[1] + 1) * self.sizes.grid_size[0] + self.sizes.margin,
        )
        y_lim = (
            y_min_max[0] * self.sizes.grid_size[1] - self.sizes.margin,
            (y_min_max[1] + 1) * self.sizes.grid_size[1] + self.sizes.margin,
        )
        return x_lim, y_lim

    def _draw_grid(self, x_bounds, y_bounds, axes: Axes):
        for i in range(x_bounds[0] - 1, x_bounds[1] + 2):
            for j in range(y_bounds[0] - 1, y_bounds[1] + 2):
                rect = patches.Rectangle(
                    (i * self.sizes.grid_size[0], j * self.sizes.grid_size[1]),
                    *self.sizes.grid_size,
                    linewidth=1,
                    edgecolor="lightgrey",
                    facecolor="none",
                )
                axes.add_patch(rect)

    def _draw_edges_simple(self, simple_edges, positions, comp_patches, axes: Axes):
        drawn = set()
        for source, target in simple_edges:
            if (source, target) in drawn:
                continue

            bidir = (target, source) in simple_edges
            if bidir:
                drawn.add((target, source))

            src_pos = self._comp_pos(source, positions[source])
            trg_pos = self._comp_pos(target, positions[target])

            src_pos = (
                src_pos[0] + self.sizes.component_size[0] / 2,
                src_pos[1] + self.sizes.component_size[1] / 2,
            )
            trg_pos = (
                trg_pos[0] + self.sizes.component_size[0] / 2,
                trg_pos[1] + self.sizes.component_size[1] / 2,
            )

            style = "<|-|>" if bidir else "-|>"
            arr = patches.ConnectionPatch(
                src_pos,
                trg_pos,
                "data",
                "data",
                patchA=comp_patches[source],
                patchB=comp_patches[target],
                arrowstyle=style,
                mutation_scale=20,
                fc="w",
            )

            axes.add_patch(arr)

    def _draw_edge(self, edge, positions, show_adapters: bool, axes: Axes):
        src_pos = self._comp_pos(edge.source, positions[edge.source])
        trg_pos = self._comp_pos(edge.target, positions[edge.target])

        if isinstance(edge.source, IComponent):
            out_idx = list(edge.source.outputs.keys()).index(edge.out_name)
            out_size = self.sizes.comp_slot_size
        else:
            out_idx = 0
            out_size = self.sizes.adap_slot_size

        if isinstance(edge.target, IComponent):
            in_idx = list(edge.target.inputs.keys()).index(edge.in_name)
            in_size = self.sizes.comp_slot_size
        else:
            in_idx = 0
            in_size = self.sizes.adap_slot_size

        out_off = self._output_pos(edge.source, out_idx)
        in_off = self._input_pos(edge.target, in_idx)

        p1 = (
            src_pos[0] + out_off[0] + out_size[0],
            src_pos[1] + out_off[1] + out_size[1] / 2,
        )
        p4 = trg_pos[0] + in_off[0], trg_pos[1] + in_off[1] + in_size[1] / 2

        dx = abs(p4[0] - p1[0])
        curve_sz = max(self.sizes.curve_size, dx / 2)

        p2 = p1[0] + curve_sz, p1[1]
        p3 = p4[0] - curve_sz, p4[1]

        axes.add_patch(
            patches.PathPatch(
                Path(
                    [p1, p2, p3, p4],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4],
                ),
                fc="none",
            )
        )

        if edge.num_adapters > 0 and not show_adapters:
            pc = (p1[0] + p4[0]) / 2, (p1[1] + p4[1]) / 2
            axes.add_patch(
                patches.Rectangle(
                    (pc[0] - 4, pc[1] - 4),
                    8,
                    8,
                    linewidth=1,
                    edgecolor="k",
                    facecolor=self.colors.adapter_color,
                )
            )

            axes.text(
                *pc,
                str(edge.num_adapters),
                ha="center",
                va="center",
                size=6,
            )

    def _draw_component(self, comp, position, label, color, simple, labels, axes: Axes):
        name = label or comp.name
        xll, yll = self._comp_pos(comp, position)

        rect = patches.FancyBboxPatch(
            (xll, yll),
            *self.sizes.component_size,
            boxstyle=f"round,rounding_size={self.corner_radius}",
            linewidth=1,
            edgecolor="k",
            facecolor=self.colors.selected_comp_color
            if self.selected_cell == comp
            else color
            or (
                self.colors.time_comp_color
                if isinstance(comp, ITimeComponent)
                else self.colors.comp_color
            ),
        )
        axes.add_patch(rect)

        if not simple:
            self._draw_slots(comp, labels, xll, yll, axes)

        axes.text(
            xll + self.sizes.component_size[0] / 2,
            yll + self.sizes.component_size[1] / 2,
            _shorten_str(name.replace("Component", "Co"), self.max_label_length),
            ha="center",
            va="center",
            size=8,
        )

        return rect

    def _draw_slots(self, comp, labels, xll, yll, axes):
        if len(comp.inputs) > 0:
            for i, (n, inp) in enumerate(comp.inputs.items()):
                in_name = labels.get(inp, n)
                xlli, ylli = self._input_pos(comp, i)
                inp_rect = patches.Rectangle(
                    (xll + xlli, yll + ylli),
                    *self.sizes.comp_slot_size,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="lightgrey",
                )
                axes.add_patch(inp_rect)
                axes.text(
                    xll + xlli + 2,
                    yll + ylli + self.sizes.comp_slot_size[1] / 2,
                    _shorten_str(in_name, self.max_slot_label_length),
                    ha="left",
                    va="center",
                    size=7,
                )

        if len(comp.outputs) > 0:
            for i, (n, out) in enumerate(comp.outputs.items()):
                out_name = labels.get(out, n)
                xllo, yllo = self._output_pos(comp, i)
                out_rect = patches.Rectangle(
                    (xll + xllo, yll + yllo),
                    *self.sizes.comp_slot_size,
                    linewidth=1,
                    edgecolor="k",
                    facecolor="white",
                )
                axes.add_patch(out_rect)
                axes.text(
                    xll + xllo + 2,
                    yll + yllo + self.sizes.comp_slot_size[1] / 2,
                    _shorten_str(out_name, self.max_slot_label_length),
                    ha="left",
                    va="center",
                    size=7,
                )

    def _draw_adapter(self, comp, position, label, color, axes: Axes):
        name = label or comp.name
        xll, yll = self._comp_pos(comp, position)

        rect = patches.FancyBboxPatch(
            (xll, yll),
            *self.sizes.adapter_size,
            boxstyle=f"round, pad=0, rounding_size={self.corner_radius}",
            linewidth=1,
            edgecolor="k",
            facecolor=self.colors.selected_adapter_color
            if self.selected_cell == comp
            else color or self.colors.adapter_color,
        )

        xlli, ylli = self._input_pos(comp, 0)
        inp = patches.Rectangle(
            (xll + xlli, yll + ylli),
            *self.sizes.adap_slot_size,
            linewidth=1,
            edgecolor="k",
            facecolor="lightgrey",
        )

        xllo, yllo = self._output_pos(comp, 0)
        out = patches.Rectangle(
            (xll + xllo, yll + yllo),
            *self.sizes.adap_slot_size,
            linewidth=1,
            edgecolor="k",
            facecolor="white",
        )

        axes.add_patch(rect)
        axes.add_patch(inp)
        axes.add_patch(out)

        axes.text(
            xll + self.sizes.adapter_size[0] / 2,
            yll + self.sizes.adapter_size[1] / 2,
            _shorten_str(name.replace("Adapter", "Ad."), self.max_label_length),
            ha="center",
            va="center",
            size=8,
        )

    def _comp_pos(self, comp_or_ada, pos):
        if isinstance(comp_or_ada, IComponent):
            return (
                pos[0] * self.sizes.grid_size[0] + self.component_offset[0],
                pos[1] * self.sizes.grid_size[1] + self.component_offset[1],
            )

        return (
            pos[0] * self.sizes.grid_size[0] + self.adapter_offset[0],
            pos[1] * self.sizes.grid_size[1] + self.adapter_offset[1],
        )

    def _input_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            cnt = len(comp_or_ada.inputs)
            inv_idx = cnt - 1 - idx
            in_sp = self.sizes.component_size[1] / cnt
            return (
                -self.sizes.comp_slot_size[0],
                in_sp / 2 + in_sp * inv_idx - self.sizes.comp_slot_size[1] / 2,
            )

        return (
            -self.sizes.adap_slot_size[0],
            self.sizes.adapter_size[1] / 2 - self.sizes.adap_slot_size[1] / 2,
        )

    def _output_pos(self, comp_or_ada, idx):
        if isinstance(comp_or_ada, IComponent):
            cnt = len(comp_or_ada.outputs)
            inv_idx = cnt - 1 - idx
            out_sp = self.sizes.component_size[1] / cnt
            return (
                self.sizes.component_size[0],
                out_sp / 2 + out_sp * inv_idx - self.sizes.comp_slot_size[1] / 2,
            )

        return (
            self.sizes.adapter_size[0],
            self.sizes.adapter_size[1] / 2 - self.sizes.adap_slot_size[1] / 2,
        )


def _calc_bounds(positions):
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

    return (x_min, x_max), (y_min, y_max)


def _shorten_str(s, max_length):
    if len(s) > max_length:
        return s[0 : (max(1, max_length - 1))]
    return s


def _optimize_positions(
    graph: Graph, rng, simple: bool, show_adapters: bool, max_iterations: int
):
    length = len(graph.components)
    if show_adapters:
        length += len(graph.adapters)
    size = math.ceil(math.sqrt(length)) * 3
    grid = np.ndarray((size, size), dtype=object)

    all_mods = (
        set.union(graph.components, graph.adapters)
        if show_adapters
        else graph.components
    )
    pos = _random_initial_positions(all_mods, grid, size, rng)

    nodes = list(pos.keys())
    nodes.sort(key=lambda co: co.__class__.__name__)

    return _do_optimize_positions(
        graph, nodes, simple, show_adapters, pos, grid, size, max_iterations, rng
    )


def _do_optimize_positions(
    graph, nodes, simple, show_adapters, pos, grid, size, max_iterations, rng
):

    print("Optimizing graph layout...")

    score = _rate_positions(
        pos, graph.edges if show_adapters else graph.direct_edges, simple
    )

    last_improvement = 0
    i = -1
    for i in range(max_iterations):
        pos_new = dict(pos)
        grid_new = grid.copy()

        for _j in range(rng.integers(1, 5, 1)[0]):
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

        score_new = _rate_positions(
            pos_new, graph.edges if show_adapters else graph.direct_edges, simple
        )

        if score_new <= score:
            if score_new < score:
                last_improvement = i

            pos = pos_new
            grid = grid_new
            score = score_new

        if i > 2500 and i > 4 * last_improvement:
            break

    print(f"Done ({i + 1} iterations, score {score})")

    return pos


def _random_initial_positions(all_mods, grid, size, rng):
    pos = {}
    for c in all_mods:
        while True:
            x, y = rng.integers(0, size, 2)
            if grid[x, y] is None:
                grid[x, y] = c
                break
        pos[c] = x, y

    return pos


def _rate_positions(pos, edges, simple: bool):
    score = 0.0

    if simple:
        for e in edges:
            p1 = pos[e.source]
            p2 = pos[e.target]

            dist = abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])
            score += dist
    else:
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
