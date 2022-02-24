import unittest
import numpy as np
from datetime import datetime, timedelta

from finam.adapters import base, time
from finam.core.interfaces import ComponentStatus
from finam.core.schedule import Composition
from finam.core.sdk import ATimeComponent, Input
from finam.data.grid import Grid, GridSpec
from finam.modules.generators import CallbackGenerator

from finam_graph.comp_analyzer import CompAnalyzer


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


class TestCompAnalyzer(unittest.TestCase):
    def test_analyze(self):
        source = CallbackGenerator(
            callbacks={"Grid": lambda t: generate_grid()},
            start=datetime(2000, 1, 1),
            step=timedelta(days=7),
        )

        cons = MockupComponent(start=datetime(2000, 1, 1), step=timedelta(days=1))

        composition = Composition([source, cons])
        composition.initialize()

        _ = (
            source.outputs["Grid"]
            >> base.GridToValue(np.mean)
            >> time.LinearInterpolation()
            >> cons.inputs["Input"]
        )

        composition.run(datetime(2000, 7, 1))

        analyzer = CompAnalyzer(composition)

        comps, adapters, edges = analyzer.get_graph()

        self.assertEqual(len(comps), 2)
        self.assertEqual(len(adapters), 2)
        self.assertEqual(len(edges), 3)
