#!/usr/bin/env python3
#
# Test script for interactive manipulation with a fig based on
# https://stackoverflow.com/questions/60877468/how-to-dynamically-update-matplotlib-plot-using-images-instead-of-markers
#
import logging
import matplotlib.pyplot as plt
import random
import matplotlib.image as image
import sys

global d

def get_ax_size(fig, ax):
    '''
    Returns the size of a given axis in pixels

    Args:
       fig (matplotlib fig)
       ax (matplotlib axes)

    '''
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


def get_extent(fig, ax, img, xsize, xpos, ypos):
    '''
    Calculate extent image on a given axes whilst maintaining its aspect ratio

    Args:
        fig (matplotlib fig)
        ax (matplotlib axes)
        img (numpy.ndarray): image data
        xsize (float): size of the x-dimension of object given as fraction of the axes length
        xpos (float): x-coordinate of image given as fraction of axes (0-1)
        ypos (float): y-coordinate of image given as fraction of axes (0-1)

    Returns:
        xmin, xmax, ymin, ymax (float): min and max x & y specifyin gimage extent in axes coodinates

    '''
    img_aspect = img.shape[0] / img.shape[1]
    xrange=ax.get_xlim()[1]-ax.get_xlim()[0]
    yrange=ax.get_ylim()[1]-ax.get_ylim()[0]

    ysize = xsize * img_aspect * get_ax_size(fig,ax)[0]/get_ax_size(fig,ax)[1]

    xsize *= xrange
    ysize *= yrange

    xpos = (xpos*xrange) + ax.get_xlim()[0]
    ypos = (ypos*yrange) + ax.get_ylim()[0]

    return xpos, xpos+xsize, ypos, ypos+ysize

def on_key(event):
    """Event handler for keypress."""
    logging.warning("Keypress: %s", event.key)
    if (event.key == 'q'):
        print("Exiting...")
        sys.exit(0)
    elif (event.key == 'down'):
        d.y -= 0.05
    elif (event.key == 'up'):
        d.y += 0.05
    elif (event.key == 'u'):
        d.line_x += 1.0
    elif (event.key == 'd'):
        d.line_x -= 1.0
    else:
        print('Untrapped keypress: ' + str(event.key))


class InteractiveDisplay():

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'o')
        self.ax.set_xlim(-1.0,1.0)
        self.ax.set_ylim(-1.0,1.0)
        self.ax.grid()
        self.ax.set_aspect('equal', adjustable='box')
        self.fig.canvas.draw()  # Unless we draw something, the aspect has no effect
        # Image
        self.x = 0.0
        self.y = 0.0
        # Line
        self.line_x = 1.0
        # Record elements plotted so we can erase them
        self.elements = []
        # Image
        self.image_file = "flute_photos/robust_1_2_2022.jpg"
        self.img = image.imread(self.image_file)

    def erase(self):
        """Erase all elements from the plot."""
        for element in self.elements:
            print("Removing", element)
            element.remove()
        self.elements = []

    def draw(self):
        """Update the plot based on current data.

        Internally we rely on a global `elements` to store references
        to all objects plotted. These are then removed from the axes
        before we replot the new view.
        """
        self.erase()

        # And now plot current view
        extent=get_extent(self.fig, self.ax, self.img, 1.0, self.x,self.y)
        print(extent)
        self.elements.append(self.ax.imshow(self.img, aspect='auto', extent=extent,
                                            interpolation='none', zorder=0))
        self.elements.append(self.ax.plot([0.0, 1.0], [self.line_x, 0.0],
                                          color="red", linewidth=1)[0])
        self.ax.set_aspect('equal', adjustable='box') # Have to keep doing this!
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def run(self):
        """Run the interactive display."""
        for it in range(100):
            self.draw()
            print(plt.waitforbuttonpress())


plt.ion()
d = InteractiveDisplay()
d.fig.canvas.mpl_connect('key_press_event', on_key)
d.run()
