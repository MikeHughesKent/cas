# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 18:17:10 2022

@author: AOG
"""
import context

from ImageAcquisitionThread import ImageAcquisitionThread

import matplotlib.pyplot as plt

import time


filename = r"test_data\stack_10.tif"

imThread = ImageAcquisitionThread('SimulatedCamera', 100, filename = filename)
imThread.get_camera().pre_load(10)

imThread.start()

try:
    while True:
        if imThread.is_image_ready():
            frame = imThread.get_next_image()
            print(frame)
                
except KeyboardInterrupt:
    pass