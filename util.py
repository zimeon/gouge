"""Utilites for gouge design."""


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
