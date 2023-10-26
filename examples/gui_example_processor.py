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


from ImageProcessorThread import ImageProcessorThread


class FilterProcessor(ImageProcessorThread):
    
    applyFilter = False
    filterSize = None
   
    
    def __init__(self, inBufferSize, outBufferSize, **kwargs):
        """ Technically not needed since we are not adding anything, but
        if any additional initialisation is needed, it goes here.
        """
        
        super().__init__(inBufferSize, outBufferSize, **kwargs)        
       
                
    def process_frame(self, inputFrame):
        """ This is where we do the processing.
        """
        if self.applyFilter and self.filterSize > 0:
            outputFrame = gaussian_filter(inputFrame, self.filterSize)
        else:
            outputFrame = inputFrame
        return outputFrame

   
       