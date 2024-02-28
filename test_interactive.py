#!/usr/bin/env python3
#
# Test script for interactive manipulation with a figure based on
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
       fig (matplotlib figure)
       ax (matplotlib axes)

    '''
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


def get_extent(fig, ax, image_name, xsize, xpos, ypos):
    '''
    Places an image on a given axes whilst maintaining its aspect ratio

    Args:
        fig (matplotlib figure)
        ax (matplotlib axes)
        image_name (string): name of image to place on axes
        xsize(float): size of the x-dimension of object given as fraction of the axes length
        xpos(float): x-coordinate of image given as fraction of axes
        ypos(float): y-coordinate of image given as fraction of axes

    '''
    import matplotlib.image as image

    im = image.imread(image_name)

    xrange=ax.get_xlim()[1]-ax.get_xlim()[0]
    yrange=ax.get_ylim()[1]-ax.get_ylim()[0]

    ysize=(im.shape[0]/im.shape[1])*(xsize*get_ax_size(fig,ax)[0])/get_ax_size(fig,ax)[1]

    xsize *= xrange
    ysize *= yrange

    xpos = (xpos*xrange) + ax.get_xlim()[0]
    ypos = (ypos*yrange) + ax.get_ylim()[0]

    return (xpos,xpos+xsize,ypos,ypos+ysize)

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


class DynamicUpdate():

    def __init__(self):
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[], 'o')
        self.im = []
        self.ax.set_xlim(0,10)
        self.ax.set_ylim(0,10)
        self.ax.grid()
        # Image
        self.x = 0.5
        self.y = 0.5
        # Line
        self.line_x = 10.0

    def draw(self):
        """

        Internally we rely on a global `elements` to store references
        to all objects plotted. These are then removed from the axes
        before we replot the new view.
        """
        global elements

        image_file = "flute_photos/robust_1_2_2022.jpg"
        im = image.imread(image_file)

        for element in elements:
            print("Removing", element)
            element.remove()
        elements = []
        extent=get_extent(self.figure,self.ax,image_file,0.1,self.x,self.y)
        print(extent)
        elements.append(self.ax.imshow(im,aspect='auto',extent=extent,interpolation='none', zorder=0 ))
        elements.append(self.ax.plot([0.0, 10.0], [self.line_x, 0.0], color="red", linewidth=1)[0])

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def run(self):
        import numpy as np
        import time
        xdata = np.arange(10)/10
        ydata = np.zeros(10)
        for it in range(100):
            self.draw()
            print(plt.waitforbuttonpress())


plt.ion()
elements=[]
d = DynamicUpdate()
d.figure.canvas.mpl_connect('key_press_event', on_key)
d.run()
