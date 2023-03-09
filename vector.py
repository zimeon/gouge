"""Vectors Utils."""

import math
import numpy


def unit_vector(v):
    """Unit vector in direction of vector v."""
    return v / numpy.linalg.norm(v)
