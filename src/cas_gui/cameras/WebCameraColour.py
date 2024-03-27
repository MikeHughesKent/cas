# -*- coding: utf-8 -*-
"""
Extends WebCamera to return colour images.

@author: Mike Hughes, Applied Optics Group, University of Kent
"""

import cv2 as cv
import time

import numpy as np
from cas_gui.cameras.WebCamera import WebCamera  

        
class WebCameraColour(WebCamera):

          
    def grab_image(self):
        print("grab")
        
        rval, imageData = self.vc.read()
        imageData = cv.cvtColor(imageData, cv.COLOR_BGR2RGB)
        
        return imageData.astype('uint8')


    def is_colour(self):
        return True

if __name__ == "__main__":
    print("Test mode not implemented")