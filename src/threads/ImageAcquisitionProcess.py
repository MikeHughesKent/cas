# -*- coding: utf-8 -*-
"""
Kent-CAS: Camera Acquisition System

Threading class for image processing for use in GUIs or or 
multi-threading applications. Sub-class and implement __process_frame
to make a custom image processor.

@author: Mike Hughes
Applied Optics Group
University of Kent
"""

import queue
import threading
import multiprocessing
import time
import logging

class ImageAcquisitionProcess(multiprocessing.Process):
    
    processor = None
    currentFrameNumber = 0
    lastFrameTime = 0
    
    def __init__(self, imageQueue, updateQueue, cam):
        
        # Caller passes the name of the camera class (which should be in a
        # module of the same name) in the variable camName. This is dynamically
        # imported here and an instance created as self.cam.
   
        super().__init__()        
                      
        self.updateQueue = updateQueue
        self.imageQueue = imageQueue

        # self.currentOutputImage = None
        # self.currentInputImage = None
        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True
        
        self.cam = cam
        
        
    def run(self):

        while True:            

           if self.imageQueue.full():
               temp = self.imageQueue.get()
      
           frame = self.cam.get_image()
                #print("Get image time: " + str(time.perf_counter() - t1))
                
           if frame is not None:
                self.currentFrameNumber = self.currentFrameNumber + 1
                self.imageQueue.put(frame)
                self.currentFrame = frame
                self.currentFrameTime = time.perf_counter()
                self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                self.lastFrameTime = self.currentFrameTime
                print(self.frameStepTime)
                
  
       
    
   