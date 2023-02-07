"""User interface for model manipulation."""
import logging
import sys

# Notes on interactive matplotlib:
# https://stackoverflow.com/questions/33707987/matplotlib-button-to-close-a-loop-python

global p
global exit_if_confirm

exit_if_confirm = False


def on_click(event):
    """Event handler for mouse button press."""
    print('view=%s: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (p.view, event.button, event.x, event.y, event.xdata, event.ydata))
    if (p.view == 'sections' and event.button == 3):
        p.select_point_width_profile(event.xdata, event.ydata)
        p.make_plot()


def on_key(event):
    """Event handler for keypress."""
    global exit_if_confirm
    STATION_KEYS = "0123456789)!@#$%^&*('"
    if (exit_if_confirm):
        if (event.key == 'y'):
            logging.warn("Exiting.")
            sys.exit(0)
        else:
            logging.warn("Not exiting, continuing.")
            exit_if_confirm = False
    if (event.key == 'q'):
        logging.warn("Exit, are you sure (y/N)?")
        exit_if_confirm = True
    elif (event.key == 'r'):
        logging.warn("Redrawing...")
        p.make_plot(reset=True)
    elif (event.key == 'e'):
        logging.warn("Selecting sections view.")
        p.view = 'sections'
        p.make_plot()
    elif (event.key == 'o'):
        logging.warn("Selecting orthographic view.")
        p.view = 'orthographic'
        p.make_plot()
    elif (event.key in STATION_KEYS):
        station = STATION_KEYS.find(event.key)
        if (station in p.hull.stations):
            logging.warn("Selecting station %d view." % (station))
            p.view = 'station'
            p.station = station
            p.make_plot()
        else:
            logging.warn("No station %d in this model." % (station))
    elif (event.key == 'w'):
        filename = "new.md"
        logging.warn("Writing to %s..." % (filename))
        p.hull.write(filename)
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
    elif (event.key == 'c'):
        logging.warn("Setting breadth interpolation to cubic")
        p.hull.breadth_interpolator_kind = 'cubic'
        p.make_plot(recalc=True)
    elif (event.key == 'l'):
        logging.warn("Setting breadth interpolation to linear")
        p.hull.breadth_interpolator_kind = 'linear'
        p.make_plot(recalc=True)
    elif (event.key == 'C'):
        logging.warn("Setting length interpolation to cubic")
        p.hull.length_interpolator_kind = 'cubic'
        p.make_plot(recalc=True)
    elif (event.key == 'L'):
        logging.warn("Setting length interpolation to linear")
        p.hull.length_interpolator_kind = 'linear'
        p.make_plot(recalc=True)
    elif (event.key == 'S'):
        logging.warn("Summary stats with current interpolation")
        print(p.hull.summary_stats())
    elif (event.key == 'p'):
        plansfile = 'plans.pdf'
        # logging.warn("Printing plans to %s" % (plansfile))
        p.write_plans(plansfile)
    elif (event.key == 'f'):
        logging.warn("Will use feet for length")
        p.use_feet = True
        p.make_plot()
    elif (event.key == 'i'):
        logging.warn("Will use inches for length")
        p.use_feet = False
        p.make_plot()
    else:
        logging.warn('Untrapped keypress: ' + str(event.key))


def setup_ui(fig, plotter):
    """Set-up UI by attaching event handlers to the figure."""
    global p
    p = plotter
    # Attach event handlers
    cid1 = fig.canvas.mpl_connect('key_press_event', on_key)
    cid2 = fig.canvas.mpl_connect('button_press_event', on_click)
