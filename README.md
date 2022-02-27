# FINAM-Graph

A tool for visualizing FINAM model linkage setups.

![graph.svg](https://git.ufz.de/FINAM/finam-graph/uploads/2542cdd9ee03e1ccf0fc274d9859c1ec/graph.svg)

This tool analyzed FINAM coupling setups to extract the linkage graph, and renders it as a flow diagram.
The placement of graph nodes (components and adapters) is optimized to some extent, but scripted and interactive placement are also possible.

For **interactive placement**, simply click boxes to select, and click again to move them.
It is recommended to enable the placement grid by pressing `SPACE`.

**Usage:**

```python
# ...

composition = Composition([comp_a, comp_b])
composition.initialize()

comp_a.outputs["Out"] >> comp_b.inputs["In"]

GraphDiagram().draw(composition, save_path="graph.svg")
```
