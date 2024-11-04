# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Class for image processing of fibre bundle images. 

@author: Mike Hughes
Applied Optics Group
University of Kent

"""

import sys
import os

file_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(file_dir, '../../../../pyfibrebundle/src')))


import logging
import time

import pybundle
import numpy as np


from pybundle import PyBundle
from pybundle import Mosaic

from cas_gui.threads.image_processor_class import ImageProcessorClass

class BundleProcessor(ImageProcessorClass):
    
    method = None
    mask = None
    crop = None
    filterSize = None
    mosaicing = False
    dualMode = False
    previousImage = None
    
    def __init__(self, **kwargs):
        
        self.mosaicing = kwargs.get('mosaic', False)
        
        super().__init__()
        
        self.pyb = PyBundle()
        if self.mosaicing is True:
            self.mosaic = Mosaic(1000, resize = 200, boundaryMethod = Mosaic.SCROLL)

                
    def process(self, inputFrame):
        outputFrame = inputFrame

        if self.dualMode:

            if self.previousImage is not None:
                inputFrame = inputFrame.astype('float64')
                outputFrame = inputFrame - self.previousImage
                if np.min(outputFrame) < - np.max(outputFrame):
                    outputFrame = -1 * outputFrame
                outputFrame[outputFrame < 0] = 0
            self.previousImage = inputFrame.copy()
        t1 = time.perf_counter()    
        outputFrame = self.pyb.process(outputFrame)
        #print("Proc:" + str(time.perf_counter() - t1))
        #self.preProcessFrame = outputFrame
        #print(self.mosaicing)
        if self.mosaicing and outputFrame is not None:
            self.mosaic.add(outputFrame)
    
        return outputFrame


    def get_mosaic(self):
        if self.mosaicing: 
            return self.mosaic.get_mosaic()
        else:
            return None