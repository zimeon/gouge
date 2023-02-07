"""Routines to help produce fair curves and interpolations.

Goal is to have routines that work "OK" under all circumstances,
ideally never worse than a linear interpolation.

We are working in real space for canoes that are about 15' long
or 180.0 units (inches) and thus measurements of less than 0.1"
or certainly of less than 0.01" are not significant (because we
can't produce them reliably).

Sources:

Nice set of lecture notes:
http://www.uio.no/studier/emner/matnat/ifi/INF-MAT5340/v05/undervisningsmateriale/

Book with a number of introductory chapters:
http://epubs.siam.org/doi/book/10.1137/1.9781611971521

https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.CubicSpline.html

"""

import logging
import math
import numpy as np
from scipy.interpolate import CubicSpline


class FairCurve(object):
    """Curvey curve, who is the fairest of them all? Why I am."""

    default_step = 0.1  # assume unit = inches

    def __init__(self, xy, bc_type='natural', mid_index=None):
        """Initialize fair curve with point set xy."""
        self.xy = list(xy)  # Record a list even if generator supplied
        self.mid_index = mid_index
        if (len(self.xy) == 0):
            raise Exception("Empty array")
        if (len(self.xy) == 1):
            # Duplicate point
            self.xy = [self.xy[0], self.xy[0]]
        self.len = len(self.xy)
        self.bc_type = bc_type
        self.spline = CubicSpline(range(0, self.len), self.xy,
                                  bc_type=self.bc_type)

    def dist(self, i):
        """Real space distance between points i and i+1."""
        dx = self.xy[i][0] - self.xy[i + 1][0]
        dy = self.xy[i][1] - self.xy[i + 1][1]
        return(math.sqrt(dx * dx + dy * dy))

    def parameter_range(self, start=None, end=None, step=None):
        """Generator for the parameter of the curve with given step."""
        if (start is None):
            start = 0
        if (end is None):
            end = self.len - 1
        if (step is None):
            step = self.default_step
        if (start > end):
            raise Exception("Must have start before or equal to end!")
        for i in range(start, end):
            steps = math.ceil(self.dist(i) / step)
            if (steps < 2):
                ar = [0.0]
            else:
                ar = np.linspace(0.0, 1.0, steps, endpoint=False)
            for di in ar:
                yield(i + di)
        yield(end)

    def curve(self, start=None, end=None, step=None):
        """Interpolate curve with real-space step distance of approx step."""
        xx = []
        yy = []
        logging.debug('FairCurve.curve(..)')
        for i in self.parameter_range(start, end, step):
            x, y = self.spline(i)
            xx.append(x)
            yy.append(y)
            if (i == int(i)):
                logging.debug("  i=%g |x'''|=%.3f" % (i, math.sqrt(sum([x*x for x in self.spline(i, 3)]))))
        return(xx, yy)

    def length(self, start=0, end=None, step=None):
        """Length of curve from start to end point (default all curve)."""
        l = 0.0
        if (end is None):
            end = self.len - 1
        if (start > end):
            start, end = end, start
        last_x = None
        last_y = None
        for i in self.parameter_range(start=start, end=end, step=None):
            x, y = self.spline(i)
            if (last_x is not None):
                l += math.sqrt((x - last_x) ** 2 + (y - last_y) ** 2)
            last_x, last_y = x, y
        # FIXME - can we use l = self.spline.integrate(start,)
        return(l)

    def x(self, y, start=None, end=None):
        """Find x value corresponding to y.

        Since the curve may by be a function of y the value of x may
        not be well-defined. Attempt to find _a_ value with bias toward
        the start of the curve.
        """
        last_x = None
        last_y = None
        for i in self.parameter_range(start, end):
            this_x, this_y = self.spline(i)
            if (this_y == y):
                return(this_x)
            elif (last_y is not None):
                if ((last_y >= y and y >= this_y) or (this_y >= y and y >= last_y)):
                    # Desired y in this range, do linear interp
                    x = this_x + (last_x - this_x) * (y - this_y) / (last_y - this_y)
                    # logging.warn("Got x=%.2f at y=%.2f" % (x,y))
                    return(x)
            last_x = this_x
            last_y = this_y
        raise ValueError("Failed to find x at y=%.2f" % y)

    def y(self, x, start=None, end=None):
        """Find y value corresponding to x.

        Since the curve may by be a function of x the value of y may
        not be well-defined. Attempt to find _a_ value with bias toward
        the start of the curve.
        """
        last_x = None
        last_y = None
        for i in self.parameter_range(start, end):
            this_x, this_y = self.spline(i)
            if (this_x == x):
                return(this_y)
            elif (last_x is not None):
                if ((last_x >= x and x >= this_x) or (this_x >= x and x >= last_x)):
                    # Desired x in this range, do linear interp
                    y = this_y + (last_y - this_y) * (x - this_x) / (last_x - this_x)
                    return(y)
            last_x = this_x
            last_y = this_y
        raise ValueError("Failed to find y at x=%.2f" % x)
