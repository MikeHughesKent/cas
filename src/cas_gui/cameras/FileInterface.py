# -*- coding: utf-8 -*-
"""
CAS: Camera Acquisition System

A camera interface for CAS which instead of using a camera, loads images 
from a file (single or stack).

"""
import time

from PIL import Image, ImageSequence
import numpy as np

from cas_gui.cameras.GenericCamera import GenericCameraInterface


class FileInterface(GenericCameraInterface):
        
    dtype = 'uint16'
    currentImageIdx = 0
    lastImageIdx = -1
    lastImage = None
    fileOpen = False
    dataset = None
    stack = None
    
    def __init__(self, **kwargs): 
        
        self.filename = kwargs.get('filename', None)
        self.lastImageTime = time.perf_counter()
        self.fps = 30
        self.frameRateEnabled = False

        if self.filename is not None:
            try:
                self.dataset = Image.open(self.filename)
                self.fileOpen = True
                self.stack = None
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
      
               
    def get_image(self):
        """ Get the desired image from the file.
        """

        # If we have already loaded this image, just return it
        if self.currentImageIdx == self.lastImageIdx:
            return self.lastImage
            
        # Otherwise jump to desired image (if it is a stack)
        self.dataset.seek(self.currentImageIdx)
        imData = np.asarray(self.dataset)

       
        # Store this image in lastImage
        self.lastImage = imData
        self.lastImageIdx = self.currentImageIdx

       
        return imData
    
    
    def get_all_images(self):
        
        if self.stack is None:
        
            with Image.open(self.filename) as im:
            
                if im.n_frames > 1:
                    h,w = np.shape(im)
                    dt = np.array(im).dtype
                    self.stack = np.zeros((im.n_frames, h,w), dtype = dt)
                    for i in range(im.n_frames):
                        im.seek(i)
                        self.stack[i,:,:] = np.array(im)
                    return self.stack
                else:    
                    return np.array(Image.open(self.filename))
        else:
            return self.stack
    
    def set_image_idx(self, idx):
        """ If the file contains multiple frames, sets the index of the
        image that will be returned when get_image is called.
        """
        self.currentImageIdx = idx
        
        
    def get_number_images(self):
        """ If the file contains multiple frames, returns the number of frames.
        Will return 1 if a singe image.
        """
        if self.dataset is not None:
            return self.dataset.n_frames
        
    
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