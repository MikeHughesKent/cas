# -*- coding: utf-8 -*-
"""
Examples of how to use a simulated camera in CAS.

@author: Mike Hughes, Applied Optics Group, University of Kent
"""

import context
import time
import math
import matplotlib.pyplot as plt
from pathlib import Path

from SimulatedCamera import SimulatedCamera

# This is the tif file containing images to be used a simulated camera feed
filename = Path('data/vid_example.tif')

# Create an instance of the simulated camera
cam = SimulatedCamera(filename = filename)

# Open the camera. The argument is the camera number, for compatibility with
# camera interfaces that support multiple cameras, it is ignored here for the
# simulated camera
cam.open_camera(0)


# Pre-load frames into memory. This is not essential, but will prevent file 
# i/o speed limiting the frame rate. (try commenting this line and see the
# drop in measured frame rate). Passing -1 loads all the frames. Pass a number
# to load only that number of frames. The simulated camera will then stream
# only those pre-loaded frames.
cam.pre_load(-1)


# We wait to ensure we have an image available
time.sleep(0.5)


# Grab the next image
img = cam.get_image()


# Display the image
if img is not None:
    plt.imshow(img, cmap = 'gray')
else:
    print ("No image was received.")


# Set the frame rate to 50 fps
frame_rate = 100
cam.set_frame_rate(frame_rate)

# Wait until we have a frame to avoid messing up frame rate measurement below
while cam.get_image() is None:
    pass

# Now we will grab some images in succession and check that they are served
# at the requested frame rate
nFrames = 50

start_time = time.perf_counter()
for iImage in range(0,nFrames):
    while cam.get_image() is None:
        pass
end_time =  time.perf_counter()

measured_frame_rate = round(nFrames / (end_time-start_time))
print(f"Requested frame rate is {frame_rate} fps. \nMeasured frame rate is {measured_frame_rate} fps.")   


# Close the camera (not strictly necessary for simulated cameras, for compatibility with real cameras.)
cam.close_camera()
