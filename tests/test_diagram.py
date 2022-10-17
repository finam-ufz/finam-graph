import os
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import numpy as np
from finam import Composition, Info, NoGrid, UniformGrid
from finam.adapters import base, time
from finam.modules.debug import DebugConsumer
from finam.modules.generators import CallbackGenerator

from finam_graph import GraphDiagram


def generate_grid(grid):
    return np.random.random(grid.data_size).reshape(
        shape=grid.data_shape, order=grid.order
    )


class TestDiagram(unittest.TestCase):
    def test_diagram(self):

        grid = UniformGrid((10, 5))

        source = CallbackGenerator(
            callbacks={
                "Grid": (lambda t: generate_grid(grid), Info(grid=grid)),
                "Scalar": (lambda t: np.random.random(1)[0], Info(grid=NoGrid())),
            },
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
        consumer3 = DebugConsumer(
            inputs={"Input": Info(grid=NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        grid_to_val = base.GridToValue(np.mean)
        grid_to_val2 = base.GridToValue(np.mean)
        lin_interp = time.LinearInterpolation()

        composition = Composition([source, consumer, consumer2, consumer3])
        composition.initialize()

        _ = (
            source.outputs["Grid"]
            >> grid_to_val
            >> lin_interp
            >> consumer.inputs["Input"]
        )

        _ = source.outputs["Grid"] >> grid_to_val2 >> consumer2.inputs["Input"]

        _ = source.outputs["Scalar"] >> consumer3.inputs["Input"]

        with TemporaryDirectory() as tmp:
            file_path = os.path.join(tmp, "test.svg")
            GraphDiagram().draw(
                composition, block=False, show=False, seed=5, save_path=file_path
            )
