# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Test Kiralux Camera

@author: Mike Hughes
Applied Optics Group, University of Kent
"""

import context

import matplotlib.pyplot as plt

from KiraluxCamera import KiraluxCamera
import sys

sys.path.append(r"\\dll64_lib")

cam = KiraluxCamera()

cam.open_camera(0)

im = cam.get_image()
im2 = cam.get_image()

plt.figure()
plt.imshow(im)

cam.close_camera()



