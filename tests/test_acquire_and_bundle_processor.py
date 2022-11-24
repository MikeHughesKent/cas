# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 16:27:13 2022

@author: AOG
"""



import cv2 as cv
#import pybundle
import numpy as np
import time
import sys
import os
import math
sys.path.append(os.path.abspath("..\\src\\widgets"))
sys.path.append(os.path.abspath("..\\src\\cameras"))
sys.path.append(os.path.abspath("..\\src\\threads"))

from BundleProcessor import BundleProcessor
from ImageAcquisitionThread import ImageAcquisitionThread

imageProcessor = BundleProcessor(10,10, mosaic = True)
imageProcessor.pyb.set_core_method(imageProcessor.pyb.FILTER)
imageProcessor.pyb.set_filter_size(1.4)
imageProcessor.pyb.set_bundle_loc((600,500,450))
imageProcessor.pyb.set_auto_mask(None)

rawImageBufferSize = 10

sourceFilename = (r"..\\..\\endomicroscope\\test\\data\\raw_example.tif")
imageThread = ImageAcquisitionThread('SimulatedCamera', rawImageBufferSize, filename=sourceFilename )
imageThread.get_camera().pre_load(100)
print("images pre-loaded")

imageThread.cam.set_frame_rate(100)
imageThread.start()
#imageProcessor.start()

nFrames = 100

t1 = time.perf_counter()
for i in range(1,nFrames):
    while imageThread.is_image_ready() is False:
        time.sleep(0.0001)
    a = imageThread.get_next_image()
    #print("n" + str(i))
    #print(imageThread.get_actual_fps())
    #print("Processed frame:" + str(i))
    # print(imageProcessor.is_image_ready())
    # imageProcessor.add_image(imgStack[i,:,:])
    # time.sleep(0.01)
    # currentProcessedImage = imageProcessor.get_latest_processed_image()
print((time.perf_counter() - t1) / nFrames)    
    
imageProcessor.stop() 
imageThread.stop()
