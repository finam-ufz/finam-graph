import unittest
from datetime import datetime, timedelta

import numpy as np
from finam import (ATimeComponent, ComponentStatus, Composition, Info, Input,
                   NoGrid, UniformGrid)
from finam.adapters import base, time
from finam.modules.callback import CallbackComponent
from finam.modules.debug import DebugConsumer
from finam.modules.generators import CallbackGenerator

from finam_graph.graph import Graph


def generate_grid(grid):
    return np.random.random(grid.data_size).reshape(
        shape=grid.data_shape, order=grid.order
    )


class TestCompAnalyzer(unittest.TestCase):
    def test_analyze(self):
        grid = UniformGrid((10, 5))

        source = CallbackGenerator(
            callbacks={"Grid": (lambda t: generate_grid(), Info(grid=grid))},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = DebugConsumer(
            inputs={"Input": Info(grid=NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer2 = DebugConsumer(
            inputs={"Input": Info(grid=NoGrid())},
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
