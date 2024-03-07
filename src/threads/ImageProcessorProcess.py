# -*- coding: utf-8 -*-
"""
ImageProcessorProcess

Part of Kent- CAS-GUI: Camera Acquisition System GUI

Class to assist with real-time image processing in a dedicated process (i.e. 
for multiprocessor applications). At initialisation, three multiprocessing
queues must be provided. 
    
    inQueue  - Provides images to be processed
    outQueue - Class places processed images in this queue
    updateQueue - An object which implements the process method must be provided
                  here at least once.
                  
This class must be supplied with an object which implements a process method accepting
a single argument, img.

When an image is found in the inQueue, this will be passed to the process method
of the supplied processor object. Whatever is returned from the process method will then 
be placed in outQueue.

This allows a controller or GUI running in a different process to change
parameters of the processing by updating the processor object and passing
it to the process that ImageProcessorProcess is running in via the updateQueue.

@author: Mike Hughes
Applied Optics Group
University of Kent

"""

import queue
import multiprocessing
import time

class ImageProcessorProcess(multiprocessing.Process):
    
    processor = None
    currentFrameNumber = 0
    lastFrameTime = 0
    
    def __init__(self, inQueue, outQueue, updateQueue):
        
        
        super().__init__()  
        
        print("Proess init")
                      
        self.updateQueue = updateQueue
        self.inputQueue = inQueue
        self.outputQueue = outQueue
        
        print(f" PROC: {self.inputQueue}")
            
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True
        
       
    
    # This method is run once the process is created   
    def run(self):

        while True:
            
            
            # Get an updated processor object
            if self.updateQueue.qsize() > 0:
                self.processor = self.updateQueue.get()
            
            if self.processor is not None:
                
                
                try:
                    im = self.inputQueue.get_nowait()
                except:
                    im = None
                    time.sleep(0.01)
                    
                if im is not None:
                    #print("get im time time:" , time.perf_counter() - t1)
    
                    #t1 = time.perf_counter()
    
                    outImage = self.processor.process(im)  
                    #print("processed image")
                    
                    #print("Processing time:" , time.perf_counter() - t1)
                    
                    # If the output queue is full we removed an item to make space
                    if self.outputQueue.full():
                        temp = self.outputQueue.get()
                        
                    #print("writing to queue") 
                    #print(self.outputQueue)
                    self.outputQueue.put(outImage)
                    
                    #print("added to queue")
                    
                    # Timing
                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime
                    
                   
                    # print("Process frame time:" + str(self.frameStepTime) + "\n")
  
       
  