# -*- coding: utf-8 -*-
"""
CAS: Camera Acquisition System

Camera interface for webcameras, returning monochrome images. Uses OpenCV.
"""

import time

import numpy as np
import cv2 as cv

from cas_gui.cameras.GenericCamera import GenericCameraInterface  
    
        
class WebCamera(GenericCameraInterface):    
  
    
    def __init__(self):
        
        self.lastImageTime = time.perf_counter()
        self.lastImageTimeAdjusted = self.lastImageTime
        self.fps = 20
        self.frameRateEnabled = True
        self.exposure = -10        
        
        
    def get_camera_list(self):
        return None
        
        
    def open_camera(self, camNum):
        self.vc = cv.VideoCapture(camNum)
        self.camera_open = True

              
    def close_camera(self):
        self.vc.release()
        
    def dispose(self):
        pass               
           

    def get_image(self):
    
       # Calculate delay needed to achieve desired frame rate
       if self.fps > 0:
           desiredWait = 1/self.fps
       else:
           desiredWait = 100000
       currentTime = time.perf_counter()
       waitNeeded = desiredWait - (currentTime - self.lastImageTimeAdjusted)
       
       
       # Only return an image if enough time has passed since the last image
       # to match the frame rate, otherwise return None
       if waitNeeded < 0:
           self.lastImageTime = time.perf_counter()
           
           # We keep a record of the last time minus the wait needed. This way,
           # when we have waited too long (i.e. waitNeeded << 0) we add something
           # to the lastImageTimeAdjusted which has the effect of making the next
           # wait needed shorter. This lead to a more accurate frame rate.
           self.lastImageTimeAdjusted = self.lastImageTime - waitNeeded

           imageData = self.grab_image()

           self.actualFrameRate = 1/(time.perf_counter() - self.lastImageTime)     
       
       else:
           
           imageData = None
      
       return imageData
   

    def grab_image(self):
        """ Pull image from camera
        """        
        rval, imageData = self.vc.read()
        imageData = np.mean(imageData, 2).astype('uint8')
        
        return imageData
        
   
    def set_frame_rate_on(self):
        return True
    
    def get_exposure(self):
        return self.vc.get(cv.CAP_PROP_EXPOSURE)
        
    def get_exposure_range(self):
        return -10,0
   
    def set_exposure(self, exposure):
        self.vc.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.vc.set(cv.CAP_PROP_EXPOSURE, exposure) 
        self.exposure = exposure
        return True    
     
    def set_gain(self, gain):
        self.vc.set(cv.CAP_PROP_GAIN, gain)
        
        
    def get_gain(self):
        return self.vc.get(cv.CAP_PROP_GAIN)
    
    def set_frame_rate(self, fps):
        self.fps = fps
        
    
    def get_frame_rate(self):
        return self.fps
        
    
    def get_gain_range(self):
        return (0,1)

if __name__ == "__main__":
    print("Test mode not implemented")