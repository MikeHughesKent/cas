# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Threading class for image processing for use in GUIs or or 
multi-threading applications. Sub-class and implement __process_frame
to make a custom image processor.

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

#import queue
#import threading
import multiprocessing
import time
import logging
from ImageProcessorProcess import ImageProcessorProcess
from ImageProcessorHandler import ImageProcessorHandler
#import BundleProcessorProcess

from pybundle import PyBundle
from pybundle import Mosaic
import pybundle

class BundleProcessorHandler(ImageProcessorHandler):
    
    def __init__(self, inBufferSize, outBufferSize, **kwargs):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
 
        super().__init__(inBufferSize, outBufferSize, **kwargs)
        
        self.pyb = PyBundle()
               
        self.updateQueue.put(self.pyb)
        
        self.process = ImageProcessorProcess(self.inputQueue, self.outputQueue, self.updateQueue)
        self.process.start()
                                              
        
    def update_settings(self):
        self.updateQueue.put(self.pyb)
       
   

