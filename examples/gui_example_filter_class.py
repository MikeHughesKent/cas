# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Example thread for simple Gaussian filtering of an image. 

To test this thread use GUI_example.py

This subclasses ImageProcessorThread which provides all the core functionality
of the thread, including handling the image queues. We therefore only need
to implement the process_frame function.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

from scipy.ndimage import gaussian_filter


from ImageProcessorClass import ImageProcessorClass


class FilterClass(ImageProcessorClass):
    
    applyFilter = False
    filterSize = None   
    
    def __init__(self, applyFilter = False, filterSize = None):
        """ Technically not needed since we are not adding anything, but
        if any additional initialisation is needed, it goes here.
        """
        self.applyFilter = applyFilter
        self.filterSize = filterSize
        
                
    def process(self, inputFrame):
        """ This is where we do the processing.
        """
        if self.applyFilter and self.filterSize > 0:
            outputFrame = gaussian_filter(inputFrame, self.filterSize)
        else:
            outputFrame = inputFrame
        return outputFrame
   
   
       