"""User interface for model manipulation."""
import logging
import sys

# Notes on interactive matplotlib:
# https://stackoverflow.com/questions/33707987/matplotlib-button-to-close-a-loop-python

global p


def on_click(event):
    """Event handler for mouse button press."""
    print('view=%s: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (p.view, event.button, event.x, event.y, event.xdata, event.ydata))
    if (p.view == 'sections' and event.button == 3):
        p.select_point_width_profile(event.xdata, event.ydata)
        p.make_plot()


def on_key(event):
    """Event handler for keypress."""
    STATION_KEYS = "0123456789)!@#$%^&*('"
    if (event.key == 'q' or event.key == 'escape'):
        logging.warn("Exiting...")
        sys.exit(0)
    elif (event.key == 'r'):
        logging.warn("Redrawing...")
        p.make_plot(reset=True)
    elif (event.key in STATION_KEYS):
        station = STATION_KEYS.find(event.key)
        if (station in p.hull.stations):
            logging.warn("Selecting station %d view." % (station))
            p.view = 'station'
            p.station = station
            p.make_plot()
        else:
            logging.warn("No station %d in this model." % (station))
    elif (event.key == 'm'):
        if (p.selected is not None):
            logging.warn("Move left big")
            p.move_point_width_profile(dx=-0.1)
            p.make_plot()
    elif (event.key == ','):
        if (p.selected is not None):
            logging.warn("Move left")
            p.move_point_width_profile(dx=-0.01)
            p.make_plot()
    elif (event.key == '.'):
        if (p.selected is not None):
            logging.warn("Move right")
            p.move_point_width_profile(dx=0.01)
            p.make_plot()
    elif (event.key == '/'):
        if (p.selected is not None):
            logging.warn("Move right big")
            p.move_point_width_profile(dx=0.1)
            p.make_plot()
    elif (event.key == 'a'):
        if (p.selected is not None):
            logging.warn("Move up")
            p.move_point_width_profile(dy=0.01)
            p.make_plot()
    elif (event.key == 'z'):
        if (p.selected is not None):
            logging.warn("Move down")
            p.move_point_width_profile(dy=-0.01)
            p.make_plot()
    else:
        logging.warn('Untrapped keypress: ' + str(event.key))


def setup_ui(fig, plotter):
    """Build UI by attaching event handlers to the figure."""
    global p
    p = plotter
    # Attach event handlers
    cid1 = fig.canvas.mpl_connect('key_press_event', on_key)
    cid2 = fig.canvas.mpl_connect('button_press_event', on_click)
