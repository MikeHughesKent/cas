# -*- coding: utf-8 -*-
"""
CAS: Camera Acquisition System

Simulated camera interface for Camera Acquisition Based GUIs. Loads images
from a file (image or video).

"""

from cas_gui.cameras.GenericCamera import GenericCameraInterface
from PIL import Image, ImageSequence
import numpy as np
import time

class SimulatedCamera(GenericCameraInterface):    
    
    preLoaded = False
    currentFrame = 0
    dtype = 'uint16'   
    
    def __init__(self, **kwargs):         
        
        self.filename = kwargs.get('filename', None)
        self.lastImageTime = time.perf_counter()
        self.lastImageTimeAdjusted = self.lastImageTime
        self.fps = 10
        self.frameRateEnabled = False
        if self.filename is not None:
            try:
                self.dataset = Image.open(self.filename)
            except:
                self.dataset = None

                   
        
    def __str__(self):
        return "Simmulated Camera, source = " + self.filename  
    

    def get_camera_list(self):
        return "Simulated Camera, source = " + self.filename  
     
        
    def open_camera(self, camID):  
        if self.filename is not None:
            try:
                self.dataset = Image.open(self.filename)
                self.camera_open = True
            except:
                self.dataset = None
                self.camera_open = False
               
                
    def close_camera(self):
        self.camera_open = False
    
        
    def dispose(self):
        self.dataset.close()
    
    
    def pre_load(self, nImages):
        
        if self.dataset is not None:
            # Pre-Loads nImages into memory, avoiding file read timing slowing
            # down apparent frame rate
            h = np.shape(self.dataset)[0]
            w = np.shape(self.dataset)[1]
            
            if nImages > 0:
                framesToLoad = min(nImages, self.dataset.n_frames)
            else:
                framesToLoad = self.dataset.n_frames
            self.imageBuffer = np.zeros((h,w,framesToLoad), dtype = self.dtype)
    
            for i in range(framesToLoad):
                self.dataset.seek(i)
                self.imageBuffer[:,:,i] = np.array(self.dataset).astype(self.dtype)
            self.preLoaded = True



    def set_current_image(self, imNum):
        currentImageIdx = imNum
        
               
    def get_image(self):
       # Either loads the next image from the file or, if we have pre-loaded,
       # copies the image from memory. Returns the image.
       
       imData = None
       
       if self.dataset is not None:    

           # Calculate delay needed to simulate desired frame rate
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
               # wait needed shorter. This leads to a more accurate frame rate.
               if waitNeeded > -desiredWait:
                   self.lastImageTimeAdjusted = self.lastImageTime - waitNeeded
               else:
                   self.lastImageTimeAdjusted = self.lastImageTime
                   
               if self.preLoaded:
                
                   if self.currentFrame >= np.shape(self.imageBuffer)[2]:
                       self.currentFrame = 0
                   imData = self.imageBuffer[:,:,self.currentFrame].astype(self.dtype)
                   
               else:
                       
                   if self.currentFrame > self.dataset.n_frames - 1:
                       self.currentFrame = 0
                   
                   self.dataset.seek(self.currentFrame)
                   imData = np.array(self.dataset.getdata()).reshape(self.dataset.size[1], self.dataset.size[0]).astype(self.dtype)
    
               self.currentFrame = self.currentFrame + 1
               self.actualFrameRate = 1/(time.perf_counter() - self.lastImageTime)     
           
             
       return imData
    
    
    
    # The following are implmented to better simulate a real camera:
    
    ###### Frame Rate 

    def enable_frame_rate(self):
        self.frameRateEnabled = True
        return True    

    def disable_frame_rate(self):
        self.frameRateEnabled = False
        return True     

    def set_frame_rate(self, fps):
        self.fps = fps
        return
    
    def get_frame_rate(self):
        return self.fps
    
    def get_frame_rate_range(self):
        return (0.01,1024)        
    
    def is_frame_rate_enabled(self):
        return self.frameRateEnabled
    
      


    ##### Exposure
    def is_exposure_enabled(self):
        return False

    def set_exposure(self, exposure):
        pass      
        
    def get_exposure(self):
        return 0
    
    def get_exposure_range(self):
        return 0,0

    
        
    ##### Gain    
    def isGainEnabled(self):
        return False
        
    def setGain(self, gain):
        pass
    
    def getGain(self):
        return 0
    
    def getGainRange(self):
        return 0,0
        
        

if __name__ == "__main__":
    print("Test mode not implemented")