import numpy as np
from datetime import datetime, timedelta

from finam.adapters import base, time
from finam.core.interfaces import ComponentStatus
from finam.core.schedule import Composition
from finam.core.sdk import ATimeComponent, Input
from finam.data.grid import Grid, GridSpec
from finam.modules.generators import CallbackGenerator

from finam_graph.diagram import GraphDiagram


class MockupComponent(ATimeComponent):
    def __init__(self, start, step):
        super(MockupComponent, self).__init__()
        self._time = start
        self._step = step
        self._status = ComponentStatus.CREATED

    def initialize(self):
        super().initialize()
        self._inputs["Input"] = Input()
        self._status = ComponentStatus.INITIALIZED

    def connect(self):
        super().connect()
        self._status = ComponentStatus.CONNECTED

    def validate(self):
        super().validate()
        self._status = ComponentStatus.VALIDATED

    def update(self):
        super().update()
        self._time += self._step
        self._status = ComponentStatus.UPDATED

    def finalize(self):
        super().finalize()
        self._status = ComponentStatus.FINALIZED


def generate_grid():
    return Grid(GridSpec(10, 5), data=np.random.random(50))


if __name__ == "__main__":
    source = CallbackGenerator(
        callbacks={
            "Grid": lambda t: generate_grid(),
            "Scalar": lambda t: np.random.random(1)[0],
        },
        start=datetime(2000, 1, 1),
        step=timedelta(days=7),
    )
    consumer = MockupComponent(start=datetime(2000, 1, 1), step=timedelta(days=1))
    consumer2 = MockupComponent(start=datetime(2000, 1, 1), step=timedelta(days=1))
    consumer3 = MockupComponent(start=datetime(2000, 1, 1), step=timedelta(days=1))

    grid_to_val = base.GridToValue(np.mean)
    grid_to_val2 = base.GridToValue(np.mean)
    lin_interp = time.LinearInterpolation()
    lin_interp2 = time.LinearInterpolation()

    composition = Composition([source, consumer, consumer2, consumer3])
    composition.initialize()

    _ = source.outputs["Grid"] >> grid_to_val >> lin_interp >> consumer.inputs["Input"]

    _ = source.outputs["Grid"] >> grid_to_val2 >> consumer2.inputs["Input"]

    _ = source.outputs["Scalar"] >> lin_interp2 >> consumer3.inputs["Input"]

    pos = {
        source: (0, 2),
        grid_to_val: (1, 2),
        lin_interp: (2, 2),
        consumer: (3, 2),
        grid_to_val2: (1, 1),
        consumer2: (2, 1),
        lin_interp2: (1, 3),
        consumer3: (2, 3),
    }

    GraphDiagram().draw(composition, save_path="examples/graph.svg")
