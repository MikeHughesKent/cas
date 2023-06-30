# -*- coding: utf-8 -*-
"""
Created on Sun Jun 20 07:28:31 2021

@author: AOG
"""

import cv2 as cv
import time

import numpy as np
from GenericCamera import GenericCameraInterface  
    
        
class WebCamera(GenericCameraInterface):

    exposure = 0              

    
    def __init__(self):
        pass
        
        
            
        
    def get_camera_list(self):
        return None
        
        
    def open_camera(self, camNum):
        self.vc = cv.VideoCapture(1)

        
              
        
    def close_camera(self):

        self.vc.release()
        
    def dispose(self):
        del(self.sdk)
               
        
    def get_image(self):
        
        rval, imageData = self.vc.read()
        imageData = np.mean(imageData, 2).astype('uint8')
        
        return imageData


   
    def set_frame_rate_on(self):
        
       
        return True
    
    def get_exposure(self):
        return self.exposure #self.vc.get(cv.CAP_PROP_EXPOSURE)
        
    def get_exposure_range(self):
        #r = self.camera.exposure_time_range_us
        
        return -10,0
   
    def set_exposure(self, exposure):
        print(exposure)
        self.vc.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.vc.set(cv.CAP_PROP_EXPOSURE, exposure) 
        self.exposure = exposure
        return True    
        

if __name__ == "__main__":
    print("Test mode not implemented")