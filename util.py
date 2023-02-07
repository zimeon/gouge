"""Utilites for canoe design."""


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
        return("%s%d\"" % (sign, inches))
    else:
        return("%s%.3f\"" % (sign, x))


def format_feet_inches(x, pos=None):
    """Formatted feet-and-inches string for value x in inches.

    See: https://matplotlib.org/examples/pylab_examples/custom_ticker1.html
    """
    sign = ''
    if (x < 0.0):
        sign = '-'
        x *= -1.0
    feet = x // 12
    inches = x - (12.0 * feet)
    if (abs(x - (feet * 12.0 + int(inches))) < 0.0001):
        return("%s%d'%d\"" % (sign, feet, int(inches)))
    else:
        return("%s%d'%.3f\"" % (sign, feet, inches))


def fill_range(xx, gap=1.0):
    """Return sorted array of points that includes xx and fills gaps larger than gap*1.5."""
    max = 1.5 * gap
    x2 = []
    last_x = None
    for x in sorted(xx):
        if (last_x is None):
            pass
        else:
            while ((x - last_x) > max):
                last_x += gap
                x2.append(last_x)
        x2.append(x)
        last_x = x
    return(x2)


def round_up(x, tolerance=0.001):
    """Round up to the nearest integer, given a certain tolerance."""
    if (x >= 0.0):
        return(int(x + 1.0 - tolerance))
    else:
        return(int(x - tolerance))


def round_down(x, tolerance=0.001):
    """Round down to the nearest integer, given a certain tolerance."""
    if (x >= 0.0):
        return(int(x + tolerance))
    else:
        return(-int(-x + 1.0 - tolerance))
