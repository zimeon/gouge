"""User interface for model manipulation in standalone application."""
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
    STATION_KEYS = "0123456789)!@#$%^&*('"
    if (event.key == 'q'):
        logging.warn("Exiting...")
        sys.exit(0)
    elif (event.key == 'a'):
        p.show_grinding_edge_arrows = not p.show_grinding_edge_arrows
        logging.warn("Setting show_grinding_edge_arrows: %s",
                     p.show_grinding_edge_arrows)
        p.make_plot(reset=True)
    else:
        logging.warn('Untrapped keypress: ' + str(event.key))


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
    q - quit
    """)
