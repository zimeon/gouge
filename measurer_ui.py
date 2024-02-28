"""UI controls for measurer code.

Notes on interactive matplotlib:
https://stackoverflow.com/questions/33707987/matplotlib-button-to-close-a-loop-python
"""

import logging
import sys

global d

def on_click(event):
    """Event handler for mouse button press."""
    print('button=%d, x=%f, y=%f, xdata=%f, ydata=%f' %
          (event.button, event.x, event.y, event.xdata, event.ydata))

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
        d.bar_center_y -= 0.02
    elif (event.key == 'up'):
        logging.warning("Moving center up")
        d.bar_center_y += 0.02
    elif (event.key == 'left'):
        logging.warning("Moving center left")
        d.bar_center_x -= 0.02
    elif (event.key == 'right'):
        logging.warning("Moving center right")
        d.bar_center_x += 0.02
    elif (event.key == '>'):
        logging.warning("Making bar circle bigger")
        d.bar_radius += 0.01
    elif (event.key == '<'):
        logging.warning("Making bar circle smaller")
        d.bar_radius -= 0.01
    elif (event.key == 'right'):
        logging.warning("Moving center right")
        d.bar_center_x += 0.02
    elif (event.key == 'c'):
        d.image_center_x -= d.bar_center_x
        d.image_center_y -= d.bar_center_y
        d.bar_center_x = 0.0
        d.bar_center_y = 0.0
        logging.warning("Set center: [%.3f, %.3f]", d.image_center_x, d.image_center_y)

    else:
        logging.warning('Untrapped keypress: ' + str(event.key))

def setup_ui(fig, display):
    """Set-up UI by attaching event handlers to the figure."""
    global d
    d = display
    # Attach event handlers
    cid1 = fig.canvas.mpl_connect('key_press_event', on_key)
    cid2 = fig.canvas.mpl_connect('button_press_event', on_click)
