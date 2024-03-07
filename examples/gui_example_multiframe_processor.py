# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Example thread for simple Gaussian filtering of an image. 

To test this thread use GUI_example_multi.py

This subclasses ImageProcessorThread which provides all the core functionality
of the thread, including handling the image queues. We therefore only need
to implement the process_frame function.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

import numpy as np

from ImageProcessorThread import ImageProcessorThread


class AverageProcessor(ImageProcessorThread):
    
       
    def __init__(self, inBufferSize, outBufferSize, **kwargs):
        """ Technically not needed since we are not adding anything, but
        if any additional initialisation is needed, it goes here.
        """
        
        super().__init__(inBufferSize, outBufferSize, **kwargs)        
       
                
    def process_frame(self, inputFrame):
        """ This is where we do the processing.
        """
        
        # If we have a stack of frames, take the average
        if inputFrame.ndim == 3:
            outputFrame = np.mean(inputFrame,2)
        else:
            outputFrame = inputFrame
        
        return outputFrame

   
       