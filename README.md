# FINAM-Graph

A tool for visualizing FINAM model linkage setups

![graph.svg](/uploads/1057e6291053461b2f175c51946a1efd/graph.svg)

Usage:

```python
# ...

composition = Composition([comp_a, comp_b])
composition.initialize()

comp_a.outputs["Out"] >> comp_b.inputs["In"]

GraphDiagram().draw(composition, save_path="graph.svg")
```
