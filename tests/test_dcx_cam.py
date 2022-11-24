# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Test Simulated Camera

@author: Mike Hughes
Applied Optics Group, University of Kent
"""

import context

import matplotlib.pyplot as plt
import time

from SimulatedCamera import SimulatedCamera
from DCXCameraInterface import DCXCameraInterface


filename = "C:\\Users\\AOG\\OneDrive - University of Kent\\Experimental\\Holography\\Off Axis Holography\\Example Data\\01_11_21 example OAH data USAF HeNe Kiralux\\background.tif"
filename = r"test_data\stack_10.tif"


# Test one frame at a time
cam = DCXCameraInterface()

cam.open_camera(0)
#cam.pre_load(10)
cam.set_frame_rate_on()
#cam.disable_frame_rate()   # So we see the actual time to load the image

t1 = time.time()
im = cam.get_image()

print("Single frame acquisition took " + str(time.time() - t1 ))

plt.figure()
plt.imshow(im)

cam.close_camera()

