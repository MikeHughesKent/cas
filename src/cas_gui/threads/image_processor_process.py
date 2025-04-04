# -*- coding: utf-8 -*-
"""
ImageProcessorProcess

Part of Kent CAS-GUI: Camera Acquisition System GUI

Class to assist with real-time image processing in a dedicated process (i.e. 
for multiprocessor applications). At initialisation, four multiprocessing
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

"""

import queue
import multiprocessing
import time
import numpy as np

class ImageProcessorProcess(multiprocessing.Process):
    
    processor = None
    currentFrameNumber = 0
    lastFrameTime = 0
    frameStepTime = 0
    sharedMemoryArray = None
    sharedMemorySize = 0
    sharedMemory = None
    imSize = (0,0)
    imCounter = 0
    
    def __init__(self, inQueue, outQueue, updateQueue, messageQueue, useSharedMemory = False, sharedMemoryArraySize = (2048,2048), statusQueue = None, shareName = "CASShare"):
        
        super().__init__()          
                      
        self.updateQueue = updateQueue
        self.inputQueue = inQueue
        self.outputQueue = outQueue
        self.statusQueue = statusQueue
        self.messageQueue = messageQueue
        self.useSharedMemory = useSharedMemory
        self.sharedMemoryArraySize = sharedMemoryArraySize
        self.shareName = shareName

        
        self.lastFrameTime = 0
        self.frameStepTime = 0
        self.currentFrame = None
        self.currentFrameNumber = 0
        self.isPaused = False
        self.isStarted = True
        self.imCounter = 0
        self.batchProcessNum = 1
   
        
    def run(self):                

        while True:
            
            
            t0 = time.perf_counter()    
            
            # Receive an updated instance of the processor object            
            if self.updateQueue.qsize() > 0:
                self.processor = self.updateQueue.get()
            
            if self.processor is not None:            
                 
                # Receive messages to call methods of the processor instance    
                while self.messageQueue.qsize() > 0:
                    message, parameter = self.messageQueue.get()  
                    if message == "set_batch_process_num":
                        self.set_batch_process_num(parameter)
                    else:    
                        self.processor.message(message, parameter)
                        if self.statusQueue is not None:
                            try:
                                self.statusQueue.put_nowait(message)
                            except:
                                pass
                
                # We attempt to pull an image off the queue 
                if self.get_num_images_in_input_queue() >= self.batchProcessNum:

                    try:
                        if self.batchProcessNum > 1:
                            img = self.inputQueue.get_nowait()
                            im = np.zeros((np.shape(img)[0], np.shape(img)[1], self.batchProcessNum))
                            im[:,:,0] = img
                            for i in range(1, self.batchProcessNum):
                                im[:,:,i] = self.inputQueue.get()
                         
                        else:
                            im = self.inputQueue.get_nowait()
    
                    except:
                        im = None
                        time.sleep(0.001)
                else:
                    time.sleep(0.001)
                    im = None
                    
                if im is not None:  
    
                    ret = self.processor.process(im) 
                    
                    if isinstance(ret, tuple):                        
                        self.imageId = ret[1]
                        outImage = ret[0]
                    else:
                        self.imageId = 0
                        outImage = ret
                    #print(f"process: out size {np.shape(outImage)}")    
                    
                    
                    if not self.useSharedMemory:                   
                        
                        # If the output queue is full we remove an item to make space
                        if self.outputQueue.full():
                            temp = self.outputQueue.get()
                            
                        self.outputQueue.put(outImage)
                    
                    
                    elif self.useSharedMemory:
                        #print("using shared memory")
                        if outImage is not None:
  
                            # Create the shared memory if we haven't already done so
                            if self.sharedMemory is None:

                                temp = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32')
                                try:
                                    self.sharedMemory = multiprocessing.shared_memory.SharedMemory(create=True, size=temp.nbytes, name = self.shareName)
                                except:
                                    self.sharedMemory = multiprocessing.shared_memory.SharedMemory(size=temp.nbytes, name = self.shareName)
                                self.sharedMemoryArray = np.ndarray(self.sharedMemoryArraySize, dtype = 'float32', buffer = self.sharedMemory.buf)
                                self.sharedMemorySize = outImage.nbytes
                                
                            # The output from the processor is copied into the top left corner of the array in shared memory
                            self.sharedMemoryArray[1: 1 + np.shape(outImage)[0], :np.shape(outImage)[1]] = outImage
                            
                            # Store the image size in the shared memory so that receiver know which parts
                            # of memory to use
                            self.imSize = np.shape(outImage)
                            self.sharedMemoryArray[0,0] = self.imSize[0]
                            self.sharedMemoryArray[0,1] = self.imSize[1]
                            self.sharedMemoryArray[0,2] = self.frameStepTime
                            self.sharedMemoryArray[0,3] = self.imCounter
                            self.sharedMemoryArray[0,4] = self.imageId
                            self.imCounter = self.imCounter + 1
                            #print(f"processed {self.imCounter}")
                    
                    # Timing
                    self.currentFrameNumber = self.currentFrameNumber + 1
                    self.currentFrameTime = time.perf_counter()
                    self.frameStepTime = self.currentFrameTime - self.lastFrameTime
                    self.lastFrameTime = self.currentFrameTime
                    #print(self.frameStepTime, time.perf_counter() - t0)

    def get_num_images_in_input_queue(self):
        """ Returns number of images in raw image queue"""
        return self.inputQueue.qsize()
      
    def set_batch_process_num(self, num):
        """ Sets the size of the batch of images to be sent to the processor.
        """
        self.batchProcessNum = num    