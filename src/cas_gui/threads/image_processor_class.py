# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Base class for image processor classes. Image processor classes should
aways inherit from this class to maintain future compatibility.


"""

import magicattr

class ImageProcessorClass:    
  
    
    def __init__(self, **kwargs):
        pass
        
                
    def process(self, inputFrame):
        pass
           
                
    def message(self, message, parameter):  

        f = magicattr.get(self, message)
        if callable(f):
            if isinstance(parameter, tuple):
                if len(parameter) == 0:
                    f()
                else:    
                    f(*parameter)    

            else:
                f(parameter)
        else:
            magicattr.set(self, message, parameter)
             