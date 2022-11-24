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
sys.path.append(os.path.abspath("..\\src\\widgets"))
sys.path.append(os.path.abspath("..\\src\\cameras"))
sys.path.append(os.path.abspath("..\\src\\threads"))

from BundleProcessor import BundleProcessor


imageProcessor = BundleProcessor(10,10, mosaic = True)



# Load in a fibre bundle endomicroscopy video
cap = cv.VideoCapture('data/raw_example.avi')
ret, img = cap.read()
img = img[:,:,0]
nFrames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))


# Load in the calibration image
calibImg = cv.imread('data/raw_example_calib.tif')[:,:,0]

ret, img = cap.read()
img = img[:,:,0]
imgStack = np.zeros([nFrames, np.shape(img)[0], np.shape(img)[1] ], dtype='uint8'  ) 
imgStack[0,:,:] = img


# Load video frames
for i in range(1,nFrames):
    cap.set(cv.CAP_PROP_POS_FRAMES, i)
    ret, img = cap.read()
    img = img[:,:,0]
    imgStack[i,:,:] = img


for i in range(1,nFrames):
    imageProcessor.add_image(imgStack[i,:,:])
    time.sleep(0.1)
    currentProcessedImage = imageProcessor.get_latest_processed_image()
    
    
imageProcessor.stop() 
