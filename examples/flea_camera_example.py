# -*- coding: utf-8 -*-
"""
Example of how to use control and grab images from a Flea (or other FLIR) camera in CAS.

@author: Mike Hughes, Applied Optics Group, University of Kent
"""

import context
import time
import math
import matplotlib.pyplot as plt
from pathlib import Path

from FleaCameraInterface import FleaCameraInterface


# Create an instance of the camera interface
cam = FleaCameraInterface()

# Open the camera. The argument is the camera number.
cam.open_camera(0)


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


# Find out allowed values of exposure
min_gain, max_gain = cam.get_gain_range()
print(f"Gain can be between {min_gain} and {max_gain}.")


# Find out allowed values of gain
min_exp, max_exp = cam.get_exposure_range()
print(f"Exposure can be between {min_exp} and {max_exp}.")


# Set the exposure and gain
cam.set_exposure(10000)
print(f"Exposure is now {cam.get_exposure()}.")

cam.set_gain(10)
print(f"Gain is now {cam.get_gain()}.")


# Enable the trigger. If there is no trigger signal this will timout
cam.set_trigger_mode(True)
timeout = 100
img = cam.get_image(timeout = timeout)
if img is None:
    print("Triggering timed out.")
else:
    print("Triggered image acquired.")    



# Close the camera 
cam.close_camera()
