# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Base class for image processor classes. Image processor classes should
aways inherit from this class to maintain future compatibility.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""


class ImageProcessorClass:    
  
    
    def __init__(self, **kwargs):
        pass
        
                
    def process(self, inputFrame):
        pass
    
    
    
                
    def message(self, message, parameter):  

        f = getattr(self, message)
        if isinstance(parameter, tuple):
            f(*parameter)    
        elif parameter is None:
            f()
        else:
            f(parameter)
   
       