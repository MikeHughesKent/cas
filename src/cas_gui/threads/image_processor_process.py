# -*- coding: utf-8 -*-
"""
ImageProcessorProcess

Part of Kent CAS-GUI: Camera Acquisition System GUI

Class to assist with real-time image processing in a dedicated process (i.e. 
for multiprocessor applications). At initialisation, three multiprocessing
queues must be provided. 
    
    inQueue  - Provides images to be processed
    outQueue - Class places processed images in this queue
    updateQueue - An object which implements the process method must be provided
                  here at least once.
    messageQueue - Instruction to call method of the processor with specified parameters
                   are passed using this queue.
                  
This class must be supplied with an object which implements a process method accepting
a single argument, img.

When an image is found in the inQueue, this will be passed to the process method
of the supplied processor object. Whatever is returned from the process method will then 
be placed in outQueue or in shared memory (if useSharedMemory is True)

This allows a controller or GUI running in a different process to change
parameters of the processing by updating the processor object and passing
it to the process that ImageProcessorProcess is running in via the updateQueue.

@author: Mike Hughes, Applied Optics Group, University of Kent

"""

import queue
import multiprocessing
import time
import numpy as np

class ImageProcessorProcess(multiprocessing.Process):
    
    processor = None
    currentFrameNumber = 0
    lastFrameTime = 0
    sharedMemoryArray = None
    sharedMemorySize = 0
    sharedMemory = None

    
    def __init__(self, inQueue, outQueue, updateQueue, messageQueue, useSharedMemory = False, sharedMemoryArraySize = (500,10000)):
        
        print("creating procss")
        super().__init__()  
        
                      
        self.updateQueue = updateQueue
        self.inputQueue = inQueue
        self.outputQueue = outQueue
        self.messageQueue = messageQueue
        self.useSharedMemory = useSharedMemory
        self.sharedMemoryArraySize = sharedMemoryArraySize

        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True,
     
    
    def run(self):                

        while True:
            
            # Receive an updated instance of the processor object
            if self.updateQueue.qsize() > 0:
                self.processor = self.updateQueue.get()
            
            if self.processor is not None:            
                 
                # Receive messages to call methods of the processor instance    
                if self.messageQueue.qsize() > 0:
                    message, parameter = self.messageQueue.get()                 
                    self.processor.message(message,parameter)
               
                # We attempt to pull an image of the queue
                try:
                    im = self.inputQueue.get_nowait()
                    #print("Proc got im")
                except:
                    im = None
                    time.sleep(0.01)
                    #print("Proc no im")

                    
                    
                if im is not None:  
    
                    outImage = self.processor.process(im) 
                    
                    if not self.useSharedMemory:                   
                        
                        # If the output queue is full we removed an item to make space
                        if self.outputQueue.full():
                            temp = self.outputQueue.get()
                            
                        self.outputQueue.put(outImage)
                    
                    
                    elif self.useSharedMemory:
                        
                        if outImage is not None:
  
                            # Create the shared memory if we haven't already done so
                            if self.sharedMemory is None:

                                temp = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32')
                                self.sharedMemory = multiprocessing.shared_memory.SharedMemory(create=True, size=temp.nbytes, name = "CASShare")
                                print("creating shared memory")
                                self.sharedMemoryArray = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32', buffer = self.sharedMemory.buf)
                                self.sharedMemorySize = outImage.nbytes
           
                            # The output from the processor is copied into the top left corner of the array in shared memory
                            self.sharedMemoryArray[:np.shape(outImage)[0], :np.shape(outImage)[1]] = outImage
                            
                            # If the output queue is full we removed an item to make space
                            if self.outputQueue.full():
                                temp = self.outputQueue.get()

                            # Put a tuple in the output queue that tells receiver the image size                            
                            self.outputQueue.put(np.shape(outImage))
                            

                    
                    # Timing
                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime
                    
 