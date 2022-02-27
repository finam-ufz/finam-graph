import unittest
import numpy as np
from datetime import datetime, timedelta

from finam.adapters import base, time
from finam.core.interfaces import ComponentStatus
from finam.core.schedule import Composition
from finam.core.sdk import ATimeComponent, Input
from finam.data.grid import Grid, GridSpec
from finam.modules.generators import CallbackGenerator
from finam.modules.callback import CallbackComponent

from finam_graph.graph import Graph


def generate_grid():
    return Grid(GridSpec(10, 5), data=np.random.random(50))


class TestCompAnalyzer(unittest.TestCase):
    def test_analyze(self):
        source = CallbackGenerator(
            callbacks={"Grid": lambda t: generate_grid()},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = CallbackComponent(
            inputs=["Input"],
            outputs=[],
            callback=lambda data, t: {},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer2 = CallbackComponent(
            inputs=["Input"],
            outputs=[],
            callback=lambda data, t: {},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        grid_to_val = base.GridToValue(np.mean)
        lin_interp = time.LinearInterpolation()

        composition = Composition([source, consumer, consumer2])
        composition.initialize()

        _ = (
            source.outputs["Grid"]
            >> grid_to_val
            >> lin_interp
            >> consumer.inputs["Input"]
        )

        _ = source.outputs["Grid"] >> consumer2.inputs["Input"]

        graph = Graph(composition)
        self.assertEqual(len(graph.components), 3)
        self.assertEqual(len(graph.adapters), 2)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(len(graph.direct_edges), 2)
        self.assertEqual(len(graph.simple_edges), 2)
