"""Utilites for gouge design."""

import math
import numpy
from scipy.spatial.transform import Rotation


def unit_vector(v):
    """Unit vector in direction of vector v."""
    return v / numpy.linalg.norm(v)


def rotate_point(point, center, axis, rot):
    """Rotate point about axis at center by rot radians."""
    # Translate point to have coorindinate with origin at center
    p = point - center
    # Use Rodrigues' Rotation to rotate about axis
    #
    # See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.from_mrp.html
    # "MRPs are a 3 dimensional vector co-directional to the axis of rotation
    # and whose magnitude is equal to tan(theta / 4), where theta is the angle
    # of rotation (in radians)"
    mrp = unit_vector(axis) * math.tan(rot / 4.0)
    r_mat = Rotation.from_mrp(mrp).as_matrix()
    pp = numpy.matmul(r_mat, p)
    # Translate back to original coordinate origin
    return pp + center


def format_inches(x, pos=None):
    """Formatted inches string for value x in inches.

    See: https://matplotlib.org/examples/pylab_examples/custom_ticker1.html
    """
    sign = ''
    if (x < 0.0):
        sign = '-'
        x *= -1.0
    inches = int(x)
    if (abs(x - inches) < 0.0001):
        return "%s%d\"" % (sign, inches)
    else:
        return "%s%.3f\"" % (sign, x)
