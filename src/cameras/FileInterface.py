# -*- coding: utf-8 -*-
"""
Simulated camera interface for Camera Acquisition Based GUIs. Loads images
from a file (image or video).

Mike Hughes, Applied Optics Group, University of Kent

"""

from GenericCamera import GenericCameraInterface
from PIL import Image, ImageSequence
import numpy as np
import time

class FileInterface(GenericCameraInterface):
    
    
    preLoaded = False
    currentFrame = 0
    dtype = 'uint16'
    currentImageIdx = 0
    lastImageIdx = 1
    lastImage = None
    fileOpen = False
    
    def __init__(self, **kwargs): 
        
        self.filename = kwargs.get('filename', None)
        self.lastImageTime = time.perf_counter()
        self.fps = 30
        self.frameRateEnabled = False
        if self.filename is not None:
            try:
                self.dataset = Image.open(self.filename)
                self.fileOpen = True
            except:
                self.fileOpen = False
                return None
        else:
            self.fileOpen = False
            return None
                   
        
    def __str__(self):
        return "File Processor, source = " + self.filename  
    

    def is_file_open(self):
        return self.fileOpen
    
    def get_camera_list(self):
        return "File Processor, source = " + self.filename  
     
        
    def open_camera(self, camID):  
       
        pass       
                
    def close_camera(self):
        pass
    
        
    def dispose(self):
        self.dataset.close()

        pass
    
    
    def pre_load(self, nImages):
        
        dataset = Image.open(self.filename)
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

               
    def get_image(self):
       # for i, page in enumerate(ImageSequence.Iterator(im)):
       #page.save("page%d.png" % i)
     
       if self.preLoaded:
        
           if self.currentFrame >= np.shape(self.imageBuffer)[2]:
               self.currentFrame = 0
           imData = self.imageBuffer[:,:,self.currentFrame].astype(self.dtype)
           self.currentFrame = self.currentFrame + 1

           
       else:
               
           # If we have already loaded this image, just return it
           if self.currentImageIdx == self.lastImageIdx:
               return self.lastImage
           
           # otherwise load if fom the file 
           self.dataset.seek(self.currentImageIdx)
           imData = np.array(self.dataset.getdata()).reshape(self.dataset.size[1], self.dataset.size[0]).astype(self.dtype)

           self.currentFrame = self.currentFrame + 1
           self.lastImage = imData
           self.lastImageIdx = self.currentImageIdx
           

       return imData
    
    def set_image_idx(self, idx):
        self.currentImageIdx = idx
    
    ###### Frame Rate

    def enable_frame_rate(self):
        self.frameRateEnabled = False
        return False    

    def disable_frame_rate(self):
        self.frameRateEnabled = False
        return True     

    def set_frame_rate(self, fps):
        pass    

    def get_frame_rate(self):
        return None
    
    def get_frame_rate_range(self):
        return None        
    
    def is_frame_rate_enabled(self):
        return False
    
      


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