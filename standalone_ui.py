"""User interface for model manipulation in standalone application."""
import math
import logging
import sys

# Notes on interactive matplotlib:
# https://stackoverflow.com/questions/33707987/matplotlib-button-to-close-a-loop-python

global p
global number_mode
global number_low
global number_high

number_mode = None


def on_click(event):
    """Event handler for mouse button press."""
    print('view=%s: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (p.view, event.button, event.x, event.y, event.xdata, event.ydata))
    if (p.view == 'sections' and event.button == 3):
        p.select_point_width_profile(event.xdata, event.ydata)
        p.make_plot()


def on_key(event):
    """Event handler for keypress."""
    global number_mode
    global number_low
    global number_high
    reset = False
    if (event.key == 'q'):
        logging.warn("Exiting...")
        sys.exit(0)
    elif (event.key == 'a'):
        p.show_grinding_edge_arrows = not p.show_grinding_edge_arrows
        logging.warn("Setting show_grinding_edge_arrows: %s",
                     p.show_grinding_edge_arrows)
    elif (event.key == 'p'):
        p.view = 'profile'
        logging.warn("Setting profile view")
    elif (event.key == 'l'):
        p.view = 'plan'
        logging.warn("Setting plan view")
    elif (event.key == 'e'):
        p.view = 'end'
        logging.warn("Setting end view")
    elif (event.key == 'n'):
        logging.warn("Now adjusting nose angle, 30-80 degrees")
        number_mode = 'nose'
        number_low, number_high = 30.0, 80.0
    elif (event.key == 'j'):
        number_mode = 'jig'
        number_low, number_high = 10.0, 50.0
        logging.warn("Now adjusting jig angle, 10-50 degrees")
    elif (event.key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
        value = number_low + int(event.key) / 9.0 * (number_high - number_low)
        logging.warn("Setting %s angle to %.1f", number_mode, value)
        if number_mode == 'nose':
            p.gouge.nose_angle = math.radians(value)
        elif number_mode == 'jig':
            p.gouge.jig_angle = math.radians(value)
        reset = True
    else:
        logging.warn('Untrapped keypress: ' + str(event.key))
    p.make_plot(reset=reset)


def setup_ui(fig, plotter):
    """Set-up UI by attaching event handlers to the figure."""
    global p
    p = plotter
    # Attach event handlers
    cid1 = fig.canvas.mpl_connect('key_press_event', on_key)
    cid2 = fig.canvas.mpl_connect('button_press_event', on_click)
    # Show documentation
    print("""Key commands (while plot window in focus):
    a - toggle display of cutting edge arrows
    Views:
    p - profile
    l - plan
    e - end
    Adjust parameters:
    n - Adjust nose angle (use keys 0-9)
    j - Adjust jig angle (use keys 0-9)
    Misc:
    q - quit
    """)
