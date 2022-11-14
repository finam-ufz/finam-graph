from datetime import datetime, timedelta

import finam as fm
import numpy as np

from finam_graph import GraphDiagram


def generate_grid(grid_spec):
    return np.random.random(grid_spec.data_size).reshape(
        shape=grid_spec.data_shape, order=grid_spec.order
    )


if __name__ == "__main__":
    grid = fm.UniformGrid((10, 5))

    source = fm.modules.CallbackGenerator(
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
    grid_to_val2 = fm.adapters.GridToValue(np.mean)
    lin_interp = fm.adapters.LinearTime()

    composition = fm.Composition([source, consumer, consumer2, consumer3])
    composition.initialize()

    _ = source.outputs["Grid"] >> grid_to_val >> lin_interp >> consumer.inputs["Input"]

    _ = source.outputs["Grid"] >> grid_to_val2 >> consumer2.inputs["Input"]

    _ = source.outputs["Scalar"] >> consumer3.inputs["Input"]

    # With automatic placement
    GraphDiagram().draw(
        composition,
        labels={
            source: "Source",
            grid_to_val: "G2V",
            grid_to_val2: "G2V",
        },
        seed=5,
        # save_path="examples/graph.svg"
    )

    # With manual placement
    """
    pos = {
        source: (0, 2),
        grid_to_val: (1, 2),
        lin_interp: (2, 2),
        consumer: (3, 2),
        grid_to_val2: (1, 1),
        consumer2: (2, 1),
        consumer3: (2, 3),
    }
    GraphDiagram().draw(composition, positions=pos, save_path="examples/graph.svg")
    """
