"""
A tool to visualize FINAM compositions

.. toctree::
   :hidden:

   self

Graph diagram
=============

.. autosummary::
   :toctree: generated
   :caption: Graph diagram

    GraphDiagram
    GraphColors
    GraphSizes

Graph data
==========

.. autosummary::
   :toctree: generated
   :caption: Graph data

    graph.Graph
"""

from . import graph
from .diagram import GraphColors, GraphDiagram, GraphSizes

try:
    from ._version import __version__
except ModuleNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0.dev0"


__all__ = ["GraphDiagram", "GraphColors", "GraphSizes", "graph"]
