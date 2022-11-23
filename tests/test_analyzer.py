import unittest
from datetime import datetime, timedelta

import finam as fm
import numpy as np

from finam_graph.graph import Graph


def generate_grid(grid):
    return np.random.random(grid.data_size).reshape(
        shape=grid.data_shape, order=grid.order
    )


class TestCompAnalyzer(unittest.TestCase):
    def test_analyze(self):
        grid = fm.UniformGrid((10, 5))

        source = fm.modules.CallbackGenerator(
            callbacks={
                "Grid": (lambda t: generate_grid(grid), fm.Info(time=None, grid=grid))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = fm.modules.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer2 = fm.modules.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        grid_to_val = fm.adapters.GridToValue(np.mean)
        lin_interp = fm.adapters.LinearTime()

        composition = fm.Composition([source, consumer, consumer2])
        composition.initialize()

        _ = (
            source.outputs["Grid"]
            >> grid_to_val
            >> lin_interp
            >> consumer.inputs["Input"]
        )

        _ = source.outputs["Grid"] >> consumer2.inputs["Input"]

        graph = Graph(composition, set())
        self.assertEqual(len(graph.components), 3)
        self.assertEqual(len(graph.adapters), 2)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(len(graph.direct_edges), 2)
        self.assertEqual(len(graph.simple_edges), 2)

    def test_analyze_exclude(self):
        grid = fm.UniformGrid((10, 5))

        source = fm.modules.CallbackGenerator(
            callbacks={
                "Grid": (lambda t: generate_grid(grid), fm.Info(time=None, grid=grid))
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = fm.modules.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer2 = fm.modules.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer3 = fm.modules.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        grid_to_val = fm.adapters.GridToValue(np.mean)
        grid_to_val_2 = fm.adapters.GridToValue(np.mean)
        lin_interp = fm.adapters.LinearTime()

        composition = fm.Composition([source, consumer, consumer2, consumer3])
        composition.initialize()

        _ = (
                source.outputs["Grid"]
                >> grid_to_val
                >> lin_interp
                >> consumer.inputs["Input"]
        )

        _ = source.outputs["Grid"] >> grid_to_val_2 >> consumer2.inputs["Input"]
        _ = source.outputs["Grid"] >> consumer3.inputs["Input"]

        graph = Graph(composition, {consumer2})
        self.assertEqual(len(graph.components), 3)
        self.assertEqual(len(graph.adapters), 2)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(len(graph.direct_edges), 2)
        self.assertEqual(len(graph.simple_edges), 2)
