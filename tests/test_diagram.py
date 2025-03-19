import os
import unittest
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import finam as fm
import numpy as np

from finam_graph import GraphDiagram


def generate_grid(grid):
    return np.random.random(grid.data_size).reshape(
        shape=grid.data_shape, order=grid.order
    )


class TestDiagram(unittest.TestCase):
    def test_diagram(self):
        grid = fm.UniformGrid((10, 5))

        source = fm.components.CallbackGenerator(
            callbacks={
                "Grid": (lambda t: generate_grid(grid), fm.Info(time=None, grid=grid)),
                "Scalar": (
                    lambda t: np.random.random(1)[0],
                    fm.Info(time=None, grid=fm.NoGrid()),
                ),
            },
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )
        consumer = fm.components.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer2 = fm.components.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )
        consumer3 = fm.components.DebugConsumer(
            inputs={"Input": fm.Info(time=None, grid=fm.NoGrid())},
            start=datetime(2000, 1, 1),
            step=timedelta(days=1),
        )

        grid_to_val = fm.adapters.GridToValue(np.mean)
        grid_to_val2 = fm.adapters.GridToValue(np.mean)
        lin_interp = fm.adapters.LinearTime()

        composition = fm.Composition([source, consumer, consumer2, consumer3])

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
                composition,
                excluded={consumer2},
                labels={
                    source: "Source",
                    source.outputs["Grid"]: "G",
                    consumer2.inputs["Input"]: "V",
                    grid_to_val2: "G2V",
                },
                block=False,
                show=False,
                seed=5,
                save_path=file_path,
            )


if __name__ == "__main__":
    unittest.main()
