# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Threading class for image processing of fibre bundle images. 

@author: Mike Hughes
Applied Optics Group
University of Kent

"""

import sys
sys.path.append('C:\\Users\\AOG\\Dropbox\\Programming\\Python\\pybundle')
import logging
import time
from ImageProcessorThread import ImageProcessorThread
from pybundle import PyBundle
from pybundle import Mosaic
import pybundle
import numpy as np

class BundleProcessor(ImageProcessorThread):
    
    method = None
    mask = None
    crop = None
    filterSize = None
    mosaicing = False
    dualMode = False
    previousImage = None
    
    def __init__(self, inBufferSize, outBufferSize, **kwargs):
        
        self.mosaicing = kwargs.get('mosaic', False)
        
        super().__init__(inBufferSize, outBufferSize, **kwargs)
        
        self.pyb = PyBundle()
        if self.mosaicing is True:
            self.mosaic = Mosaic(1000, resize = 200, boundaryMethod = Mosaic.SCROLL)

                
    def process_frame(self, inputFrame):
        #print("Processing frame")
        outputFrame = inputFrame

        if self.dualMode:
            if self.previousImage is not None:
                way = bool(np.mean(self.previousImage) > np.mean(inputFrame))
                #print(np.mean(self.previousImage))
                #print(np.mean(inputFrame))
                print(way)
                if way is False:
                    outputFrame = inputFrame.astype('float64') - self.previousImage
                    print("in - prev")
                else:
                    outputFrame = self.previousImage - inputFrame.astype('float64')
                    print("prev - in")
                #print(np.mean(outputFrame))
                #outputFrame = (outputFrame - np.min(outputFrame)).astype('uint8')    
            self.previousImage = inputFrame.astype('float64')
            
        t1 = time.perf_counter()
        outputFrame = self.pyb.process(outputFrame)
        #print("Proc:" + str(time.perf_counter() - t1))
        #self.preProcessFrame = outputFrame
        #print(self.mosaicing)
        if self.mosaicing and outputFrame is not None:
            self.mosaic.add(outputFrame)
    
        return outputFrame

    def update_settings(self):
        pass

    def get_mosaic(self):
        return self.mosaic.get_mosaic()
       