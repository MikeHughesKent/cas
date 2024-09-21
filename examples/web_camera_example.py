# -*- coding: utf-8 -*-
"""
Example of how to use control and grab images from a web-camera in CAS.

@author: Mike Hughes, Applied Optics Group, University of Kent
"""

import context
import time
import math
import matplotlib.pyplot as plt
from pathlib import Path

from cas_gui.cameras.WebCamera import WebCamera

# This is the tif file containing images to be used a simulated camera feed
filename = Path('data/vid_example.tif')

# Create an instance of the web camera interface
cam = WebCamera()

# Open the camera. The argument is the camera number.
print("Opening Camera (may take a few seconds)...")
cam.open_camera(0)
print("Camera Open")


# Grab the next image
img = cam.get_image()


# Display the image
if img is not None:
    plt.imshow(img, cmap = 'gray')
else:
    print ("No image was received.")


# Set the frame rate to 10 fps
frame_rate = 10
cam.set_frame_rate(frame_rate)

# Wait until we have a frame to avoid messing up frame rate measurement below
print("Waiting for first frame...")
while cam.get_image() is None:
     pass

# Now we will grab some images in succession and check that they are served
# at the requested frame rate
nFrames = 10
print(f"Grabing {nFrames} frames ...")
start_time = time.perf_counter()
for iImage in range(0,nFrames):
    while cam.get_image() is None:
        pass
end_time =  time.perf_counter()

measured_frame_rate = round(nFrames / (end_time-start_time))
print(f"Requested frame rate is {frame_rate} fps. \nMeasured frame rate is {measured_frame_rate} fps.")   


# Close the camera 
cam.close_camera()
