"""UI controls for measurer code.

Notes on interactive matplotlib:
https://stackoverflow.com/questions/33707987/matplotlib-button-to-close-a-loop-python
"""

import logging

global d

def on_click(event):
    """Event handler for mouse button press."""
    print('view=%s: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          (p.view, event.button, event.x, event.y, event.xdata, event.ydata))
    if (p.view == 'sections' and event.button == 3):
        p.select_point_width_profile(event.xdata, event.ydata)
        p.make_plot()


def on_key(event):
    """Event handler for keypress."""
    if (event.key == 'q'):
        logging.warning("Exiting...")
        sys.exit(0)
    #
    #### Controls for moving the bar cicle
    #
    elif (event.key == 'down'):
        logging.warning("Moving center down")
        d.bar_center_y += 1
    elif (event.key == 'up'):
        logging.warning("Moving center up")
        d.bar_center_y -= 1
    elif (event.key == 'e'):
        p.view = 'end'
        logging.warning("Setting end view")
    elif (event.key == 'n'):
        logging.warning("Now adjusting nose angle, 30-80 degrees")
        number_mode = 'nose'
        number_low, number_high = 30.0, 80.0
    elif (event.key == 'j'):
        number_mode = 'jig'
        number_low, number_high = 10.0, 50.0
        logging.warning("Now adjusting jig angle, 10-50 degrees")
    else:
        logging.warning('Untrapped keypress: ' + str(event.key))
    d.make_plot()

def setup_ui(fig, display):
    """Set-up UI by attaching event handlers to the figure."""
    global d
    d = display
    # Attach event handlers
    cid1 = fig.canvas.mpl_connect('key_press_event', on_key)
    cid2 = fig.canvas.mpl_connect('button_press_event', on_click)
